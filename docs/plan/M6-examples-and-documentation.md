# Milestone M6: Examples and Documentation

Status: Planned
Owner: Core Maintainers
Duration: 3–5 days

Overview
Deliver runnable examples that demonstrate core runtime capabilities and produce end-to-end documentation covering quickstart, API reference, patterns, and troubleshooting. Examples must run with uv and showcase backpressure, overflow policies, and control-plane priorities. Documentation should be concise, modular, and aligned with SRP/DRY, with code listings staying within ~200 LOC/file guidance.

EARS Requirements
- The system shall provide runnable examples that can be executed with uv run.
- The system shall include a minimal hello_graph example (producer → consumer) validating end-to-end execution.
- The system shall include a pipeline_demo example showing validator → transformer → sink with backpressure and multiple overflow policies.
- Where control-plane edges exist, the system shall demonstrate priority preemption (e.g., kill switch).
- The system shall provide documentation for quickstart, API reference, patterns, and troubleshooting.
- When a user follows the quickstart, the examples shall run without additional configuration.
- If an example encounters misconfiguration (e.g., mismatched port types), the system shall present clear validation errors and remediation steps in the docs.
- While reading docs, users shall find concise, copy-pastable commands for common workflows (init, run, test).

Deliverables
Examples
- examples/hello_graph/
  - producer.py: emits a bounded sequence of integers.
  - consumer.py: prints payloads and optionally counts them.
  - main.py: builds a subgraph, connects ports, runs scheduler.
- examples/pipeline_demo/
  - validator.py: checks schema-type and drops/flags invalid items.
  - transformer.py: transforms payloads (e.g., add fields, normalize).
  - sink.py: simulates I/O (slow consumer) to trigger backpressure.
  - control.py: publishes a kill-switch control-plane message.
  - main.py: wires nodes; configures edges with different policies (block, latest, coalesce) and priorities.
- Optional: examples/metrics_tracing_smoke/
  - Demonstrates enabling metrics adapter and tracing hooks (guarded by optional dependencies).

Documentation
- docs/quickstart.md
  - Installation via uv
  - Running examples (hello_graph first, pipeline_demo second)
  - How to enable metrics/tracing in examples (optional)
- docs/api.md
  - Public API overview: Node, Edge, Subgraph, Scheduler, Message, PortSpec, Policies
  - Reference links and signatures (kept concise; full docstrings in code)
- docs/patterns.md
  - Backpressure strategies: block, latest, coalesce
  - Control-plane priority: kill switch, admin signals
  - Subgraphs and composition
  - Error handling patterns (retry, skip, DLQ subgraph)
- docs/troubleshooting.md
  - Common wiring errors and fixes
  - Type mismatches and schema adapter usage
  - Backpressure stalls and how to diagnose with metrics
  - Priority misconfigurations (how to verify and fix)
- docs/observability.md
  - Metric catalog (summary) and recommended dashboards
  - Logging formats and levels
  - Tracing enablement and sampling guidance
- README updates
  - Link the above docs
  - Keep a small quickstart section; refer to docs for details

Example Scenarios and Key Behaviors
hello_graph
- Producer emits n integers on tick.
- Consumer prints values on on_message.
- Subgraph connect capacity configurable (default 16).
- Demonstrates:
  - Node lifecycle invocation
  - Simple message pass-through
  - End-to-end run via scheduler

pipeline_demo
- Nodes:
  - Validator: ensures payload shape (type or TypedDict), emits only valid messages.
  - Transformer: mutates payload (e.g., add normalized fields).
  - Sink: intentionally slow consumer to create backpressure.
  - Control: sends kill switch on a control-plane edge with higher priority.
- Edges and Policies:
  - Validator → Transformer: capacity moderate (e.g., 64), policy=block
  - Transformer → Sink: capacity small (e.g., 8), policy=latest or coalesce
  - Control → Scheduler/All: capacity small, high priority
- Demonstrates:
  - Backpressure with a slow sink
  - latest/coalesce behaviors under burst
  - Priority preemption for kill switch
  - Observability hooks visible when enabled

Content Guidelines
- Keep each example file ≤ ~200 LOC.
- Provide docstrings at the top explaining purpose, ports, and policies used.
- Use explicit typing in public methods.
- Avoid heavy external dependencies; stick to stdlib and the runtime.
- Provide inline comments where policies and priorities are set to teach best practices.

Commands and Runbooks
Quickstart commands (to be included in docs/quickstart.md)
- uv init
- uv lock
- uv sync
- uv run python -m examples.hello_graph.main
- uv run python -m examples.pipeline_demo.main

Optional observability commands
- Enable metrics adapter in code with a flag or environment variable.
- Expose Prometheus metrics via a small adapter script (documented as optional).
- Enable tracing if OpenTelemetry is installed; document that it’s off by default.

Documentation Structure and Cross-Links
- Each doc page has a short overview, three sections max, and links to examples.
- Add “See also” at the bottom:
  - quickstart.md → examples + patterns.md
  - api.md → code docstrings + patterns.md
  - patterns.md → troubleshooting.md
  - troubleshooting.md → observability.md
  - observability.md → api.md (metrics/tracing interfaces)

Testing Strategy
Unit-level (docs lint)
- Validate code snippets in docs compile via a simple doctest-like pass or copy into tests/docs_snippets_test.py.
- Ensure example modules import and pass static checks (mypy relaxed as needed for examples).

Integration-level (example runs)
- hello_graph: run the example entry point; assert the expected number of outputs printed or captured.
- pipeline_demo:
  - Start run; after a burst, assert:
    - Backpressure occurs (via metrics or observed processing latency).
    - latest or coalesce behaviors manifest (e.g., count drops or confirm coalesced outputs).
  - Send kill switch and assert a graceful shutdown path.
- Observability smoke:
  - With metrics enabled, assert key counters increased (edge enqueued/dequeued, node messages).
  - With tracing enabled (if available), ensure no exceptions and optional span creation.

Acceptance Criteria
- hello_graph and pipeline_demo run via uv out of the box on a clean clone.
- Docs are complete, concise, and cross-linked: quickstart, api, patterns, troubleshooting, observability.
- Examples illustrate backpressure and priorities clearly with small, readable files.
- Troubleshooting addresses common user errors with actionable guidance.
- Observability doc shows how to enable metrics and tracing, including sample dashboards/alerts.
- CI executes example smoke tests and validates docs snippets compile.
- Coverage impact remains acceptable; examples may be excluded from coverage totals if necessary.

Risks and Mitigations
- Examples drift from API surface as it evolves:
  - Mitigation: Add CI that imports and runs example entry points; include minimal assertions.
- Overly complex examples obscure learning:
  - Mitigation: Keep hello_graph trivial; reserve complexity for pipeline_demo; add comments.
- Optional observability dependencies confuse users:
  - Mitigation: Default to no-op; clearly label optional installs; guard code paths with feature flags.

Out of Scope (Deferred)
- Distributed examples or multi-process demos.
- Live UI dashboards; provide metric names and suggested panels instead.
- Advanced schema adapters beyond simple Pydantic notes.

Traceability
- Implements Technical Blueprint Implementation Plan M6.
- Satisfies EARS requirements for runnable examples, documentation breadth, backpressure/priority demonstrations, and troubleshooting guidance.

Checklist
- [ ] hello_graph implemented, runs with uv
- [ ] pipeline_demo implemented: validator, transformer, sink, control-plane kill switch
- [ ] quickstart.md written and tested (commands work)
- [ ] api.md concise overview of public APIs
- [ ] patterns.md covers backpressure, priority, composition, error handling
- [ ] troubleshooting.md common failures and fixes
- [ ] observability.md metric catalog summary and enablement guides
- [ ] CI executes example smoke tests and validates docs snippets