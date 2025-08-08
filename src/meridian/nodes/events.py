from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, Iterable

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class EventAggregator(FunctionNode):
    """Aggregates events within time windows using an aggregation function.

    If key_fn is provided, maintains independent windows per key; otherwise a
    single global window is used.
    """

    def __init__(
        self,
        name: str,
        window_ms: int,
        aggregation_fn: Callable[[list[Any]], Any],
        input_port: str = "input",
        output_port: str = "output",
        key_fn: Callable[[Any], str] | None = None,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._window_ms = max(1, int(window_ms))
        self._agg = aggregation_fn
        self._key_fn = key_fn
        # key -> (buffer, window_start_ms)
        self._buffers: Dict[str, tuple[list[Any], float]] = {}
        self._default_key = "__all__"

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _flush_key(self, key: str) -> None:
        buf, start_ms = self._buffers.get(key, ([], 0.0))
        if not buf:
            return
        try:
            result = self._agg(list(buf))
        finally:
            # Clear regardless of aggregation outcome
            self._buffers[key] = ([], self._now_ms())
        self.emit(self._out, Message(MessageType.DATA, result))

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            payload = msg.payload
            key = self._key_fn(payload) if self._key_fn is not None else self._default_key
            if key not in self._buffers:
                self._buffers[key] = ([], self._now_ms())
            buf, start_ms = self._buffers[key]
            buf.append(payload)
            self._buffers[key] = (buf, start_ms)
        elif msg.type == MessageType.CONTROL:
            # Flush all partial windows on CONTROL
            for key in list(self._buffers.keys()):
                self._flush_key(key)
            self.emit(self._out, msg)
        elif msg.type == MessageType.ERROR:
            # Forward errors unchanged
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        for key, (buf, start_ms) in list(self._buffers.items()):
            if buf and (now - start_ms) >= self._window_ms:
                self._flush_key(key)


class EventCorrelator(FunctionNode):
    """Correlates related events based on correlation keys.

    Emits when completion_predicate returns True for a key's group, or when
    timeout_ms elapses since first item for that key. On timeout, the emitted
    payload includes a marker {"timeout": True} with items and key.
    """

    def __init__(
        self,
        name: str,
        correlation_fn: Callable[[Any], str],
        completion_predicate: Callable[[list[Any]], bool],
        timeout_ms: int,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._key_of = correlation_fn
        self._complete = completion_predicate
        self._timeout_ms = max(1, int(timeout_ms))
        # key -> (items, first_seen_ms)
        self._groups: Dict[str, tuple[list[Any], float]] = {}

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _emit_group(self, key: str, items: list[Any], *, timeout: bool = False) -> None:
        payload = {"key": key, "items": list(items)}
        if timeout:
            payload["timeout"] = True
        self.emit(self._out, Message(MessageType.DATA, payload))

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            key = self._key_of(msg.payload)
            if key not in self._groups:
                self._groups[key] = ([], self._now_ms())
            items, first_ms = self._groups[key]
            items.append(msg.payload)
            self._groups[key] = (items, first_ms)
            if self._complete(items):
                self._emit_group(key, items)
                self._groups.pop(key, None)
        elif msg.type == MessageType.CONTROL:
            # Emit all partial groups as timeouts
            for key, (items, _) in list(self._groups.items()):
                self._emit_group(key, items, timeout=True)
            self._groups.clear()
            self.emit(self._out, msg)
        elif msg.type == MessageType.ERROR:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        for key, (items, first_ms) in list(self._groups.items()):
            if items and (now - first_ms) >= self._timeout_ms:
                self._emit_group(key, items, timeout=True)
                self._groups.pop(key, None)


class TriggerNode(FunctionNode):
    """Emits trigger events based on external conditions.

    On a rising edge of trigger_fn() (False -> True), emits a DATA message with
    the configured payload. While trigger_fn() remains True, duplicate triggers
    are suppressed until it returns False again.
    """

    def __init__(
        self,
        name: str,
        trigger_fn: Callable[[], bool],
        trigger_payload: Any | None = None,
        check_interval_ms: int = 1000,
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._out = output_port
        self._trigger_fn = trigger_fn
        self._payload = trigger_payload
        self._check_interval_ms = max(1, int(check_interval_ms))
        self._last_check_ms = 0.0
        self._was_true = False

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if self._last_check_ms and (now - self._last_check_ms) < self._check_interval_ms:
            return
        self._last_check_ms = now
        try:
            active = bool(self._trigger_fn())
        except Exception:
            active = False
        if active and not self._was_true:
            self.emit(self._out, Message(MessageType.DATA, self._payload))
            self._was_true = True
        elif not active and self._was_true:
            self._was_true = False
