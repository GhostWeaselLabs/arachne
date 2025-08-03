#!/usr/bin/env python3
# meridian-runtime/benchmarks/bench_edge.py
#
# Edge microbenchmark producing JSON results for ops/sec with and without metrics.
#
# Usage:
#   # Default (NoopMetrics)
#   uv run python benchmarks/bench_edge.py
#
#   # Force metrics-on (PrometheusMetrics)
#   MERIDIAN_METRICS=on uv run python benchmarks/bench_edge.py
#
#   # Control iterations and batch size
#   MERIDIAN_BENCH_EDGE_ITEMS=200000 MERIDIAN_BENCH_EDGE_BATCH=256 uv run python benchmarks/bench_edge.py
#
#   # Write JSON to file
#   MERIDIAN_EXPORT_JSON=1 uv run python benchmarks/bench_edge.py > /dev/null
#
# Notes:
#   - The script emits a single JSON document to stdout unless MERIDIAN_EXPORT_JSON=1,
#     in which case it also writes to benchmarks/current.edge.json.
#   - It supports toggling metrics via MERIDIAN_METRICS=on to measure overhead.
#   - It runs two sub-benches by default: "no_metrics" and "prom_metrics" (unless the
#     environment forces one mode explicitly).
#
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from meridian.core import Edge
    from meridian.core.policies import Latest
    from meridian.core.ports import Port, PortDirection, PortSpec
    from meridian.observability.metrics import (
        PrometheusMetrics,
        configure_metrics,
        get_metrics,
        NoopMetrics,  # type: ignore[attr-defined]
    )
except Exception as e:  # pragma: no cover
    print(json.dumps({"error": f"Failed to import meridian runtime: {e}"}))
    sys.exit(1)


# ---------------------------
# Configuration and utilities
# ---------------------------
@dataclass
class BenchConfig:
    items: int = int(os.getenv("MERIDIAN_BENCH_EDGE_ITEMS", "200000"))
    batch: int = int(os.getenv("MERIDIAN_BENCH_EDGE_BATCH", "256"))
    capacity: int = int(os.getenv("MERIDIAN_BENCH_EDGE_CAPACITY", "4096"))
    warmup_iters: int = int(os.getenv("MERIDIAN_BENCH_WARMUP_ITERS", "2"))
    measure_iters: int = int(os.getenv("MERIDIAN_BENCH_MEASURE_ITERS", "5"))
    # When MERIDIAN_METRICS is not set, we run both modes; otherwise force single mode.
    metrics_env: str = os.getenv("MERIDIAN_METRICS", "").lower()
    export_json: bool = os.getenv("MERIDIAN_EXPORT_JSON", "0").lower() in ("1", "true", "yes", "on")


def _mk_edge(cap: int) -> Edge[int]:
    p_out = Port("o", PortDirection.OUTPUT, spec=PortSpec("o", int))
    p_in = Port("i", PortDirection.INPUT, spec=PortSpec("i", int))
    return Edge("A", p_out, "B", p_in, capacity=cap, spec=PortSpec("i", int))


def _ensure_metrics(mode: str) -> str:
    """
    mode: "off" => NoopMetrics, "on" => PrometheusMetrics
    returns: resolved mode ("off" or "on")
    """
    if mode == "on":
        configure_metrics(PrometheusMetrics())
        return "on"
    # Default to Noop if anything else
    try:
        # Some versions may not expose NoopMetrics class; safest is to configure Prometheus only when "on"
        # and otherwise leave default which is NoopMetrics.
        # If get_metrics() returns Prometheus here (leftover), overwrite with a fresh Noop by re-import fallback.
        if not isinstance(get_metrics(), NoopMetrics):  # type: ignore[name-defined]
            # Fallback: reset by creating a new Noop via a tiny trick:
            # Reconfigure to a new Prometheus and then to Noop is not available; leave as-is if Noop type missing.
            pass
    except Exception:
        # If NoopMetrics type isn't available for isinstance, that's fine; default is already Noop.
        pass
    return "off"


def _time_now_ns() -> int:
    return time.perf_counter_ns()


def _run_put_get_once(n_items: int, batch: int, capacity: int) -> Tuple[float, int]:
    """
    Execute n_items put operations (using Latest policy to avoid excessive growth),
    then drain until empty. Returns (seconds, processed_count).
    """
    edge = _mk_edge(capacity)
    pol = Latest()

    start_ns = _time_now_ns()
    # Put phase
    i = 0
    while i < n_items:
        end = min(n_items, i + batch)
        for v in range(i, end):
            edge.try_put(v, pol)
        i = end

    # Drain phase
    processed = 0
    while edge.depth() > 0:
        _ = edge.try_get()
        processed += 1

    dt_s = ( _time_now_ns() - start_ns ) / 1e9
    return dt_s, processed


def _ops_per_sec(processed: int, seconds: float) -> float:
    if seconds <= 0.0:
        return float("inf")
    return float(processed) / seconds


def _run_bench_series(cfg: BenchConfig, metrics_mode: str) -> Dict[str, Any]:
    """
    Run warmups then measured iterations; return summary stats.
    """
    resolved_mode = _ensure_metrics(metrics_mode)
    warmup_times: List[float] = []
    measure_times: List[float] = []
    measure_processed: List[int] = []

    # Warmups
    for _ in range(cfg.warmup_iters):
        dt, processed = _run_put_get_once(cfg.items, cfg.batch, cfg.capacity)
        warmup_times.append(dt)

    # Measurements
    for _ in range(cfg.measure_iters):
        dt, processed = _run_put_get_once(cfg.items, cfg.batch, cfg.capacity)
        measure_times.append(dt)
        measure_processed.append(processed)

    # Compute stats
    total_processed = sum(measure_processed)
    total_time = sum(measure_times)
    ops_sec = _ops_per_sec(total_processed, total_time)

    p50 = statistics.median(measure_times) if measure_times else float("nan")
    p95 = _percentile(measure_times, 95.0) if measure_times else float("nan")

    return {
        "mode": "prom_metrics" if resolved_mode == "on" else "no_metrics",
        "config": {
            "items": cfg.items,
            "batch": cfg.batch,
            "capacity": cfg.capacity,
            "warmup_iters": cfg.warmup_iters,
            "measure_iters": cfg.measure_iters,
        },
        "results": {
            "iterations": cfg.measure_iters,
            "processed_total": total_processed,
            "time_total_seconds": total_time,
            "ops_per_sec": ops_sec,
            "time_p50_seconds": p50,
            "time_p95_seconds": p95,
            "times_seconds": measure_times,
        },
        "env": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
    }


def _percentile(values: List[float], pct: float) -> float:
    """
    Compute percentile using nearest-rank on sorted data.
    """
    if not values:
        return float("nan")
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)
    data = sorted(values)
    k = int(round((pct / 100.0) * (len(data) - 1)))
    return data[k]


def _write_current_json(doc: Dict[str, Any]) -> None:
    out_path = Path("benchmarks") / "current.edge.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    tmp.replace(out_path)


def _main() -> int:
    cfg = BenchConfig()

    results: List[Dict[str, Any]] = []
    modes: List[str]
    if cfg.metrics_env in ("on", "off"):
        modes = [cfg.metrics_env]
    else:
        # Run both modes when not forced by env
        modes = ["off", "on"]

    for mode in modes:
        results.append(_run_bench_series(cfg, mode))

    # Compose combined doc
    combined = {
        "name": "edge_put_get",
        "version": 1,
        "modes": results,
        "summary": _summarize(results),
    }

    # Print to stdout
    print(json.dumps(combined, indent=2, sort_keys=True))

    # Optionally write to file
    if cfg.export_json:
        _write_current_json(combined)

    return 0


def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Provide a compact summary focused on ops/sec and overhead of metrics.
    """
    summary: Dict[str, Any] = {}
    ops: Dict[str, float] = {}
    for r in results:
        mode = r.get("mode", "?")
        ops_sec = float(r["results"]["ops_per_sec"])
        ops[mode] = ops_sec
    summary["ops_per_sec"] = ops
    if "no_metrics" in ops and "prom_metrics" in ops:
        base = ops["no_metrics"]
        with_metrics = ops["prom_metrics"]
        overhead_pct = 0.0 if base <= 0 else max(0.0, (base - with_metrics) / base * 100.0)
        summary["metrics_overhead_pct"] = overhead_pct
    return summary


if __name__ == "__main__":
    sys.exit(_main())
