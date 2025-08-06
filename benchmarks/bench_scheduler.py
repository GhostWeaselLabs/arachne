#!/usr/bin/env python3
# meridian-runtime/benchmarks/bench_scheduler.py
#
# Add scheduler benchmark producing JSON results and summarizing loop latency histogram.
#
# This benchmark constructs a minimal runnable topology, runs the Scheduler for a
# configurable duration, and collects scheduler loop latency metrics via the
# built-in Prometheus-like metrics provider. It outputs a single JSON document
# to stdout and, optionally, to benchmarks/current.scheduler.json.
#
# Usage:
#   # Default run (Prometheus metrics enabled automatically)
#   uv run python benchmarks/bench_scheduler.py
#
#   # Control duration, producers/consumers, and interval
#   MERIDIAN_BENCH_SCHED_SECONDS=5 \
#   MERIDIAN_BENCH_SCHED_PRODUCERS=2 \
#   MERIDIAN_BENCH_SCHED_CONSUMERS=2 \
#   MERIDIAN_BENCH_SCHED_TICK_MS=1 \
#     uv run python benchmarks/bench_scheduler.py
#
#   # Export JSON to file as well as stdout
#   MERIDIAN_EXPORT_JSON=1 uv run python benchmarks/bench_scheduler.py > /dev/null
#
# Notes:
#   - The Scheduler already records per-iteration latency in a histogram named
#     "scheduler_loop_latency_seconds". This script enables PrometheusMetrics,
#     runs the scheduler, and then summarizes the histogram including p50/p95/p99.
#
from __future__ import annotations

import json
import math
import os
import random
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---- Runtime imports (assumes meridian-runtime is installed / in PYTHONPATH)
try:
    from meridian.core import Node, Scheduler, SchedulerConfig, Subgraph, Message, MessageType
    from meridian.core.ports import Port, PortDirection, PortSpec
    from meridian.observability.metrics import (
        PrometheusMetrics,
        configure_metrics,
        get_metrics,
    )
except Exception as e:  # pragma: no cover
    # Emit structured error if imports fail to help triage environment issues
    print(json.dumps({"error": f"Failed to import meridian runtime modules: {e}"}))
    sys.exit(1)


# ---- Configuration and helpers
@dataclass
class BenchSchedConfig:
    seconds: float = float(os.getenv("MERIDIAN_BENCH_SCHED_SECONDS", "5.0"))
    producers: int = int(os.getenv("MERIDIAN_BENCH_SCHED_PRODUCERS", "2"))
    consumers: int = int(os.getenv("MERIDIAN_BENCH_SCHED_CONSUMERS", "2"))
    capacity: int = int(os.getenv("MERIDIAN_BENCH_SCHED_CAPACITY", "1024"))
    tick_interval_ms: int = int(os.getenv("MERIDIAN_BENCH_SCHED_TICK_MS", "1"))
    idle_sleep_ms: int = int(os.getenv("MERIDIAN_BENCH_SCHED_IDLE_MS", "0"))
    shutdown_timeout_s: float = float(os.getenv("MERIDIAN_BENCH_SCHED_SHUTDOWN_S", "2.0"))
    fairness_ratio: Tuple[int, int, int] = tuple(
        int(x) for x in os.getenv("MERIDIAN_BENCH_SCHED_FAIRNESS", "4,2,1").split(",")
    )  # type: ignore[assignment]
    max_batch_per_node: int = int(os.getenv("MERIDIAN_BENCH_SCHED_MAX_BATCH", "128"))
    seed: int = int(os.getenv("MERIDIAN_SEED", "8675309"))
    export_json: bool = os.getenv("MERIDIAN_EXPORT_JSON", "0").lower() in ("1", "true", "yes", "on")


def _artifact_path() -> Path:
    path = Path("benchmarks") / "current.scheduler.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _percentile_from_histogram_cumulative(
    buckets: Dict[float, int], total: int, pct: float
) -> float:
    """
    Estimate percentile from a cumulative histogram mapping (upper_bound -> cumulative count).
    Includes +Inf as float('inf').
    """
    if total <= 0 or not buckets:
        return float("nan")
    if pct <= 0:
        # First non-zero bucket upper bound
        for ub in sorted(buckets.keys(), key=lambda x: float(x)):
            if buckets[ub] > 0:
                return float(ub)
        return float("nan")
    if pct >= 100:
        return float("inf")
    target = math.ceil((pct / 100.0) * total)
    for ub in sorted(buckets.keys(), key=lambda x: float(x)):
        if buckets[ub] >= target:
            return float(ub)
    # Fallback if not found
    return float("inf")


def _maybe_enable_prom_metrics() -> None:
    """
    Ensure PrometheusMetrics is enabled so the scheduler loop histogram is populated.
    """
    metrics = get_metrics()
    if not isinstance(metrics, PrometheusMetrics):
        configure_metrics(PrometheusMetrics())


# ---- Minimal workload nodes
class Producer(Node):
    """
    Producer emits increasing integers on each tick to generate message load.
    Emits Message(DATA, payload) via a declared output port, per runtime contract.
    """

    def __init__(self, name: str, out_port: Port, burst_max: int = 8) -> None:
        super().__init__(name)
        # Ensure Node has a matching output port name so Node.emit() can resolve it
        self.outputs = [out_port]
        self._out = out_port
        self._burst_max = max(1, burst_max)
        self._seq = 0

    def on_start(self) -> None:
        self._seq = 0

    def on_tick(self) -> None:
        # Emit a burst of messages to keep the scheduler busy
        burst = random.randint(1, self._burst_max)
        for _ in range(burst):
            msg = Message(MessageType.DATA, self._seq)
            self.emit(self._out.name, msg)
            self._seq += 1


class Consumer(Node):
    """
    Consumer counts messages; work is intentionally light to focus on scheduler loop behavior.
    Declares input port so scheduler can route messages by port name.
    """

    def __init__(self, name: str, in_port: Port, batch_max: int = 32) -> None:
        super().__init__(name)
        # Ensure Node declares the input port for routing
        self.inputs = [in_port]
        self._in = in_port
        self._batch_max = max(1, batch_max)
        self._processed = 0

    def on_start(self) -> None:
        self._processed = 0

    def on_message(self, port: Port, msg: Any) -> None:
        self._processed += 1

    def on_tick(self) -> None:
        # Tick present to participate in fairness, but primary work is message-driven
        pass

    @property
    def processed(self) -> int:
        return self._processed


# ---- Topology assembly
def _mk_ports(n: int = 4) -> Tuple[List[Port], List[Port]]:
    outs: List[Port] = []
    ins: List[Port] = []
    for i in range(n):
        outs.append(Port(f"o{i}", PortDirection.OUTPUT, PortSpec(f"o{i}", int)))
        ins.append(Port(f"i{i}", PortDirection.INPUT, PortSpec(f"i{i}", int)))
    return outs, ins


def _mk_subgraph(cfg: BenchSchedConfig) -> Tuple[Subgraph, List[Consumer]]:
    outs, ins = _mk_ports(max(cfg.producers, cfg.consumers))
    producers: List[Producer] = []
    consumers: List[Consumer] = []

    for p in range(cfg.producers):
        producers.append(Producer(f"prod{p}", outs[p % len(outs)], burst_max=8))
    for c in range(cfg.consumers):
        consumers.append(Consumer(f"cons{c}", ins[c % len(ins)], batch_max=32))

    # Build subgraph with nodes and explicitly wire producer outputs to consumer inputs
    g = Subgraph.from_nodes("bench_sched_topology", [*producers, *consumers])
    for p in producers:
        for c in consumers:
            g.connect((p.name, p._out.name), (c.name, c._in.name), capacity=cfg.capacity)
    return g, consumers


# ---- Metrics extraction
def _get_scheduler_loop_hist() -> Tuple[float, int, Dict[float, int]]:
    """
    Returns (sum, count, buckets) for scheduler_loop_latency_seconds.
    """
    metrics = get_metrics()
    if not isinstance(metrics, PrometheusMetrics):
        return (0.0, 0, {})
    hists = metrics.get_all_histograms()
    for key, hist in hists.items():
        if key.endswith("scheduler_loop_latency_seconds"):
            return (hist.sum, hist.count, hist.buckets)
    return (0.0, 0, {})


# ---- Benchmark runner
def _run_scheduler(cfg: BenchSchedConfig) -> Dict[str, Any]:
    # Deterministic randomness for repeatability
    random.seed(cfg.seed)

    # Ensure histogram is available
    _maybe_enable_prom_metrics()

    # Build topology and scheduler
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

    # Run scheduler in background
    t = threading.Thread(target=sched.run, name="bench-scheduler", daemon=True)
    t.start()

    # Let it run for configured duration
    time.sleep(cfg.seconds)

    # Request shutdown and wait
    sched.shutdown()
    t.join(timeout=cfg.shutdown_timeout_s + 5.0)

    # Gather metrics
    h_sum, h_count, h_buckets = _get_scheduler_loop_hist()
    p50 = _percentile_from_histogram_cumulative(h_buckets, h_count, 50.0)
    p95 = _percentile_from_histogram_cumulative(h_buckets, h_count, 95.0)
    p99 = _percentile_from_histogram_cumulative(h_buckets, h_count, 99.0)

    total_processed = sum(c.processed for c in consumers)

    return {
        "name": "scheduler_loop",
        "version": 1,
        "env": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
        "config": {
            "seconds": cfg.seconds,
            "producers": cfg.producers,
            "consumers": cfg.consumers,
            "capacity": cfg.capacity,
            "tick_interval_ms": cfg.tick_interval_ms,
            "idle_sleep_ms": cfg.idle_sleep_ms,
            "shutdown_timeout_s": cfg.shutdown_timeout_s,
            "fairness_ratio": list(cfg.fairness_ratio),
            "max_batch_per_node": cfg.max_batch_per_node,
            "seed": cfg.seed,
        },
        "results": {
            "scheduler_loop_latency_seconds": {
                "sum": h_sum,
                "count": h_count,
                "p50_estimate_seconds": p50,
                "p95_estimate_seconds": p95,
                "p99_estimate_seconds": p99,
                "buckets": {str(k): int(v) for k, v in h_buckets.items()},
            },
            "total_processed": int(total_processed),
            "iterations_per_second_estimate": (
                (h_count / cfg.seconds) if (cfg.seconds > 0 and h_count > 0) else 0.0
            ),
        },
        "summary": {
            "loop_p95_ms": (p95 * 1000.0) if not math.isnan(p95) and not math.isinf(p95) else None,
            "loop_p99_ms": (p99 * 1000.0) if not math.isnan(p99) and not math.isinf(p99) else None,
            "processed": int(total_processed),
        },
    }


def _write_current(doc: Dict[str, Any]) -> None:
    out = _artifact_path()
    tmp = out.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    tmp.replace(out)


def _main() -> int:
    cfg = BenchSchedConfig()
    doc = _run_scheduler(cfg)

    # Emit to stdout
    print(json.dumps(doc, indent=2, sort_keys=True))

    # Optionally write to benchmarks/current.scheduler.json
    if cfg.export_json:
        _write_current(doc)

    return 0


if __name__ == "__main__":
    sys.exit(_main())
