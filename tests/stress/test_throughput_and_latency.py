from __future__ import annotations

# pytest marker: stress
# This test drives a minimal topology under sustained load, measures scheduler loop latency
# via PrometheusMetrics histogram (already instrumented in Scheduler), and enforces optional
# budgets. It also supports exporting a JSON artifact with summary metrics for CI triage.
#
# Usage examples:
#   - Run only stress tests:        uv run pytest -m stress -q
#   - With JSON artifact export:    MERIDIAN_EXPORT_JSON=1 uv run pytest -m stress -q
#   - With latency budget (ms):     MERIDIAN_BUDGET_SCHED_P95_MS=5 uv run pytest -m stress -q
#   - Deterministic seed:           MERIDIAN_SEED=123 uv run pytest -m stress -q
#
# Notes:
#  - This test assumes the Scheduler records per-iteration latency into the histogram
#    "scheduler_loop_latency_seconds" (namespaced by the configured PrometheusMetrics adapter).
#  - To compare metrics-on vs metrics-off overhead locally, you can run this test twice:
#      1) default (NoopMetrics) and 2) with MERIDIAN_METRICS=on to enable PrometheusMetrics.

from __future__ import annotations

import json
import math
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from meridian.core import Node, Scheduler, SchedulerConfig, Subgraph, Message, MessageType
from meridian.core.policies import Block
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.observability.metrics import (
    PrometheusMetrics,
    configure_metrics,
    get_metrics,
)

# -----------------------
# Pytest marker for stress
# -----------------------
pytestmark = pytest.mark.stress


# -----------------------
# Helpers and test nodes
# -----------------------
@dataclass
class ThroughputConfig:
    producers: int = 2
    consumers: int = 2
    capacity: int = 1024
    run_seconds: float = 3.0
    producer_burst_max: int = 8  # producer emits [1..burst] items per tick with random burst size
    producer_sleep_ms: int = 0  # optional per-producer sleep to simulate pacing
    consumer_batch_max: int = 16  # consumer drains up to N per tick
    fairness_ratio: Tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 128
    idle_sleep_ms: int = 0
    tick_interval_ms: int = 1
    shutdown_timeout_s: float = 2.0


class Producer(Node):
    """
    Producer emits integers wrapped in Message(DATA) into its output port. It simulates
    bursty production using a per-tick random burst size (seeded externally for determinism).
    """

    def __init__(self, name: str, out_port: Port, burst_max: int, sleep_ms: int) -> None:
        super().__init__(name)
        # Ensure Node has a matching output port name so Node.emit() can resolve it
        self.outputs = [out_port]
        self._out = out_port
        self._burst_max = max(1, burst_max)
        self._sleep_ms = max(0, sleep_ms)
        self._counter = 0

    def on_start(self) -> None:
        self._counter = 0

    def on_tick(self) -> None:
        # Optional pacing to increase latency pressure realism.
        if self._sleep_ms:
            time.sleep(self._sleep_ms / 1000.0)

        # Emit a random burst of monotonic integers as DATA messages
        burst = random.randint(1, self._burst_max)
        for _ in range(burst):
            msg = Message(MessageType.DATA, self._counter)
            # Emit using the correct output port name that exists on self.outputs
            self.emit(self._out.name, msg)
            self._counter += 1


class Consumer(Node):
    """
    Consumer drains integers from its input port up to a per-tick batch limit
    to simulate bounded work and allow fairness scheduling.
    """

    def __init__(self, name: str, in_port: Port, batch_max: int) -> None:
        super().__init__(name)
        # Ensure Node declares the input port so the scheduler can route messages by port name
        self.inputs = [in_port]
        self._in = in_port
        self._batch_max = max(1, batch_max)
        self._processed = 0

    def on_start(self) -> None:
        self._processed = 0

    def on_message(self, port: Port, msg: Any) -> None:
        # Count messages as they arrive; real work would deserialize/process
        self._processed += 1

    def on_tick(self) -> None:
        # No-op: this consumer is primarily message-driven; tick assists scheduling fairness.
        pass

    @property
    def processed(self) -> int:
        return self._processed


# -----------------------
# Utilities
# -----------------------
def _get_seed() -> int:
    val = os.getenv("MERIDIAN_SEED")
    if val is None:
        return 1337  # default deterministic seed
    try:
        return int(val)
    except ValueError:
        return 1337


def _maybe_enable_metrics() -> None:
    """
    Enable PrometheusMetrics if MERIDIAN_METRICS=on. Otherwise, keep default NoopMetrics.
    """
    if os.getenv("MERIDIAN_METRICS", "").lower() == "on":
        configure_metrics(PrometheusMetrics())


def _artifact_path(suite: str, name: str) -> Path:
    base = Path(".meridian") / "artifacts" / suite
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name}.json"


def _export_json(enabled: bool, suite: str, name: str, payload: Dict[str, Any]) -> None:
    if not enabled:
        return
    path = _artifact_path(suite, name)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _histogram_p95_from_buckets(buckets: Dict[float, int], total: int) -> float:
    """
    Compute approximate p95 from cumulative histogram buckets.
    Args:
      buckets: mapping of upper bound -> cumulative count (includes +Inf as float('inf'))
      total: total count of observations
    Returns:
      p95 estimate (float seconds)
    """
    if total <= 0:
        return float("nan")
    target = math.ceil(total * 0.95)
    # Sort by upper bound to find the first bucket exceeding the target
    for ub in sorted(buckets.keys(), key=lambda x: float(x)):
        if buckets[ub] >= target:
            # Return the upper bound as a conservative p95 estimate
            return float(ub)
    return float("inf")


def _get_scheduler_latency_histogram(
    metrics_provider: PrometheusMetrics,
) -> Tuple[float, int, Dict[float, int]]:
    """
    Find the scheduler_loop_latency_seconds histogram in the provided PrometheusMetrics.
    Returns tuple (sum, count, buckets). If not found, returns (0.0, 0, {}).
    """
    # PrometheusMetrics uses namespaced keys like "meridian-runtime_scheduler_loop_latency_seconds{...}"
    # We match the instrument by suffix.
    hists = metrics_provider.get_all_histograms()
    for key, hist in hists.items():
        if key.endswith("scheduler_loop_latency_seconds"):
            return (hist.sum, hist.count, hist.buckets)
    return (0.0, 0, {})


def _mk_ports() -> Tuple[List[Port], List[Port]]:
    outs: List[Port] = []
    ins: List[Port] = []
    for i in range(4):  # create a small pool of ports to wire producers/consumers
        outs.append(Port(f"o{i}", PortDirection.OUTPUT, PortSpec(f"o{i}", int)))
        ins.append(Port(f"i{i}", PortDirection.INPUT, PortSpec(f"i{i}", int)))
    return outs, ins


def _mk_subgraph(cfg: ThroughputConfig) -> Tuple[Subgraph, List[Consumer]]:
    # Create ports, nodes
    outs, ins = _mk_ports()

    producers: List[Producer] = []
    consumers: List[Consumer] = []

    # We reuse ports round-robin to keep the topology small yet active.
    for p in range(cfg.producers):
        producers.append(
            Producer(f"prod{p}", outs[p % len(outs)], cfg.producer_burst_max, cfg.producer_sleep_ms)
        )
    for c in range(cfg.consumers):
        consumers.append(Consumer(f"cons{c}", ins[c % len(ins)], cfg.consumer_batch_max))

    # Build subgraph with nodes
    g = Subgraph.from_nodes("stress_topology", [*producers, *consumers])

    # Explicitly wire producer outputs to consumer inputs using bounded edges
    # Simple fan-out: each producer connects to every consumer (limited by available ports)
    for p in producers:
        for c in consumers:
            g.connect((p.name, p._out.name), (c.name, c._in.name), capacity=cfg.capacity)

    return g, consumers


def _run_scheduler_for(cfg: ThroughputConfig, subgraph: Subgraph) -> PrometheusMetrics:
    # Enable metrics if requested; otherwise, the histogram will be Noop and count=0
    _maybe_enable_metrics()
    # Capture the provider after we may have configured it
    provider = get_metrics()
    # We need access to get_all_histograms(); ensure we are using PrometheusMetrics
    # If not, switch to PrometheusMetrics to collect latency data for this run specifically.
    if not isinstance(provider, PrometheusMetrics):
        configure_metrics(PrometheusMetrics())

    # Configure scheduler
    s_cfg = SchedulerConfig(
        fairness_ratio=cfg.fairness_ratio,
        max_batch_per_node=cfg.max_batch_per_node,
        idle_sleep_ms=cfg.idle_sleep_ms,
        tick_interval_ms=cfg.tick_interval_ms,
        shutdown_timeout_s=cfg.shutdown_timeout_s,
    )
    sched = Scheduler(s_cfg)
    sched.register(subgraph)

    # Launch in a background thread
    t = threading.Thread(target=sched.run, name="scheduler-stress", daemon=True)
    t.start()

    # Let it run for the configured duration
    time.sleep(cfg.run_seconds)

    # Request shutdown and wait
    sched.shutdown()
    t.join(timeout=cfg.shutdown_timeout_s + 5.0)

    # Return the (now configured) PrometheusMetrics instance
    provider = get_metrics()
    assert isinstance(provider, PrometheusMetrics), "Expected PrometheusMetrics to be active"
    return provider


# -----------------------
# The actual stress test
# -----------------------
def test_scheduler_throughput_and_latency_budget_and_artifacts() -> None:
    # Seed RNG for deterministic burst patterns
    seed = _get_seed()
    random.seed(seed)

    # Load env-based settings
    budget_ms_env = os.getenv("MERIDIAN_BUDGET_SCHED_P95_MS")
    budget_ms = int(budget_ms_env) if budget_ms_env and budget_ms_env.isdigit() else None
    export_json = os.getenv("MERIDIAN_EXPORT_JSON", "0") in ("1", "true", "TRUE", "yes", "on")

    cfg = ThroughputConfig(
        producers=int(os.getenv("MERIDIAN_STRESS_PRODUCERS", "2")),
        consumers=int(os.getenv("MERIDIAN_STRESS_CONSUMERS", "2")),
        capacity=int(os.getenv("MERIDIAN_STRESS_CAPACITY", "1024")),
        run_seconds=float(os.getenv("MERIDIAN_STRESS_RUN_SECONDS", "3.0")),
        producer_burst_max=int(os.getenv("MERIDIAN_STRESS_PRODUCER_BURST_MAX", "8")),
        producer_sleep_ms=int(os.getenv("MERIDIAN_STRESS_PRODUCER_SLEEP_MS", "0")),
        consumer_batch_max=int(os.getenv("MERIDIAN_STRESS_CONSUMER_BATCH_MAX", "16")),
        idle_sleep_ms=int(os.getenv("MERIDIAN_STRESS_IDLE_SLEEP_MS", "0")),
        tick_interval_ms=int(os.getenv("MERIDIAN_STRESS_TICK_INTERVAL_MS", "1")),
        shutdown_timeout_s=float(os.getenv("MERIDIAN_STRESS_SHUTDOWN_TIMEOUT_S", "2.0")),
    )

    # Build the topology and run
    g, consumers = _mk_subgraph(cfg)
    metrics_provider = _run_scheduler_for(cfg, g)

    # Snapshot scheduler loop latency histogram
    h_sum, h_count, h_buckets = _get_scheduler_latency_histogram(metrics_provider)
    p95_s = _histogram_p95_from_buckets(h_buckets, h_count)
    runnable_info = metrics_provider.get_all_gauges()
    counters_info = metrics_provider.get_all_counters()

    # Basic sanity assertions: the scheduler should have iterated and recorded latency
    assert h_count > 0, "Scheduler loop histogram should have observations"

    # If a budget is set, enforce it
    if budget_ms is not None and not math.isnan(p95_s):
        assert p95_s * 1000.0 <= budget_ms, (
            f"Scheduler p95 loop latency exceeded budget: "
            f"{p95_s * 1000.0:.3f} ms > {budget_ms} ms"
        )

    # Aggregate consumer throughput for visibility
    total_processed = sum(c.processed for c in consumers)
    # Export artifact if enabled
    artifact_payload = {
        "suite": "stress",
        "name": "throughput_and_latency",
        "seed": seed,
        "env": {
            "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.sys.platform,
        },
        "config": {
            "producers": cfg.producers,
            "consumers": cfg.consumers,
            "capacity": cfg.capacity,
            "run_seconds": cfg.run_seconds,
            "producer_burst_max": cfg.producer_burst_max,
            "producer_sleep_ms": cfg.producer_sleep_ms,
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
            "gauges": {k: getattr(v, "value", None) for k, v in runnable_info.items()},
            "counters": {k: getattr(v, "value", None) for k, v in counters_info.items()},
            "total_processed": total_processed,
        },
        "budgets": {
            "sched_p95_ms": budget_ms,
        },
        "result": (
            "pass"
            if (budget_ms is None or (not math.isnan(p95_s) and p95_s * 1000.0 <= budget_ms))
            else "fail"
        ),
    }
    _export_json(export_json, "stress", "throughput_and_latency", artifact_payload)

    # Provide a final assertion that there was meaningful work done
    # We don't require a specific throughput, but we ensure at least some messages processed.
    assert total_processed > 0, "Stress test should process at least one message"
