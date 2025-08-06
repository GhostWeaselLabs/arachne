#!/usr/bin/env python3
"""
meridian-runtime/benchmarks/compare_baseline.py

Add baseline JSON and comparator for benchmark regression checks.

This script compares a "current" benchmark JSON document (produced by the
benchmarks in this repository) against a versioned baseline JSON, and exits
non-zero if any metric has regressed beyond a configured threshold.

Usage:
  # Compare using explicit files
  uv run python benchmarks/compare_baseline.py --current benchmarks/current.json --baseline benchmarks/baseline.json

  # Compare individual bench outputs against a shared baseline
  uv run python benchmarks/compare_baseline.py --current benchmarks/current.edge.json --baseline benchmarks/baseline.json
  uv run python benchmarks/compare_baseline.py --current benchmarks/current.scheduler.json --baseline benchmarks/baseline.json

Environment variables:
  MERIDIAN_BENCH_REGRESSION_PCT   - Allowed regression percent (default: 10)
  MERIDIAN_BENCH_WARN_ONLY        - If set to "1", "true", "yes", or "on", prints warnings instead of failing
  MERIDIAN_BENCH_BASELINE_SECTION - Optional section name in baseline to compare against ("edge_put_get", "scheduler_loop", etc.)

Input expectations:
  - Baseline JSON contains named entries with numeric KPIs for each benchmark.
    A recommended structure:
      {
        "edge_put_get": {
          "ops_per_sec_no_metrics": 5_000_000,
          "ops_per_sec_prom_metrics": 4_600_000,
          "metrics_overhead_pct": 8.0
        },
        "scheduler_loop": {
          "loop_p95_ms": 2.0,
          "loop_p99_ms": 5.0,
          "iterations_per_second": 30000
        }
      }

  - Current JSON can be one of:
    1) A combined document with a "name" and metrics fields.
    2) A per-benchmark document emitted by our bench scripts:
       - benchmarks/bench_edge.py:
         {
           "name": "edge_put_get",
           "modes": [...],
           "summary": {
             "ops_per_sec": { "no_metrics": N1, "prom_metrics": N2 },
             "metrics_overhead_pct": P
           }
         }
       - benchmarks/bench_scheduler.py:
         {
           "name": "scheduler_loop",
           "summary": {
             "loop_p95_ms": P95,
             "loop_p99_ms": P99,
             "processed": COUNT
           },
           "results": {
             "iterations_per_second_estimate": IPS,
             ...
           }
         }

Comparison semantics:
  - For "higher is better" metrics (e.g., ops/sec, iterations/sec), the script checks that:
      (baseline - current) / baseline * 100 <= threshold_pct
  - For "lower is better" metrics (e.g., loop p95/p99), the script checks that:
      (current - baseline) / baseline * 100 <= threshold_pct
  - Unknown metrics in current that do not have entries in baseline are ignored.
  - Missing metrics in current that exist in baseline are reported as warnings.

Exit codes:
  0 - No regression beyond threshold (or warn-only mode)
  1 - Regression detected beyond threshold (and not in warn-only mode)

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


# ---------------------------
# Configuration and constants
# ---------------------------

DEFAULT_THRESHOLD_PCT = 10.0

# Metric direction: True => higher is better, False => lower is better
# This mapping is used to interpret whether increases/decreases are regressions.
METRIC_DIRECTIONS = {
    # Edge benchmarks
    "ops_per_sec_no_metrics": True,
    "ops_per_sec_prom_metrics": True,
    "metrics_overhead_pct": False,  # lower overhead is better
    # Scheduler benchmarks
    "iterations_per_second": True,
    "iterations_per_second_estimate": True,  # as emitted by bench_scheduler
    "loop_p50_ms": False,
    "loop_p95_ms": False,
    "loop_p99_ms": False,
}

# Fallback metric key candidates for scheduler and edge when extracting from "current"
EDGE_SUMMARY_TO_BASELINE_KEYS = {
    # current.summary.ops_per_sec.no_metrics -> baseline.ops_per_sec_no_metrics
    ("summary", "ops_per_sec", "no_metrics"): "ops_per_sec_no_metrics",
    ("summary", "ops_per_sec", "prom_metrics"): "ops_per_sec_prom_metrics",
    ("summary", "metrics_overhead_pct"): "metrics_overhead_pct",
}

SCHED_SUMMARY_TO_BASELINE_KEYS = {
    # current.summary.loop_p95_ms -> baseline.loop_p95_ms
    ("summary", "loop_p50_ms"): "loop_p50_ms",
    ("summary", "loop_p95_ms"): "loop_p95_ms",
    ("summary", "loop_p99_ms"): "loop_p99_ms",
    # current.results.iterations_per_second_estimate -> baseline.iterations_per_second
    ("results", "iterations_per_second_estimate"): "iterations_per_second",
}


@dataclass
class CompareConfig:
    current_path: Path
    baseline_path: Path
    threshold_pct: float
    warn_only: bool
    section: str | None


# ---------------------------
# JSON helpers
# ---------------------------


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")


def _get_env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


# ---------------------------
# Extraction and alignment
# ---------------------------


def _infer_section(current: Dict[str, Any], override: str | None) -> str | None:
    """
    Try to infer which section of the baseline to compare against from the "current" doc,
    unless an explicit override is provided.
    """
    if override:
        return override
    # Use 'name' if available (e.g., "edge_put_get", "scheduler_loop")
    name = current.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _flatten_current_to_metrics(current: Dict[str, Any], section: str | None) -> Dict[str, float]:
    """
    Extracts a normalized metric dict from the current document using known conventions.
    Keys will match baseline metric names where possible.
    """
    metrics: Dict[str, float] = {}

    # If section isn't known, try to discover by available fields (edge or scheduler shapes)
    sec = section or current.get("name")

    # Edge bench shape
    if sec == "edge_put_get":
        # Map current.summary.ops_per_sec.{no_metrics,prom_metrics} -> baseline keys
        for key_path, out_key in EDGE_SUMMARY_TO_BASELINE_KEYS.items():
            try:
                val = _get_nested(current, *key_path)
                if val is not None:
                    metrics[out_key] = float(val)
            except Exception:
                # tolerate missing keys
                pass

    # Scheduler bench shape
    if sec == "scheduler_loop":
        for key_path, out_key in SCHED_SUMMARY_TO_BASELINE_KEYS.items():
            try:
                val = _get_nested(current, *key_path)
                if val is not None:
                    metrics[out_key] = float(val)
            except Exception:
                pass

    # Generic fallbacks: copy any numeric summary fields directly if they match baseline names
    if "summary" in current and isinstance(current["summary"], dict):
        for k, v in current["summary"].items():
            if isinstance(v, (int, float)) and k not in metrics:
                metrics[k] = float(v)

    # Also permit a "metrics" top-level numeric map
    if "metrics" in current and isinstance(current["metrics"], dict):
        for k, v in current["metrics"].items():
            if isinstance(v, (int, float)) and k not in metrics:
                metrics[k] = float(v)

    return metrics


def _get_nested(obj: Dict[str, Any], *keys: str) -> Any:
    cur = obj
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur


# ---------------------------
# Comparison logic
# ---------------------------


def _compare_metrics(
    section: str,
    baseline: Dict[str, Any],
    current_metrics: Dict[str, float],
    threshold_pct: float,
) -> Tuple[bool, Dict[str, Any], Dict[str, str]]:
    """
    Compare current_metrics against baseline[section].

    Returns:
      (ok, details, messages)

      ok: True if no regression beyond threshold
      details: per-metric comparison results with deltas
      messages: human-readable messages for logs
    """
    ok = True
    details: Dict[str, Any] = {}
    messages: Dict[str, str] = {}

    base_section = baseline.get(section, {})
    if not isinstance(base_section, dict):
        messages["section"] = (
            f"Baseline section '{section}' missing or not an object; skipping comparison."
        )
        return True, details, messages  # do not fail if section isn't present

    for metric, base_value in base_section.items():
        if not isinstance(base_value, (int, float)):
            continue

        cur_value = current_metrics.get(metric)
        if cur_value is None:
            messages[metric] = (
                f"WARNING: Metric '{metric}' missing in current; baseline={base_value}"
            )
            continue

        higher_is_better = METRIC_DIRECTIONS.get(metric, True)
        if higher_is_better:
            # regression if current < baseline
            delta_pct = _pct_drop(baseline=base_value, current=cur_value)
            regressed = delta_pct > threshold_pct
            verdict = "OK" if not regressed else "REGRESSED"
            if regressed:
                ok = False
        else:
            # lower is better: regression if current > baseline
            delta_pct = _pct_increase(baseline=base_value, current=cur_value)
            regressed = delta_pct > threshold_pct
            verdict = "OK" if not regressed else "REGRESSED"
            if regressed:
                ok = False

        details[metric] = {
            "baseline": float(base_value),
            "current": float(cur_value),
            "direction": "higher_is_better" if higher_is_better else "lower_is_better",
            "delta_pct": float(delta_pct),
            "threshold_pct": float(threshold_pct),
            "verdict": verdict,
        }

        if higher_is_better:
            messages[metric] = (
                f"{metric}: current={cur_value:.6g}, baseline={base_value:.6g}, "
                f"drop={delta_pct:.2f}% [{verdict}]"
            )
        else:
            messages[metric] = (
                f"{metric}: current={cur_value:.6g}, baseline={base_value:.6g}, "
                f"increase={delta_pct:.2f}% [{verdict}]"
            )

    return ok, details, messages


def _pct_drop(baseline: float, current: float) -> float:
    if baseline <= 0:
        return 0.0
    drop = (baseline - current) / baseline * 100.0
    return max(0.0, drop)


def _pct_increase(baseline: float, current: float) -> float:
    if baseline <= 0:
        return 0.0
    inc = (current - baseline) / baseline * 100.0
    return max(0.0, inc)


# ---------------------------
# I/O and CLI
# ---------------------------


def _parse_args(argv: list[str]) -> CompareConfig:
    parser = argparse.ArgumentParser(
        description="Compare benchmark results to a JSON baseline and detect regressions."
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Path to the current benchmark JSON file (e.g., benchmarks/current.scheduler.json)",
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to the baseline JSON file (e.g., benchmarks/baseline.json)",
    )
    parser.add_argument(
        "--section",
        required=False,
        default=None,
        help="Optional baseline section name to compare against "
        "(e.g., 'edge_put_get' or 'scheduler_loop'). "
        "If omitted, inferred from current JSON 'name' field.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Regression threshold in percent. If omitted, read from env or default to 10.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Warn on regressions but do not fail (same as MERIDIAN_BENCH_WARN_ONLY).",
    )

    args = parser.parse_args(argv)

    threshold = (
        args.threshold
        if args.threshold is not None
        else _get_env_float("MERIDIAN_BENCH_REGRESSION_PCT", DEFAULT_THRESHOLD_PCT)
    )
    warn_only = args.warn_only or _get_env_bool("MERIDIAN_BENCH_WARN_ONLY", False)

    return CompareConfig(
        current_path=Path(args.current),
        baseline_path=Path(args.baseline),
        threshold_pct=threshold,
        warn_only=warn_only,
        section=args.section or os.getenv("MERIDIAN_BENCH_BASELINE_SECTION"),
    )


def _main(argv: list[str]) -> int:
    cfg = _parse_args(argv)

    if not cfg.current_path.exists():
        print(json.dumps({"error": f"Current file not found: {cfg.current_path}"}))
        return 1
    if not cfg.baseline_path.exists():
        print(json.dumps({"error": f"Baseline file not found: {cfg.baseline_path}"}))
        return 1

    try:
        current = _load_json(cfg.current_path)
        baseline = _load_json(cfg.baseline_path)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read JSON: {e}"}))
        return 1

    # Infer section if necessary
    section = _infer_section(current, cfg.section)
    if section is None:
        # If we cannot infer, compare all sections that match the current "name" if present,
        # otherwise bail with an informative message.
        print(
            json.dumps(
                {
                    "error": "Unable to infer section; provide --section or include 'name' in current JSON"
                }
            )
        )
        return 1

    # Extract metrics from current and compare
    current_metrics = _flatten_current_to_metrics(current, section)
    ok, details, messages = _compare_metrics(section, baseline, current_metrics, cfg.threshold_pct)

    result_doc = {
        "section": section,
        "threshold_pct": cfg.threshold_pct,
        "warn_only": cfg.warn_only,
        "ok": ok or cfg.warn_only,
        "details": details,
        "messages": messages,
    }

    print(json.dumps(result_doc, indent=2, sort_keys=True))

    if ok:
        return 0

    if cfg.warn_only:
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
