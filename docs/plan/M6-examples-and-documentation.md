# Milestone M6: Examples and Documentation (EARS-aligned)

Status: In Progress
Owner: Core Maintainers
Duration: 3–5 days
Branch: feature/m6-examples-docs

## 1) Purpose
Deliver runnable, composable examples and concise documentation that demonstrate core runtime behaviors: lifecycle, composition, backpressure and overflow policies, control‑plane priority, and observability. Adhere to SRP/DRY and small‑file guidance (~200 LOC/file).

## 2) Standards Alignment
- Modularity: ≤ ~200 LOC/file; single‑responsibility modules; avoid hidden coupling.
- SRP/DRY: Factor shared helpers; reuse patterns; eliminate duplication across examples/docs.
- Composability: Favor subgraphs and clear port contracts; validate wiring before run.
- Docs style: Concise pages with copy‑paste commands; cross‑link milestones; EARS‑framed requirements.
- EARS usage: Use Ubiquitous/Event/Unwanted/State/Complex patterns for example specs.
- Observability: JSON logs by default; metrics interface; tracing optional; no sensitive payloads in logs.

## 3) EARS Requirements
- Ubiquitous: The system shall provide runnable examples executable with uv run.
- Ubiquitous: The system shall include hello_graph (producer → consumer) validating end‑to‑end execution.
- Ubiquitous: The system shall include pipeline_demo (validator → transformer → sink) showing backpressure and multiple overflow policies.
- Complex: Where control‑plane edges exist, the system shall demonstrate priority preemption (e.g., kill switch).
- Ubiquitous: The system shall provide documentation for quickstart, API, patterns, troubleshooting, and observability.
- Event‑driven: When a user follows the quickstart, the examples shall run without additional configuration.
- Unwanted: If misconfiguration occurs (e.g., mismatched port types), validation errors shall be clear with remediation steps.
- State‑driven: While reading docs, users shall find concise, copy‑pastable commands for common workflows (init, run, test).

## 4) Deliverables
### Examples
- examples/hello_graph/
  - producer.py: emits a bounded sequence of integers.
  - consumer.py: prints or counts messages.
  - main.py: builds a subgraph, connects ports, runs scheduler.
- examples/pipeline_demo/
  - validator.py: type/schema gate; emits valid only.
  - transformer.py: enrich/normalize payloads.
  - sink.py: slow consumer to trigger backpressure.
  - control.py: kill‑switch via control‑plane edge.
  - main.py: wiring; capacities; policies (block/latest/coalesce); priorities.
- Optional: examples/observability_demo/
  - metrics_tracing.py: enable metrics/tracing via flags; no‑op safe by default.

### Documentation
- docs/quickstart.md: uv workflow; run hello_graph; run pipeline_demo; optional observability flags.
- docs/api.md: concise API overview (Node, Edge, Subgraph, Scheduler, Message, PortSpec, Policies).
- docs/patterns.md: backpressure strategies (block/latest/coalesce); control‑plane priority; subgraph composition; error‑handling patterns.
- docs/troubleshooting.md: wiring errors; type mismatches; diagnosing backpressure; priority issues.
- docs/observability.md: metric catalog (summary); logging format; tracing enablement and sampling.
- README: links to the above; short quickstart.

## 5) Example Authoring Template
### File size and structure
- ≤ ~200 LOC/file; one cohesive class/module per node or subgraph.
- __init__.py optional; expose run entry points if needed.
- Top‑level docstring includes: Purpose; Ports (name:type, policy); Capacity/priorities; Run command (uv run ...).

### Type and policy hygiene
- Static typing for public functions/classes.
- Explicit PortSpec types and policies; capacity and priority set near wiring sites.

### SRP/DRY
- One node class per file; helpers local or shared; avoid duplication across examples.

## 6) Example Checklist
- [x] Files ≤ ~200 LOC; SRP respected.
- [x] Docstring with purpose, ports, capacities, policies, priorities.
- [x] uv run command included and tested.
- [ ] Validation errors are clear if miswired (expand troubleshooting examples).
- [ ] Metrics/logs visible (no‑op safe); tracing guarded by optional deps.
- [x] Smoke tests in CI.

## 7) Commands
Quickstart
- uv init
- uv lock
- uv sync
- uv run python -m examples.hello_graph.main
- uv run python -m examples.pipeline_demo.main

Optional observability
- Enable metrics/tracing via env flags or code switches; default to no‑op when disabled.

## 8) EARS Template (for examples and docs)
- Ubiquitous: The example shall <goal/behavior>.
- Event‑driven: When <event>, the example/system shall <behavior>.
- Unwanted: If <failure/condition>, the example/system shall <mitigation>.
- State‑driven: While <state>, the example/system shall <policy>.
- Complex: Where <context/adapter>, the example/system shall <behavior>.

## 9) Example Specs (EARS)
### hello_graph
- Ubiquitous: The example shall demonstrate producer→consumer message flow and node lifecycle.
- Event‑driven: When producer ticks, it shall emit an integer Message to the output port.
- Event‑driven: When consumer receives a Message, it shall record/print the payload.
- State‑driven: While the edge capacity is not exceeded, enqueue operations shall succeed with policy=block.
- Unwanted: If the consumer raises, the runtime shall log a structured error and continue per default node error policy.

### pipeline_demo
- Ubiquitous: The example shall demonstrate validation, transformation, and backpressure under varied overflow policies.
- Event‑driven: When validator receives input, it shall drop or flag invalid payloads and emit valid ones only.
- State‑driven: While the sink is slow, the Transformer→Sink edge with policy=latest shall retain only the newest message beyond capacity.
- Event‑driven: When a kill‑switch control‑plane message is emitted, the scheduler shall prioritize its processing and initiate graceful shutdown.
- Unwanted: If an edge reaches capacity with policy=coalesce, the example shall coalesce burst messages via a supplied function and expose behavior via logs/metrics.

### observability_demo (optional)
- Ubiquitous: The example shall demonstrate enabling metrics and optional tracing with minimal overhead.
- Event‑driven: When nodes process messages, counters and histograms shall update; tracing spans shall be created only if enabled.
- Unwanted: If tracing is not installed, the example shall run with a no‑op provider without errors.

### subgraph_composition_mini
- Ubiquitous: The example shall demonstrate composing two subgraphs into a larger graph with exposed ports.
- Event‑driven: When subgraph A emits, subgraph B shall receive via exposed connectors with validated PortSpec types.
- Unwanted: If port types mismatch, validation shall fail with a clear Issue and location.

## 10) Documentation Structure and Cross‑Links
- quickstart.md → examples; patterns.md
- api.md → code docstrings; patterns.md
- patterns.md → troubleshooting.md
- troubleshooting.md → observability.md
- observability.md → api.md (metrics/tracing)

## 11) Testing and Acceptance
Docs lint and snippets
- [ ] Validate code blocks/snippets compile/run in CI.

Example smoke tests
- [x] hello_graph: run and assert N outputs observed.
- [x] pipeline_demo: basic smoke runs; backpressure path sketched; refine assertions next.
- [ ] observability_demo: metrics counters increment; tracing path does not error when disabled.

CI acceptance
- [x] Examples run via uv on clean clone.
- [ ] Snippet checks pass.
- [x] Coverage impact acceptable.

## 12) Git Workflow
- git checkout -b feature/m6-examples-docs
- Incremental commits per example/doc page; PR early; keep commits small.

## 13) Traceability
- Aligns with M0 governance (SRP/DRY, small modules, docs‑as‑product).
- Implements EARS master for examples, policies, scheduler priorities, and observability.

## 14) Current Status Summary
- Examples: hello_graph and pipeline_demo stubs implemented and runnable.
- Typing: mypy strict pass across src/; optional pydantic guarded.
- Lint: ruff clean (auto‑fixed).
- Tests: pytest passing locally.
- Scaffolding: legacy generate_test_template wrapper restored (deprecated; remove pre‑1.0).

## 15) Remaining TODOs
- Write docs pages: quickstart, api, patterns, troubleshooting, observability.
- Add observability_demo example and snippet docs.
- Strengthen pipeline_demo assertions for backpressure and coalesce behaviors.
- Add docs snippet CI to validate code blocks.
- Plan removal of legacy scaffolding alias before 1.0 and update tests/docs.
