# Milestone M7: Testing and Hardening

## EARS Tasks and Git Workflow

Branch name: feature/m7-testing-hardening

EARS loop
- Explore: inventory gaps in unit/integration/stress/soak coverage
- Analyze: set performance budgets and diagnostics
- Implement: tests across suites; benchmarks; CI gates
- Specify checks: coverage thresholds and regression comparisons
- Commit after each major step

Git commands
- git checkout -b feature/m7-testing-hardening
- git add -A && git commit -m "test(unit): expand core coverage for primitives and scheduler"
- git add -A && git commit -m "test(integration): backpressure, policies, priorities, shutdown"
- git add -A && git commit -m "test(stress,soak): throughput/latency and long-running stability"
- git add -A && git commit -m "chore(ci): coverage gates and benchmark regression checks"
- git add -A && git commit -m "docs(testing): how to run suites and interpret benchmarks"
- git push -u origin feature/m7-testing-hardening
- Open PR early; keep commits small and focused

Status: In Progress
Owner: Core Maintainers
Duration: 5–7 days

PR: feature/m7-testing-hardening (draft) – incremental commits aligned to checklist

Overview
This milestone raises product confidence to release quality by expanding unit and integration coverage, adding stress and soak tests, validating backpressure correctness, and hardening error paths and shutdown semantics. It also introduces lightweight benchmarking and performance budgets for hot paths (edges and scheduler) and formalizes diagnostics and regression prevention in CI.

EARS Requirements
- The system shall achieve ≥90% test coverage for core modules and ≥80% overall.
- The system shall provide unit tests for core classes: Message, PortSpec, Policies, Edge, Node, Subgraph, and Scheduler.
- The system shall provide integration tests for subgraph composition, backpressure propagation, overflow policies, and control-plane priorities.
- The system shall provide stress tests that validate throughput and latency characteristics under load, including starvation avoidance and priority preemption.
- The system shall provide long-running reliability tests to detect memory growth and resource leaks.
- When a node raises exceptions, the system shall continue running (unless configured otherwise), log errors, and increment metrics.
- When shutdown is requested, the system shall gracefully stop within a configurable timeout and adhere to edge policies for in-flight items.
- If regressions are detected by benchmarks (exceeding budget thresholds), the CI shall fail and require triage.

Scope of Work
1) Unit Tests (Core Correctness)
- Message:
  - Header normalization, trace_id generation, timestamp helpers.
  - Immutability-by-convention checks and safe header enrichment.
- Ports:
  - PortSpec creation, schema compatibility, optional Pydantic adapter hooks (guarded).
- Policies:
  - Block: capacity limits return BLOCKED semantics; no drops.
  - Drop: counts drops and preserves queue depth.
  - Latest: replaces older items; ensures depth bounded to latest semantics.
  - Coalesce: deterministic merge function behavior, error surfacing.
- Edge:
  - Bounded capacity accounting, enqueue/dequeue semantics.
  - Overflow behavior per policy with metrics intents.
  - Type enforcement at enqueue boundaries.
- Node:
  - Lifecycle hooks order, emit routing, error policy placeholder behavior.
- Subgraph:
  - Wiring validation, type compatibility, exposure correctness, deterministic edge IDs.
- Scheduler:
  - Ready-queue fairness (round-robin within band).
  - Priority bias ratio across bands.
  - Tick cadence tolerance.
  - Backpressure cooperative scheduling (producer yields, consumer runs, producer resumes).
  - Shutdown sequencing (reverse topo on_stop), drain per policy, timeout behavior.

2) Integration Tests (End-to-End Scenarios)
- Backpressure propagation: (COMPLETE)
  - Producer → block edge → slow consumer: producer experiences BLOCKED; consumer throughput stabilizes. (tests/integration/test_backpressure_end_to_end.py)
- Mixed overflow policies: (COMPLETE)
  - latest and drop under burst; validate final outputs and counters. (tests/integration/test_mixed_overflow_policies.py)
- Control-plane priority (preemption under load): (COMPLETE)
  - CONTROL messages preempt data-plane and are delivered with bounded latency. (tests/integration/test_priority_preemption_under_load.py)
- Shutdown semantics and lifecycle ordering: (COMPLETE)
  - Start-before-work, reverse stop ordering, deterministic shutdown. (tests/integration/test_shutdown_semantics.py)
- Observability smoke: (COMPLETE)
  - Metrics counters increment; logs include node/scheduler lifecycle and error events. (unit + integration observability tests)
- Validation errors:
  - Mismatched port types and invalid capacities are reported with actionable messages. (covered in unit tests for ports/subgraph)

3) Stress, Soak, and Performance Tests
- Throughput stress:
  - Multiple producers/consumers; measure enqueue/dequeue rate and loop latency histogram.
- Starvation and fairness:
  - Adversarial patterns to ensure no runnable node is starved across bands.
- Priority enforcement under load:
  - High data-plane traffic with low-rate control messages; ensure bounded preemption latency.
- Soak test (30–60 min):
  - Memory usage stability; no unbounded growth; consistent throughput.
- Performance budgets (baseline and guardrails):
  - Edge put/get ops/sec target with metrics disabled vs. enabled (overhead ≤ 5–10%).
  - Scheduler loop latency p95 under steady load.
  - Regression thresholds stored as JSON/CSV artifact and compared in CI.

4) Diagnostics and Developer Tooling
- Enhanced test logging:
  - Structured logs at info level for lifecycle; debug off by default.
- Deterministic seeds:
  - Pseudo-random test inputs seeded; record seed on failure for reproducibility.
- Flake mitigation:
  - Time-based assertions with tolerances; retries for non-deterministic external timing only where justified.
- Failure artifacts:
  - On failure, emit metrics snapshots, runnable queue stats, and recent logs (captured in-memory) to assist triage.

5) CI and Coverage Gates
- Coverage thresholds:
  - Core modules ≥90%, overall ≥80%; enforced in CI.
- Sharded test execution:
  - Split unit, integration, stress into separate jobs; stress/soak may run on nightly builds.
- Benchmark job:
  - Microbenchmarks for edge and scheduler; compare to baseline; fail on significant regressions (>10% unless justified).
- Flake quarantine:
  - Label tests as flaky only with triage issue; auto-retry at most once; track in CI dashboard.

Test Matrix
- Python versions: 3.11 (primary), 3.12 (if feasible).
- Operating systems: Linux (primary), macOS (best-effort smoke).
- Config toggles:
  - Observability: metrics/logging on/off; tracing disabled by default; optional smoke with tracing enabled.
  - Policies: block/drop/latest/coalesce coverage.
  - Capacities: small (8–16), medium (64–256), large (≥1024).

Example Test Cases (Representative)
- unit/test_edge_policies.py
  - test_block_applies_backpressure_until_get
  - test_drop_increments_counter_and_preserves_depth
  - test_latest_keeps_only_newest_during_burst
  - test_coalesce_merges_fast_and_is_pure
- unit/test_scheduler_priority.py
  - test_control_plane_preempts_data_plane
  - test_fairness_within_priority_band_round_robin
  - test_pq_edge_cases_and_starvation_avoidance (PLANNED)
- integration/test_backpressure_end_to_end.py (COMPLETE)
  - test_producer_slowed_by_block_policy_slow_consumer
- integration/test_priority_preemption_under_load.py (COMPLETE)
  - test_control_pierces_data_under_sustained_load
- integration/test_mixed_overflow_policies.py (COMPLETE)
  - test_latest_and_drop_under_burst_with_bounded_depth
- integration/test_shutdown_semantics.py (COMPLETE)
  - test_graceful_shutdown_respects_policies_and_timeout_and_ordering
- unit/test_scheduler_pq_edge_cases.py (COMPLETE)
  - test_deduplication_on_reenqueue
  - test_fifo_within_band_under_reenqueue
  - test_ratio_bias_prefers_control_but_services_lower_bands
  - test_fallback_selects_any_available_band
  - test_bounded_skew_two_nodes_same_band
- stress/test_throughput_and_latency.py (PLANNED)
  - test_scheduler_loop_latency_under_load_with_budgets
- soak/test_long_running_stability.py (PLANNED)
  - test_no_memory_growth_over_time

Performance and Reliability Budgets
- Edge operations:
  - put/get ≥ 1–5 million ops/minute on a typical dev machine without metrics; overhead with metrics ≤ 10%.
- Scheduler loop:
  - p95 loop latency within 1–2x tick interval baseline under normal load; bounded growth under burst with batch limits.
- Priority preemption:
  - Control-plane message service latency stays below a target bound (e.g., < one tick interval) under sustained data-plane load.
- Memory:
  - No unbounded growth in soak; queues bounded by capacity; references released on drain.

Risk Assessment and Mitigations
- Flaky timing-sensitive tests:
  - Mitigation: Use monotonic clocks, tolerances, and deterministic seeds; separate timing-heavy tests into nightly.
- Benchmark noise in CI:
  - Mitigation: Run benchmarks multiple times; use median; allow small variance window; cache warm-up iterations.
- Hidden coupling or global state in tests:
  - Mitigation: Test isolation, fixture teardown, and avoidance of shared singletons; contextvars reset per test.
- Coverage inflation without meaningful assertions:
  - Mitigation: Enforce assertion density in reviews; prefer behavior-focused tests over line coverage alone.

Acceptance Criteria
- Core coverage ≥90%, overall coverage ≥80%, enforced in CI. (IN PROGRESS – tests added; CI gating pending)
- Unit, integration, stress, and soak suites implemented; stress/soak may run nightly with artifacts. (PARTIAL – unit/integration complete; stress/soak pending)
- Backpressure correctness verified end-to-end for all policies. (COMPLETE for Block/Drop/Latest; Coalesce covered in unit)
- Priority preemption verified with bounded latency under load. (COMPLETE)
- Graceful shutdown verified with policy-respecting drain and timeout fallback. (COMPLETE)
- Benchmarks established with stored baselines; CI fails on significant regressions. (PENDING – initial bench shim present)
- Failures produce actionable diagnostics (logs, metrics snapshots, seeds). (IN PROGRESS – logging/metrics integrated; artifacting for failures pending)
- PR task list alignment: incremental commits for each completed item; PR checklist updated (IN PROGRESS)

Deliverables
- Tests:
  - tests/unit/* covering core primitives, node, subgraph, scheduler.
  - tests/integration/* covering backpressure, priorities, shutdown, observability smoke.
  - tests/stress/* minimal benchmarks and high-load validations.
  - tests/soak/* long-running stability checks (nightly).
- CI updates:
  - Jobs for unit, integration; optional nightly stress/soak; benchmark comparison step; coverage gates.
- Docs:
  - CONTRIBUTING/testing.md: how to run suites locally, interpret benchmarks, and debug failures.
  - README links to testing docs; note coverage goals and nightly jobs.

Traceability
- Implements Technical Blueprint Implementation Plan M7.
- Satisfies EARS requirements for coverage, backpressure validation, priority behavior, graceful shutdown, observability validation, and regression prevention.

Checklist
- [x] Unit tests: core primitives, node/subgraph, scheduler
- [x] Unit tests: PQ edge cases (dedup, FIFO, ratio bias, bounded skew)
- [x] Integration tests: backpressure, priorities (preemption), mixed overflow policies, shutdown, observability smoke
- [ ] Unit tests: node lifecycle error isolation (on_start/on_tick/on_message/on_stop)
- [ ] Stress tests: throughput, latency, fairness, priority preemption
- [ ] Soak tests: long-running stability and memory checks
- [ ] Benchmarks: edge put/get, scheduler loop latency; baseline stored
- [ ] CI: coverage gates, shard runs, nightly stress/soak, benchmark comparison
- [ ] Docs: testing guide, how to run suites and interpret benchmarks; debugging and diagnostics