# Testing Guide

This document explains how to run Meridian Runtime tests locally, how to use environment toggles, how benchmarks and seeds work, and what CI enforces.

Contents
- Test suites and markers
- Running tests locally
- Environment toggles
- Deterministic seeds
- Benchmarks and budgets
- Stress and soak
- CI notes and expectations
- Troubleshooting

Test suites and markers
We organize tests by suite and mark them for easy selection:

- Unit: fast, isolated tests for core primitives and logic
  - Marker: unit
  - Path examples: tests/unit/*
- Integration: end-to-end behavior across nodes/edges/scheduler
  - Marker: integration
  - Path examples: tests/integration/*
- Stress: high-load validations (short duration), throughput/latency smoke
  - Marker: stress
  - Path examples: tests/stress/*
- Soak: long-running stability checks (nightly), memory/throughput stability
  - Marker: soak
  - Path examples: tests/soak/*
- Benchmark: microbenchmarks for hot paths (edge put/get, scheduler loop)
  - Marker: benchmark
  - Path examples: tests/**/test_bench_*.py

Running tests locally
We recommend Python 3.11 and using uv (or your preferred virtualenv manager).

Install dependencies
- If using uv:
  - uv lock (first time)
  - uv sync

Run the whole suite (fast path)
- uv run pytest -q

Run by suite
- Unit:
  - uv run pytest -q -k "unit"
- Integration:
  - uv run pytest -q -k "integration"
- Stress:
  - uv run pytest -q -k "stress"
- Soak:
  - uv run pytest -q -k "soak"
- Benchmarks (warn-only by default):
  - MERIDIAN_BENCH_WARN_ONLY=1 uv run pytest -q -k "benchmark"

Coverage
- Overall coverage (gate ≥ 80% in CI):
  - uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
- Core module coverage (stricter ≥ 90%, if core package path exists):
  - uv run pytest --cov=src/meridian --cov-report=term --cov-fail-under=90 -k "unit"

Environment toggles
These environment variables control diagnostics and performance behavior:

- MERIDIAN_METRICS
  - 1 to enable metrics; 0 to disable (default off in unit tests)
- MERIDIAN_BENCH_WARN_ONLY
  - 1 to allow benchmark regressions to warn but not fail (default for PRs)
  - 0 to enforce benchmark thresholds (nightly/main)
- MERIDIAN_TEST_SEED
  - Override the deterministic test seed (integer)
- MERIDIAN_SET_CPU_AFFINITY
  - 1 to enable optional CPU affinity pinning (if available)
  - Off by default; not required for v1 correctness

Deterministic seeds
- The test session uses a deterministic seed determined by:
  - CLI option --seed if provided, else
  - MERIDIAN_TEST_SEED if set, else
  - Daily UTC date (YYYYMMDD), else
  - A fixed constant fallback
- Each test re-seeds at start to avoid inter-test randomness leakage.
- Failures append the active seed to the report for reproducibility.
- To reproduce a failure:
  - uv run pytest -q --seed <seed_from_report> -k "<your_test>"

Benchmarks and budgets
Scope and philosophy for v1
- Benchmarks exist to catch extreme regressions and ensure sanity.
- We do not optimize for peak performance in v1; clarity and correctness first.

Running benchmarks
- Smoke run (warn-only by default):
  - MERIDIAN_BENCH_WARN_ONLY=1 uv run pytest -q -k "benchmark"
- Enforced mode (e.g., for main/nightly):
  - MERIDIAN_BENCH_WARN_ONLY=0 uv run pytest -q -k "benchmark"

Budget style and thresholds
- Microbenchmarks are deterministic and short.
- Thresholds are conservative and designed to be stable in CI.
- Budgets may be looser in warn-only mode to reduce noise in PRs.

Artifacts
- Benchmarks can export JSON/CSV artifacts in CI (post-v1 will include richer artifact comparison).
- For local study, consider capturing run logs or simple JSON outputs from benchmark utilities.

Stress and soak
Stress tests (short)
- Goal: exercise throughput/latency and fairness under controlled load.
- Default durations are short to keep CI-friendly runtime (~minutes).
- Run: uv run pytest -q -k "stress"

Soak tests (nightly)
- Goal: catch memory leaks or stability issues over a longer interval.
- Nightly jobs run shortened soaks (~10–15 minutes) for v1; longer soaks post-v1.
- Run locally (optional): uv run pytest -q -k "soak"
  - Tip: Prefer a dedicated machine and avoid running soaks alongside other heavy workloads.

CI notes and expectations
What CI enforces for v1
- Linting (ruff), formatting (black), typing (mypy)
- Unit tests and integration tests on PRs
- Coverage gates:
  - Overall ≥ 80%
  - Core modules ≥ 90% (if applicable path exists)
- Benchmarks:
  - PRs: warn-only (MERIDIAN_BENCH_WARN_ONLY=1)
  - Nightly/main: enforced (MERIDIAN_BENCH_WARN_ONLY=0)
- Nightly:
  - Run stress/soak short versions and enforced benchmarks
  - Upload artifacts/logs as needed

Sharding
- Jobs are split across unit, integration, and benchmark-smoke on PRs.
- Nightly includes stress/soak/benchmarks.

Flake mitigation
- Deterministic seeds and tolerant time-based assertions are used where appropriate.
- If a true flake is found, open an issue with details:
  - Seed, test name, logs, reproduction steps
- CI may allow a single retry where justified, but flaky tests must be triaged.

Troubleshooting
Common issues
- Import errors: ensure src is on PYTHONPATH; running via uv sync adds dependencies.
- Timing sensitivity:
  - Use --seed to reproduce and adjust local machine load
  - Avoid assertions on exact times; use ranges/tolerances
- Metrics overhead:
  - Disable metrics (MERIDIAN_METRICS=0) when measuring core loop behavior for sanity checks
  - Enable metrics when validating observability pathways
- Benchmark variance:
  - Use warn-only mode for PRs; rely on nightly for enforcement
  - Close noisy background tasks on your machine to reduce variance

Getting help
- File an issue with:
  - The failing test name and suite
  - Seed and environment variables
  - OS, Python version
  - Logs and any artifacts
- Label appropriately (area/testing, area/benchmarks, kind/bug or kind/task).

Thanks for helping keep the runtime deterministic, well-tested, and maintainable.