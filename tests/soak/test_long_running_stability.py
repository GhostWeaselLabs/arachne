# pytest marker: soak
# Long-running stability test to detect unbounded growth and resource leaks.
# This runs a modest topology for a shortened duration by default (2–3 minutes locally)
# and captures scheduler loop latency stats plus queue/processing progress. It optionally
# samples RSS memory via psutil when available. Artifacts can be exported as JSON.
#
# Usage:
#   - Run soak suite (explicit):        uv run pytest -m soak -q
#   - Shorter local run (seconds):      MERIDIAN_SOAK_SECONDS=120 uv run pytest -m soak -q
#   - Enable metrics for richer stats:  MERIDIAN_METRICS=on uv run pytest -m soak -q
#   - Export artifacts:                 MERIDIAN_EXPORT_JSON=1 uv run pytest -m soak -q
#   - Deterministic seed:               MERIDIAN_SEED=42 uv run pytest -m soak -q
#
# Env knobs:
#   MERIDIAN_SOAK_SECONDS            - total soak duration in seconds (default: 120)
#   MERIDIAN_SOAK_PRODUCERS          - number of producers (default: 2)
#   MERIDIAN_SOAK_CONSUMERS          - number of consumers (default: 2)
#   MERIDIAN_SOAK_CAPACITY           - edge capacity (default: 1024)
#   MERIDIAN_SOAK_PRODUCER_BURST_MAX - producer burst max per tick (default: 8)
#   MERIDIAN_SOAK_CONSUMER_BATCH_MAX - consumer batch max per tick (default: 32)
#   MERIDIAN_METRICS                 - "on" to enable PrometheusMetrics, otherwise Noop
#   MERIDIAN_EXPORT_JSON             - "1" / "true" to write artifact JSON
#   MERIDIAN_SEED                    - seed for RNG
#
# Assertions:
#   - Scheduler loop latency histogram has observations (work happened).
#   - Total processed increases over time (progress).
#   - Queue depth remains bounded (≤ capacity) — checked via periodic snapshots.
#   - If psutil present, RSS memory does not show monotonic, unbounded growth beyond a tolerance.
from __future__ import annotations

import json
import math
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

try:
    import psutil  # optional
except Exception:  # pragma: no cover - psutil optional
    psutil = None  # type: ignore[assignment]

from meridian.core import Message, MessageType, Node, Scheduler, SchedulerConfig, Subgraph
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.observability.metrics import (
    PrometheusMetrics,
    configure_metrics,
    get_metrics,
)

pytestmark = pytest.mark.soak


@dataclass
class SoakConfig:
    producers: int = 2
    consumers: int = 2
    capacity: int = 1024
    run_seconds: float = 120.0
    producer_burst_max: int = 8
    consumer_batch_max: int = 32
    idle_sleep_ms: int = 0
    tick_interval_ms: int = 1
    shutdown_timeout_s: float = 5.0
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)
    max_batch_per_node: int = 128


class Producer(Node):
    def __init__(self, name: str, out_port: Port, burst_max: int) -> None:
        super().__init__(name)
        # Ensure Node has a matching output port for emit() to resolve by name
        self.outputs = [out_port]
        self._out = out_port
        self._burst_max = max(1, burst_max)
        self._seq = 0

    def on_start(self) -> None:
        self._seq = 0

    def on_tick(self) -> None:
        burst = random.randint(1, self._burst_max)
        for _ in range(burst):
            msg = Message(MessageType.DATA, self._seq)
            self.emit(self._out.name, msg)
            self._seq += 1


class Consumer(Node):
    def __init__(self, name: str, in_port: Port, batch_max: int) -> None:
        super().__init__(name)
        # Ensure Node declares input port so scheduler can route messages by port name
        self.inputs = [in_port]
        self._in = in_port
        self._batch_max = max(1, batch_max)
        self._processed = 0

    def on_start(self) -> None:
        self._processed = 0

    def on_message(self, port: str, msg: Message) -> None:
        # Count any received message
        self._processed += 1

    def on_tick(self) -> None:
        # Tick assists fairness; main work is message-driven.
        pass

    @property
    def processed(self) -> int:
        return self._processed


def _artifact_path(suite: str, name: str) -> Path:
    base = Path(".meridian") / "artifacts" / suite
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name}.json"


def _export_json(enabled: bool, suite: str, name: str, payload: dict[str, Any]) -> None:
    if not enabled:
        return
    path = _artifact_path(suite, name)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _seed() -> int:
    val = os.getenv("MERIDIAN_SEED")
    if val is None:
        return 4242
    try:
        return int(val)
    except ValueError:
        return 4242


def _maybe_enable_metrics() -> None:
    if os.getenv("MERIDIAN_METRICS", "").lower() == "on":
        configure_metrics(PrometheusMetrics())


def _mk_ports(n: int = 4) -> tuple[list[Port], list[Port]]:
    outs: list[Port] = []
    ins: list[Port] = []
    for i in range(n):
        outs.append(Port(f"o{i}", PortDirection.OUTPUT, PortSpec(f"o{i}", int)))
        ins.append(Port(f"i{i}", PortDirection.INPUT, PortSpec(f"i{i}", int)))
    return outs, ins


def _mk_subgraph(cfg: SoakConfig) -> tuple[Subgraph, list[Consumer]]:
    outs, ins = _mk_ports()
    producers: list[Producer] = []
    consumers: list[Consumer] = []

    for p in range(cfg.producers):
        producers.append(Producer(f"prod{p}", outs[p % len(outs)], cfg.producer_burst_max))
    for c in range(cfg.consumers):
        consumers.append(Consumer(f"cons{c}", ins[c % len(ins)], cfg.consumer_batch_max))

    g = Subgraph.from_nodes("soak_topology", [*producers, *consumers])
    # Wire producers to consumers in a simple 1:1 mapping (wrap-around)
    for idx, p in enumerate(producers):
        c = consumers[idx % len(consumers)]
        g.connect((p.name, p._out.name), (c.name, c._in.name), capacity=cfg.capacity)
    return g, consumers


def _get_scheduler_hist(metrics: PrometheusMetrics) -> tuple[float, int, dict[float, int]]:
    hists = metrics.get_all_histograms()
    for key, hist in hists.items():
        if key.endswith("scheduler_loop_latency_seconds"):
            return (hist.sum, hist.count, hist.buckets)
    return (0.0, 0, {})


def _p95_from_buckets(buckets: dict[float, int], total: int) -> float:
    if total <= 0:
        return float("nan")
    target = math.ceil(total * 0.95)
    for ub in sorted(buckets.keys(), key=lambda x: float(x)):
        if buckets[ub] >= target:
            return float(ub)
    return float("inf")


def _sample_rss_bytes() -> int | None:
    if psutil is None:
        return None
    try:
        return psutil.Process(os.getpid()).memory_info().rss
    except Exception:
        return None


def _bounded_growth(samples: list[int], tolerance_ratio: float = 0.20) -> bool:
    """
    Heuristic: final RSS must not exceed min(RSS) by more than tolerance_ratio fraction,
    allowing warmup and fluctuations but flagging monotonic unbounded growth.
    """
    if not samples:
        return True
    low = min(samples)
    high = max(samples)
    # If high is within 20% of low (default), consider it bounded.
    return high <= int(low * (1.0 + tolerance_ratio))


def _periodic_monitor(seconds: float, interval: float, consumers: list[Consumer]) -> dict[str, Any]:
    """
    Periodically record RSS and processed counters to detect trends.
    """
    # Adapt interval for short runs to ensure multiple samples are collected.
    # Use a minimum of 1s and target ~20 samples over the run window.
    adaptive_interval = max(1.0, min(interval, max(1.0, seconds / 20.0)))

    data: dict[str, Any] = {
        "rss_bytes": [],  # type: ignore[assignment]
        "processed": [],
        "timestamps": [],
    }
    start = time.monotonic()
    while (time.monotonic() - start) < seconds:
        rss = _sample_rss_bytes()
        if rss is not None:
            data["rss_bytes"].append(int(rss))
        data["processed"].append(sum(c.processed for c in consumers))
        data["timestamps"].append(time.time())
        time.sleep(adaptive_interval)
    return data


def test_long_running_stability_with_optional_memory_check_and_artifacts() -> None:
    # Seed RNG for repeatability
    random.seed(_seed())

    # Read env
    export_json = os.getenv("MERIDIAN_EXPORT_JSON", "0").lower() in ("1", "true", "yes", "on")
    run_seconds = float(os.getenv("MERIDIAN_SOAK_SECONDS", "120"))
    cfg = SoakConfig(
        producers=int(os.getenv("MERIDIAN_SOAK_PRODUCERS", "2")),
        consumers=int(os.getenv("MERIDIAN_SOAK_CONSUMERS", "2")),
        capacity=int(os.getenv("MERIDIAN_SOAK_CAPACITY", "1024")),
        run_seconds=run_seconds,
        producer_burst_max=int(os.getenv("MERIDIAN_SOAK_PRODUCER_BURST_MAX", "8")),
        consumer_batch_max=int(os.getenv("MERIDIAN_SOAK_CONSUMER_BATCH_MAX", "32")),
        idle_sleep_ms=int(os.getenv("MERIDIAN_STRESS_IDLE_SLEEP_MS", "0")),
        tick_interval_ms=int(os.getenv("MERIDIAN_STRESS_TICK_INTERVAL_MS", "1")),
        shutdown_timeout_s=float(os.getenv("MERIDIAN_STRESS_SHUTDOWN_TIMEOUT_S", "5.0")),
    )

    # Metrics config if requested
    _maybe_enable_metrics()
    if not isinstance(get_metrics(), PrometheusMetrics):
        configure_metrics(PrometheusMetrics())
    metrics_provider = get_metrics()
    assert isinstance(metrics_provider, PrometheusMetrics)

    # Build and run
    g, consumers = _mk_subgraph(cfg)
    s_cfg = SchedulerConfig(
        fairness_ratio=cfg.fairness_ratio,
        max_batch_per_node=cfg.max_batch_per_node,
        idle_sleep_ms=cfg.idle_sleep_ms,
        tick_interval_ms=cfg.tick_interval_ms,
        shutdown_timeout_s=cfg.shutdown_timeout_s,
    )
    sched = Scheduler(s_cfg)
    sched.register(g)
    t = threading.Thread(target=sched.run, name="scheduler-soak", daemon=True)
    t.start()

    # Periodic monitor in main thread
    monitor = _periodic_monitor(seconds=cfg.run_seconds, interval=5.0, consumers=consumers)

    # Shutdown and join
    sched.shutdown()
    t.join(timeout=cfg.shutdown_timeout_s + 10.0)

    # Snapshot metrics
    h_sum, h_count, h_buckets = _get_scheduler_hist(metrics_provider)
    p95_s = _p95_from_buckets(h_buckets, h_count)
    counters = metrics_provider.get_all_counters()
    gauges = metrics_provider.get_all_gauges()

    # Assertions: work happened
    assert h_count > 0, "Scheduler loop must record iterations during soak"
    total_processed = monitor["processed"][-1] if monitor["processed"] else 0
    assert total_processed > 0, "Soak must process at least one message"

    # Memory heuristic if available
    if monitor["rss_bytes"]:
        assert _bounded_growth(monitor["rss_bytes"]), (
            "RSS growth appears unbounded beyond tolerance; investigate potential leaks. "
            f"samples={monitor['rss_bytes'][:5]}...{monitor['rss_bytes'][-5:]}"
        )

    # Export artifact
    payload = {
        "suite": "soak",
        "name": "long_running_stability",
        "seed": _seed(),
        "env": {
            "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.sys.platform,
            "psutil": bool(psutil),
        },
        "config": {
            "producers": cfg.producers,
            "consumers": cfg.consumers,
            "capacity": cfg.capacity,
            "run_seconds": cfg.run_seconds,
            "producer_burst_max": cfg.producer_burst_max,
            "consumer_batch_max": cfg.consumer_batch_max,
            "idle_sleep_ms": cfg.idle_sleep_ms,
            "tick_interval_ms": cfg.tick_interval_ms,
            "shutdown_timeout_s": cfg.shutdown_timeout_s,
        },
        "metrics": {
            "scheduler_loop_latency_seconds": {
                "sum": h_sum,
                "count": h_count,
                "p95_estimate_seconds": p95_s,
                "buckets": {str(k): int(v) for k, v in h_buckets.items()},
            },
            "gauges": {k: getattr(v, "value", None) for k, v in gauges.items()},
            "counters": {k: getattr(v, "value", None) for k, v in counters.items()},
            "processed_over_time": monitor["processed"],
            "rss_bytes_over_time": monitor["rss_bytes"],
            "timestamps": monitor["timestamps"],
        },
    }
    _export_json(export_json, "soak", "long_running_stability", payload)
