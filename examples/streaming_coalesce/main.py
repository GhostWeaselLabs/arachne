from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass

from meridian.core import (
    Message,
    MessageType,
    Node,
    Port,
    PortDirection,
    PortSpec,
    Scheduler,
    SchedulerConfig,
    Subgraph,
)
from meridian.core.policies import Coalesce
from meridian.observability.config import ObservabilityConfig, configure_observability
from meridian.observability.logging import get_logger, with_context

# ---------------------------
# Domain model
# ---------------------------


@dataclass(frozen=True, slots=True)
class SensorReading:
    ts: float
    value: float


@dataclass(frozen=True, slots=True)
class WindowAgg:
    count: int
    sum: float
    min_v: float
    max_v: float

    @property
    def avg(self) -> float:
        return 0.0 if self.count == 0 else self.sum / self.count


def merge_window(a: WindowAgg, b: WindowAgg) -> WindowAgg:
    """
    Pure, deterministic merge function for rolling window aggregates.

    The Edge configured with Coalesce(fn=merge_window) will call this when capacity is hit,
    replacing the last queued item with a merged one to reduce pressure.
    """
    return WindowAgg(
        count=a.count + b.count,
        sum=a.sum + b.sum,
        min_v=min(a.min_v, b.min_v),
        max_v=max(a.max_v, b.max_v),
    )


# ---------------------------
# Nodes
# ---------------------------


class SensorNode(Node):
    """
    Emits SensorReading at a configurable rate. Uses ticks as the pacing mechanism.
    """

    def __init__(self, name: str = "sensor", rate_hz: float = 200.0) -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", SensorReading))],
        )
        self._last_emit = 0.0
        self._period = 1.0 / max(1e-6, rate_hz)
        self._rng = random.Random(1234)

    def _handle_tick(self) -> None:
        now = time.monotonic()
        if now - self._last_emit >= self._period:
            self._last_emit = now
            reading = SensorReading(ts=time.time(), value=0.5 + self._rng.random())
            self.emit("out", Message(MessageType.DATA, reading))


class WindowAggNode(Node):
    """
    Converts SensorReading to per-item WindowAgg (count=1), downstream coalescing merges bursts.

    Demonstrates:
      - Deterministic coalescing function
      - Low per-item overhead (one tuple allocation)
    """

    def __init__(self, name: str = "agg") -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", SensorReading))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", WindowAgg))],
        )

    def _handle_message(self, port: str, msg: Message) -> None:
        # Strictly validate payload type to prevent AttributeError
        payload = msg.payload
        if not isinstance(payload, SensorReading):
            logger = get_logger()
            with with_context(node=self.name, port=port):
                logger.warn(
                    "agg.invalid_payload",
                    f"Ignoring non-SensorReading payload type={type(payload).__name__}",
                )
            return

        reading: SensorReading = payload
        agg = WindowAgg(count=1, sum=reading.value, min_v=reading.value, max_v=reading.value)
        self.emit("out", Message(MessageType.DATA, agg))


class SinkNode(Node):
    """
    Prints aggregate snapshots and periodic summaries. Keeps a small ring buffer.
    """

    def __init__(self, name: str = "sink", keep: int = 10, verbose: bool = True) -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", WindowAgg))],
            outputs=[],
        )
        self._keep = keep
        self._verbose = verbose
        self._buf: list[WindowAgg] = []
        self._last_summary = 0.0

    def _handle_message(self, port: str, msg: Message) -> None:
        agg: WindowAgg = msg.payload
        self._buf.append(agg)
        if len(self._buf) > self._keep:
            self._buf.pop(0)

        if self._verbose:
            logger = get_logger()
            with with_context(node=self.name):
                logger.info(
                    "sink.item",
                    f"count={agg.count} avg={agg.avg:.4f} min={agg.min_v:.4f} max={agg.max_v:.4f}",
                )

    def _handle_tick(self) -> None:
        now = time.monotonic()
        if now - self._last_summary >= 1.0:
            self._last_summary = now
            if not self._buf:
                return
            # Summarize last window
            total = WindowAgg(count=0, sum=0.0, min_v=float("inf"), max_v=float("-inf"))
            for a in self._buf:
                total = merge_window(total, a)

            logger = get_logger()
            with with_context(node=self.name):
                logger.info(
                    "sink.summary",
                    f"window_size={len(self._buf)} total_count={total.count} "
                    f"avg={total.avg:.4f} min={total.min_v:.4f} max={total.max_v:.4f}",
                )


# ---------------------------
# Graph builder
# ---------------------------


def build_graph(args: argparse.Namespace) -> Subgraph:
    sensor = SensorNode(rate_hz=args.rate_hz)
    agg = WindowAggNode()
    sink = SinkNode(keep=args.keep, verbose=not args.quiet)

    g = Subgraph.from_nodes("streaming_coalesce", [sensor, agg, sink])

    # Sensor -> Agg: normal capacity
    g.connect((sensor.name, "out"), (agg.name, "in"), capacity=args.cap_sensor_to_agg)

    # Agg -> Sink: small capacity with explicit Coalesce policy to merge bursts deterministically
    g.connect(
        (agg.name, "out"),
        (sink.name, "in"),
        capacity=args.cap_agg_to_sink,
        policy=Coalesce(lambda a, b: merge_window(a, b)),  # type: ignore[arg-type]
    )

    return g


# ---------------------------
# Runner
# ---------------------------


def configure_obs(args: argparse.Namespace) -> None:
    cfg = ObservabilityConfig(
        log_level="DEBUG" if args.debug else "INFO",
        log_json=not args.human,
        metrics_enabled=False,
        tracing_enabled=False,
    )
    configure_observability(cfg)


def run(args: argparse.Namespace) -> None:
    configure_obs(args)

    # Build and register graph
    graph = build_graph(args)

    sched = Scheduler(
        SchedulerConfig(
            tick_interval_ms=args.tick_ms,
            fairness_ratio=(4, 2, 1),
            max_batch_per_node=args.max_batch,
            idle_sleep_ms=1,
            shutdown_timeout_s=args.timeout_s,
        )
    )

    sched.register(graph)

    logger = get_logger()
    with with_context(node="driver"):
        logger.info(
            "demo.start",
            "Streaming coalesce demo starting",
            rate_hz=args.rate_hz,
            cap_agg_to_sink=args.cap_agg_to_sink,
        )

    sched.run()

    with with_context(node="driver"):
        logger.info("demo.stop", "Streaming coalesce demo stopped")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meridian streaming coalesce demo")
    p.add_argument("--rate-hz", type=float, default=300.0, help="Sensor emit rate (items/sec)")
    p.add_argument("--tick-ms", type=int, default=10, help="Scheduler tick interval (ms)")
    p.add_argument("--max-batch", type=int, default=16, help="Max messages per node per slice")
    p.add_argument("--timeout-s", type=float, default=5.0, help="Shutdown timeout when idle (s)")
    p.add_argument("--cap-sensor-to-agg", type=int, default=256, help="Capacity: sensor -> agg")
    p.add_argument("--cap-agg-to-sink", type=int, default=16, help="Capacity: agg -> sink")
    p.add_argument("--keep", type=int, default=10, help="Sink buffer size")
    p.add_argument("--quiet", action="store_true", help="Reduce per-item logs")
    p.add_argument("--human", action="store_true", help="Human-readable logs")
    p.add_argument("--debug", action="store_true", help="Enable debug logs")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
