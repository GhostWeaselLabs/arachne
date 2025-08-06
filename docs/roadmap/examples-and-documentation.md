# Milestone M6: Examples and Documentation (EARS-aligned)

**Branch**: main (merged from `feature/m6-examples-docs`)

---

## Purpose

Deliver runnable, composable examples and concise documentation that demonstrate core runtime behaviors: lifecycle, composition, backpressure and overflow policies, control‑plane priority, and observability. Adhere to SRP/DRY and small‑file guidance (~200 LOC/file).

---

## Standards Alignment

- **Modularity**: ≤ ~200 LOC/file; single‑responsibility modules; avoid hidden coupling.
- **SRP/DRY**: Factor shared helpers; reuse patterns; eliminate duplication across examples/docs.
- **Composability**: Favor subgraphs and clear port contracts; validate wiring before run.
- **Docs style**: Concise pages with copy‑paste commands; cross‑link milestones; EARS‑framed requirements.
- **EARS usage**: Use Ubiquitous/Event/Unwanted/State/Complex patterns for example specs.
- **Observability**: JSON logs by default; metrics interface; tracing optional; no sensitive payloads in logs.

---

## EARS Requirements

- **Ubiquitous**: The system shall provide runnable examples executable with `uv run`. [DONE][PASSING]
- **Ubiquitous**: The system shall include `hello_graph` (producer → consumer) validating end‑to‑end execution. [DONE][PASSING]
- **Ubiquitous**: The system shall include `pipeline_demo` (validator → transformer → sink) showing backpressure and multiple overflow policies. [DONE][PASSING]
- **Complex**: Where control‑plane edges exist, the system shall demonstrate priority preemption (e.g., kill switch). [DONE]
- **Ubiquitous**: The system shall provide documentation for quickstart, API, patterns, troubleshooting, and observability. [DONE]
- **Event‑driven**: When a user follows the quickstart, the examples shall run without additional configuration. [DONE][PASSING]
- **Unwanted**: If misconfiguration occurs (e.g., mismatched port types), validation errors shall be clear with remediation steps. [PARTIAL]
- **State‑driven**: While reading docs, users shall find concise, copy‑pastable commands for common workflows (init, run, test). [DONE]

---

## Deliverables

### Examples

- `examples/hello_graph/` [DONE][PASSING]
    - `producer.py`: emits a bounded sequence of integers. [DONE]
    - `consumer.py`: prints or counts messages. [DONE]
    - `main.py`: builds a subgraph, connects ports, runs scheduler. [DONE]
- `examples/pipeline_demo/` [DONE][PASSING]
    - `validator.py`: type/schema gate; emits valid only. [DONE]
    - `transformer.py`: enrich/normalize payloads. [DONE]
    - `sink.py`: slow consumer to trigger backpressure. [DONE]
    - `control.py`: kill‑switch via control‑plane edge. [DONE]
    - `main.py`: wiring; capacities; policies (block/latest/coalesce); priorities. [DONE]
- Optional: `examples/observability_demo/`
    - `metrics_tracing.py`: enable metrics/tracing via flags; no‑op safe by default. [TODO]

### Documentation

- `docs/quickstart.md`: `uv` workflow; run `hello_graph`; run `pipeline_demo`; optional observability flags. [DONE]
- `docs/api.md`: concise API overview (Node, Edge, Subgraph, Scheduler, Message, PortSpec, Policies). [DONE]
- `docs/patterns.md`: backpressure strategies (block/latest/coalesce); control‑plane priority; subgraph composition; error‑handling patterns. [DONE]
- `docs/troubleshooting.md`: wiring errors; type mismatches; diagnosing backpressure; priority issues. [DONE]
- `docs/observability.md`: metric catalog (summary); logging format; tracing enablement and sampling. [DONE]
- `README`: links to the above; short quickstart. [DONE]

---

## Example Authoring Template

### File size and structure

- ≤ ~200 LOC/file; one cohesive class/module per node or subgraph.
- `__init__.py` optional; expose run entry points if needed.
- Top‑level docstring includes: Purpose; Ports (name:type, policy); Capacity/priorities; Run command (`uv run ...`).

### Type and policy hygiene

- Static typing for public functions/classes.
- Explicit `PortSpec` types and policies; capacity and priority set near wiring sites.

### SRP/DRY

- One node class per file; helpers local or shared; avoid duplication across examples.

---

## Example Checklist

- [x] Files ≤ ~200 LOC; SRP respected.
- [x] Docstring with purpose, ports, capacities, policies, priorities.
- [x] `uv run` command included and tested.
- [x] Edge validates `Message.payload` against `PortSpec.schema` (Message-wrapped types supported).
- [ ] Validation errors are clear if miswired (expand troubleshooting examples). [PARTIAL]
- [ ] Metrics/logs visible (no‑op safe); tracing guarded by optional deps. [PARTIAL]
- [x] Smoke tests in CI.

---

## Commands

### Quickstart

```bash
uv init
uv lock
uv sync
uv run python -m examples.hello_graph.main
uv run python -m examples.pipeline_demo.main
```

### Optional observability

- Enable metrics/tracing via env flags or code switches; default to no‑op when disabled.

---

## EARS Template (for examples and docs)

- **Ubiquitous**: The example shall <goal/behavior>.
- **Event‑driven**: When <event>, the example/system shall <behavior>.
- **Unwanted**: If <failure/condition>, the example/system shall <mitigation>.
- **State‑driven**: While <state>, the example/system shall <policy>.
- **Complex**: Where <context/adapter>, the example/system shall <behavior>.

---

## Example Specs (EARS)

### hello_graph

- **Ubiquitous**: The example shall demonstrate producer→consumer message flow and node lifecycle.
- **Event‑driven**: When producer ticks, it shall emit an integer `Message` to the output port.
- **Event‑driven**: When consumer receives a `Message`, it shall record/print the payload.
- **State‑driven**: While the edge capacity is not exceeded, enqueue operations shall succeed with `policy=block`.
- **Unwanted**: If the consumer raises, the runtime shall log a structured error and continue per default node error policy.

### pipeline_demo

- **Ubiquitous**: The example shall demonstrate validation, transformation, and backpressure under varied overflow policies.
- **Event‑driven**: When validator receives input, it shall drop or flag invalid payloads and emit valid ones only.
- **State‑driven**: While the sink is slow, the Transformer→Sink edge with `policy=latest` shall retain only the newest message beyond capacity.
- **Event‑driven**: When a kill‑switch control‑plane message is emitted, the scheduler shall prioritize its processing and initiate graceful shutdown.
- **Unwanted**: If an edge reaches capacity with `policy=coalesce`, the example shall coalesce burst messages via a supplied function and expose behavior via logs/metrics.

### observability_demo (optional)

- **Ubiquitous**: The example shall demonstrate enabling metrics and optional tracing with minimal overhead.
- **Event‑driven**: When nodes process messages, counters and histograms shall update; tracing spans shall be created only if enabled.
- **Unwanted**: If tracing is not installed, the example shall run with a no‑op provider without errors.

### subgraph_composition_mini

- **Ubiquitous**: The example shall demonstrate composing two subgraphs into a larger graph with exposed ports.
- **Event‑driven**: When subgraph A emits, subgraph B shall receive via exposed connectors with validated `PortSpec` types.
- **Unwanted**: If port types mismatch, validation shall fail with a clear `Issue` and location.

---

## Documentation Structure and Cross‑Links

- `quickstart.md` → examples; `patterns.md`
- `api.md` → code docstrings; `patterns.md`
- `patterns.md` → `troubleshooting.md`
- `troubleshooting.md` → `observability.md`
- `observability.md` → `api.md` (metrics/tracing)

---

## Testing and Acceptance

### Docs lint and snippets

- [ ] Validate code blocks/snippets compile/run in CI. [TODO]

### Example smoke tests

- [x] `hello_graph`: run and assert N outputs observed. [DONE][PASSING]
- [x] `pipeline_demo`: basic smoke runs; backpressure path sketched; refine assertions next. [DONE][PASSING]
- [ ] `observability_demo`: metrics counters increment; tracing path does not error when disabled. [TODO]

### CI acceptance

- [x] Examples run via `uv` on clean clone. [DONE][PASSING]
- [ ] Snippet checks pass. [TODO]
- [x] Coverage impact acceptable. [PASSING]

---

## Git Workflow

```bash
git checkout -b feature/m6-examples-docs
```

Incremental commits per example/doc page; PR early; keep commits small.

---

## Traceability

- Aligns with M0 governance (SRP/DRY, small modules, docs‑as‑product).
- Implements EARS master for examples, policies, scheduler priorities, and observability.

---

## Current Status Summary

- **Examples**: `hello_graph` and `pipeline_demo` implemented and runnable. [DONE][PASSING]
- **Docs**: site automated via GitHub Pages; dedicated homepage; nav updated; badges added. [DONE]
- **Typing**: mypy strict pass across `src/`; optional pydantic guarded. [PASSING]
- **Lint**: ruff clean (auto‑fixed). [PASSING]
- **Tests**: pytest passing locally and in CI. [PASSING]
- **CI/CD**: Docs build optimized with caching; pinned deps; deploy green. [DONE][PASSING]
- **Scaffolding**: legacy `generate_test_template` wrapper restored (deprecated; remove pre‑1.0). [KNOWN - TODO remove before 1.0]

---

## Remaining TODOs

- Add `observability_demo` example and snippet docs. [TODO]
- Strengthen `pipeline_demo` assertions for backpressure and coalesce behaviors. [TODO]
- Add docs snippet CI to validate code blocks. [TODO]
- Plan removal of legacy scaffolding alias before 1.0 and update tests/docs. [TODO]
