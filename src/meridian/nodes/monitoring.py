from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Dict

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType
from ..observability.metrics import get_metrics


class MetricsCollectorNode(FunctionNode):
    """Collect and aggregate custom metrics from message streams.

    metric_extractors: mapping name -> callable(payload) -> float|int.
    Aggregation is a simple count/sum; periodic emission of snapshot by tick.
    """

    def __init__(
        self,
        name: str,
        metric_extractors: dict[str, Callable[[Any], float | int]],
        input_port: str = "input",
        output_port: str = "output",
        aggregation_window_ms: int = 60000,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._window_ms = max(1, int(aggregation_window_ms))
        self._extractors = metric_extractors
        self._metrics = get_metrics()
        self._accum: Dict[str, float] = {k: 0.0 for k in metric_extractors}
        self._count: int = 0
        self._last_emit_ms = 0.0

    def _now_ms(self) -> float:
        import time

        return time.monotonic() * 1000.0

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            self._count += 1
            for name, fn in self._extractors.items():
                try:
                    val = float(fn(msg.payload))
                except Exception:
                    val = 0.0
                self._accum[name] = self._accum.get(name, 0.0) + val
        elif msg.type in (MessageType.CONTROL, MessageType.ERROR):
            # Forward as-is
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if not self._last_emit_ms:
            # Initialize such that the first tick after any elapsed time can emit immediately
            self._last_emit_ms = now - self._window_ms
        # Always check and emit if a window has passed OR if we have data and window_ms==0
        if (now - self._last_emit_ms) >= self._window_ms:
            snapshot = {"count": self._count, **self._accum}
            # Update gauges/counters too
            for name, value in self._accum.items():
                self._metrics.gauge(f"custom_metric_{name}", {"node": self.name}).set(value)
            self._metrics.counter("custom_metric_messages_total", {"node": self.name}).inc(self._count)
            if self._count > 0 or any(v != 0.0 for v in self._accum.values()):
                self.emit(self._out, Message(MessageType.DATA, snapshot))
            # Reset window
            self._accum = {k: 0.0 for k in self._extractors}
            self._count = 0
            self._last_emit_ms = now


class HealthCheckNode(FunctionNode):
    """Monitor system health via functions; emits health summaries periodically."""

    def __init__(
        self,
        name: str,
        health_checks: list[Callable[[], bool]],
        output_port: str = "output",
        check_interval_ms: int = 30000,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._out = output_port
        self._checks = health_checks
        self._interval_ms = max(1, int(check_interval_ms))
        self._last_check_ms = 0.0

    def _now_ms(self) -> float:
        import time

        return time.monotonic() * 1000.0

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if self._last_check_ms and (now - self._last_check_ms) < self._interval_ms:
            return
        self._last_check_ms = now
        results = []
        for fn in self._checks:
            try:
                ok = bool(fn())
            except Exception:
                ok = False
            results.append(ok)
        payload = {"healthy": all(results), "checks": results}
        self.emit(self._out, Message(MessageType.DATA, payload))


class AlertingNode(FunctionNode):
    """Generate alerts based on message predicates and thresholds.

    alert_rules: list of callables (payload)-> str|None; return alert message string to fire.
    """

    def __init__(
        self,
        name: str,
        alert_rules: list[Callable[[Any], str | None]],
        notification_channels: list[Callable[[str], None]] | None = None,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._rules = alert_rules
        self._notify = notification_channels or []

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            for rule in self._rules:
                try:
                    text = rule(msg.payload)
                except Exception:
                    text = None
                if text:
                    for send in self._notify:
                        try:
                            send(text)
                        except Exception:
                            pass
                    self.emit(self._out, Message(MessageType.DATA, {"alert": text}))
        elif msg.type in (MessageType.CONTROL, MessageType.ERROR):
            self.emit(self._out, msg)


class SamplingStrategy(str):
    RANDOM = "random"


class SamplingNode(FunctionNode):
    """Sample messages for monitoring without affecting throughput."""

    def __init__(
        self,
        name: str,
        sampling_rate: float = 0.01,
        sampling_strategy: str = SamplingStrategy.RANDOM,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._rate = max(0.0, min(1.0, float(sampling_rate)))
        self._strategy = sampling_strategy

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type != MessageType.DATA:
            self.emit(self._out, msg)
            return
        if self._strategy == SamplingStrategy.RANDOM:
            if random.random() < self._rate:
                self.emit(self._out, msg)
        else:
            # Default to random
            if random.random() < self._rate:
                self.emit(self._out, msg)
