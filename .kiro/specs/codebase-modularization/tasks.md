# Implementation Plan

- [x] 0. Establish refactoring branch and baseline
  - Create feature branch `feature/codebase-modularization` from `main`
  - Run full test suite to capture a green baseline and record durations
  - Capture performance baselines from `benchmarks/` and key CI timings
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [x] 1. Phase 1 — Core Scheduler modularization
  - Create package `src/meridian/core/scheduler/` with modules: `__init__.py`, `config.py`, `coordinator.py`, `execution.py`, `fairness.py`, `shutdown.py`
  - Maintain public API by re-exporting `Scheduler` and `SchedulerConfig` from `__init__.py`
  - Keep modules ~200 lines and under 300 lines each where feasible
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4_

- [x] 1.1 Create scheduler package and public API
  - Add `src/meridian/core/scheduler/__init__.py` that re-exports `Scheduler` and `SchedulerConfig`
  - Ensure `from meridian.core.scheduler import Scheduler, SchedulerConfig` continues to work
  - Add import-compatibility tests
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 1.3, 1.4, 6.3, 7.2_

- [x] 1.2 Extract configuration to `config.py`
  - Move `SchedulerConfig` to `src/meridian/core/scheduler/config.py`
  - Annotate fields explicitly and preserve defaults
  - Update internal imports to use `from .config import SchedulerConfig`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 1.4, 2.1, 6.3_

- [x] 1.3 Split coordination logic to `coordinator.py`
  - Move main coordination loop and orchestration responsibilities
  - Keep only public `Scheduler` surface in `__init__.py`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 2.1, 2.2, 6.1, 6.2_

- [x] 1.4 Split execution lifecycle to `execution.py`
  - Move node execution, tick handling, and lifecycle helpers
  - Ensure behavior parity with existing tests
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 2.2, 7.1, 7.2_

- [x] 1.5 Split fairness and batching to `fairness.py`
  - Isolate fairness ratios, batch sizing, and scheduling decisions
  - Preserve performance characteristics and add targeted tests
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 2.2, 7.3_

- [x] 1.6 Split shutdown handling to `shutdown.py`
  - Move graceful shutdown, timeouts, and cleanup responsibilities
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 2.2_

- [x] 1.7 Backward-compatible imports and shims
  - Add re-exports and safe shims so existing deep imports do not break
  - Optionally add deprecation warnings for internal paths
  - _Requirements: 1.3, 6.3, 8.3_

- [x] 1.8 Validate with tests and performance checks
once  - Run all `tests/` to confirm parity and update assertions if only import paths changed
  - Compare scheduler-focused benchmarks to baseline and document results
  - _Requirements: 7.1, 7.3, 8.2, 8.4_

- [x] 2. Phase 2 — Observability modularization (tracing, metrics, logging)
  - Create packages per design to separate config, providers, and core APIs
  - Maintain import compatibility via `__init__.py` re-exports
  - _Requirements: 1.1, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 7.1, 7.2_

- [x] 2.1 Tracing package `src/meridian/observability/tracing/`
  - Add modules: `__init__.py`, `config.py`, `context.py`, `providers.py`, `spans.py`
  - Move types and helpers from `tracing.py` into appropriate modules
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 3.1, 3.2, 3.4, 6.1, 6.2_

- [x] 2.2 Metrics package `src/meridian/observability/metrics/`
  - Add modules: `__init__.py`, `config.py`, `providers.py`, `instruments.py`, `collection.py`
  - Preserve provider interfaces and instrument semantics
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 3.1, 3.2, 3.4, 6.1, 6.2, 7.3_

- [x] 2.3 Logging package `src/meridian/observability/logging/`
  - Add modules: `__init__.py`, `config.py`, `formatters.py`, `handlers.py`
  - Keep public logging functions stable through re-exports
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 3.3, 3.4, 6.1, 6.2_

- [x] 2.4 Import compatibility and tests
  - Add import tests to ensure `from meridian.observability import tracing, metrics, logging` still works
  - Update internal imports to avoid circular dependencies
  - Establish authoring constraint: keep newly created test files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 6.2, 6.3, 7.1, 7.2_

- [x] 3. Phase 3 — Core graph components modularization (node, subgraph, edge)
  - Create packages and split per responsibilities while preserving execution semantics
  - Ensure examples and notebooks continue to run unchanged
  - _Requirements: 1.1, 1.3, 1.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 7.1, 7.4_

- [x] 3.1 Node package `src/meridian/core/node/`
  - Add modules: `__init__.py`, `base.py`, `lifecycle.py`, `execution.py`, `observability.py`
  - Move code from `node.py` accordingly and re-export public `Node`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 4.1, 6.1, 6.3, 7.1_

- [x] 3.2 Subgraph package `src/meridian/core/subgraph/`
  - Add modules: `__init__.py`, `construction.py`, `execution.py`, `management.py`
  - Move code from `subgraph.py` accordingly and re-export public `Subgraph`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 4.2, 6.1, 6.3, 7.1_

- [x] 3.3 Edge package `src/meridian/core/edge/`
  - Add modules: `__init__.py`, `definition.py`, `dataflow.py`, `management.py`
  - Move code from `edge.py` accordingly and re-export public `Edge`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 4.3, 6.1, 6.3, 7.1_

- [x] 3.4 Compatibility and behavior validation
  - Run integration tests to ensure graph execution semantics are unchanged
  - Validate examples in `docs/examples/` and `notebooks/` run without modification
  - _Requirements: 4.4, 7.1, 7.4, 8.2_

- [x] 4. Phase 4 — Utility and support modules modularization
  - Split large utility modules into focused packages per design
  - Maintain single public entry point via each package `__init__.py`
  - _Requirements: 1.1, 1.3, 1.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.3, 7.1_

- [x] 4.1 Validation package `src/meridian/utils/validation/`
  - Add modules: `__init__.py`, `core.py`, keep existing `graph.py`, `ports.py`, `schema.py`, and add `adapters.py`
  - Move `Issue` and core types to `core.py`; re-export through `__init__.py`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 5.1, 6.1, 6.3_

- [x] 4.2 Priority queue package `src/meridian/core/priority_queue/`
  - Add modules: `__init__.py`, `config.py`, `queue.py`, `fairness.py`, `processor.py`
  - Move code from `priority_queue.py` accordingly and add tests for fairness invariants
  - Establish authoring constraint: keep newly created modules and test files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 5.2, 6.1, 6.3, 7.3_

- [x] 4.3 Runtime plan package `src/meridian/core/runtime_plan/`
  - Add modules: `__init__.py`, `creation.py`, `execution.py`, `optimization.py`
  - Move code from `runtime_plan.py` accordingly and re-export `RuntimePlan`
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 5.3, 6.1, 6.3_

- [x] 4.4 Policies package `src/meridian/core/policies/`
  - Add modules: `__init__.py`, `definitions.py`, `enforcement.py`, `backpressure.py`
  - Move code from `policies.py` accordingly and re-export public policies
  - Establish authoring constraint: keep newly created modules/files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 5.4, 6.1, 6.3_

- [x] 4.5 Import maps and migration aids
  - Provide centralized import maps in package `__init__.py` files for backward compatibility
  - Add optional deprecation warnings for deep internal imports
  - _Requirements: 6.3, 8.3_

- [x] 5. Phase 5 — Cleanup, docs, and optimization
  - Update documentation to reflect new module structure and boundaries
  - Add import guidelines and examples in `docs/concepts/` and `docs/reference/`
  - _Requirements: 1.4, 6.4, 8.4_

- [x] 5.1 Update tests to mirror new module structure
  - Organize tests under `tests/unit/core/<module>/...` as per design
  - Add import-compatibility tests and ensure existing tests remain valid
  - Establish authoring constraint: keep newly created test files around 200 LOC; keep under 300 LOC unless strongly justified; split further otherwise
  - _Requirements: 7.1, 7.2_

- [x] 5.2 Performance verification and regression guardrails
  - Re-run benchmarks; compare to baseline and document deltas
  - Add CI checks or thresholds for significant performance regressions
  - _Requirements: 7.3, 8.2_

- [x] 5.3 Examples, notebooks, and docs validation
  - Verify `docs/examples/`, `examples/`, and `notebooks/` execute without changes
  - Update any broken references; add notes about preserved imports
  - _Requirements: 7.4, 8.4_

- [x] 6. Migration and release readiness
  - Prepare `CHANGELOG.md` entries and migration notes (if any internal paths are deprecated)
  - Ensure `mkdocs` navigation and links remain correct
  - Merge branch after green CI and sign-off
  - _Requirements: 8.1, 8.2, 8.3, 8.4_
