# Codebase Modularization (Phased)

This release includes internal refactors to modularize several monolithic files into focused packages while preserving the public API.

Highlights:
- Scheduler split into `meridian.core.scheduler` package (config, coordination, execution, fairness, shutdown)
- Observability split across packages: `meridian.observability.{tracing,metrics,logging}`
- Core graph components split: `meridian.core.{node,subgraph,edge}` packages
- Utilities: `meridian.core.{priority_queue,runtime_plan,policies}` packages

Backwards compatibility:
- All public imports from `meridian.core` and `meridian.observability` continue to work via re-exports
- Added import compatibility tests in the test suite

Migration notes:
- No breaking changes expected. If deep internal imports were used, prefer the package entry points.

Owner: GhostWeasel
