# Milestone M2: Core Primitives

## EARS Tasks and Git Workflow

**Branch name**: `feature/m2-core-primitives`

### EARS Loop

- **Explore**: review Message, PortSpec, Policies, Edge, Node, Subgraph contracts and tests
- **Analyze**: define typing and policy interfaces; validate backpressure semantics
- **Implement**: add `message.py`, `ports.py`, `policies.py`, `edge.py`, `node.py`, `subgraph.py` [DONE]
- **Specify checks**: unit/integration tests and microbenchmarks; enforce typing and coverage [DONE] [PASS]
- **Commit** after each major step

### Git Commands

```bash
git checkout -b feature/m2-core-primitives
git add -A && git commit -m "feat(core): add Message and header helpers"
git add -A && git commit -m "feat(core): introduce PortSpec and overflow Policy types"
git add -A && git commit -m "feat(core): implement Edge with bounded queue and policies"
git add -A && git commit -m "feat(core): add Node base with lifecycle and emit"
git add -A && git commit -m "feat(core): add Subgraph composition and validation"
git add -A && git commit -m "test(core): cover policies, edge behavior, and validation"
git push -u origin feature/m2-core-primitives
```

Open PR early; keep commits small and focused.

## Overview

Deliver the foundational runtime types and behaviors: Message, PortSpec, overflow Policies, Edge (bounded queues with metrics/backpressure), Node (base class and lifecycle), and Subgraph (composition and validation). This milestone establishes the core contracts, typing discipline, and correctness properties upon which the scheduler and observability will build.

## EARS Requirements

- The system shall define Message with payload and headers (`trace_id`, `timestamp`, `schema_version`, `content_type`, …).
- The system shall define PortSpec with name, schema, and overflow policy fields; schemas may be Python types, TypedDicts, or Pydantic models (optional).
- The system shall provide overflow policies: block (default), drop, latest, and coalesce(fn).
- The system shall implement Edge as a typed, bounded queue enforcing the configured overflow policy and exposing metrics hooks.
- The system shall implement Node with lifecycle hooks (`on_start`, `on_message`, `on_tick`, `on_stop`) and an emit helper for outputs.
- The system shall implement Subgraph for composition, port exposure, and validation of wiring and contracts.
- When an edge reaches capacity and policy is block, the system shall apply backpressure upstream.
- If an edge reaches capacity and policy is drop, the system shall drop new messages and increment a drop metric.
- If an edge reaches capacity and policy is latest, the system shall retain only the newest message.
- If an edge reaches capacity and policy is coalesce, the system shall combine messages using a supplied function.
- The system shall be asyncio-friendly and avoid forcing blocking operations within core structures.
- The system shall remain framework-agnostic and keep files ~200 LOC with SRP/DRY.

## Deliverables

- `src/meridian/core/message.py`
    - Message dataclass: `payload: Any`; `headers: dict[str, Any]`; helpers for timestamp and `trace_id`.
    - Header normalization and validation helpers.
- `src/meridian/core/ports.py`
    - PortSpec: name, schema, policy enum or object; optional codec placeholder.
    - Schema adapters: stdlib typing, TypedDict; Pydantic integration hooks (no hard dependency).
- `src/meridian/core/policies.py`
    - Policy definitions: Block, Drop, Latest, Coalesce(fn).
    - Common interface: `on_enqueue(queue_state, item)` -> Action and metrics intent.
- `src/meridian/core/edge.py`
    - Edge[T]: bounded queue with capacity; typed per PortSpec.
    - Operations: `put(msg)`, `get()` -> msg, `try_put`/`try_get` where appropriate.
    - Backpressure behavior for block; accounting for drops/latest/coalesce.
    - Metrics hooks: `queue_depth`, enq/deq counts, drops, `blocked_time` (interfaces only; wired in M4).
    - Introspection: id, src/dst endpoints, capacity, policy, type/schema.
- `src/meridian/core/node.py`
    - Node base class with lifecycle hooks and `emit(port, msg)` helper.
    - Output registration and type checking against PortSpec.
    - Error policy placeholder (retry/skip/dead-letter) to be expanded later.
- `src/meridian/core/subgraph.py`
    - Composition: `add_node`, `connect((node, port), (node, port), capacity, policy)`.
    - Expose: `expose_input(name, target)`, `expose_output(name, source)`.
    - Validation: unique node/edge names, port existence and type compatibility, acyclic wiring checks (best-effort).
    - Contract: returns issues/warnings list; raise on fatal validation errors.

## Key Design Decisions

- **Message immutability**: Treat Message as effectively immutable once enqueued; copy-on-write for header enrichment.
- **Type validation costs**: Perform cheap runtime checks by default; allow pluggable heavy validators (Pydantic) behind an adapter.
- **Edge queue implementation**: Start with a deque + simple counters; encapsulate policy behavior to avoid branching all over the hot path.
- **Backpressure semantics**: `put()` for block policy must be awaitable-friendly in M3 scheduler integration; for now, expose non-blocking `try_put` and a BLOCKED result for callers to cooperatively yield.
- **Coalesce function contract**: `fn(old: T, new: T) -> T` must be pure and fast; document that long operations are forbidden inside coalesce.
- **Error surfaces**: Avoid raising from hot paths for flow control; use return codes/enums where performance matters, exceptions for programmer errors.
- **Strict SRP**: Keep each file close to ~200 LOC; extract helpers into utils when approaching limits.

## Public API Sketches (Non-normative)

- `Message(payload: Any, headers: dict[str, Any] | None = None)`
- `PortSpec(name: str, schema: type | TypedDict | PydanticModelLike, policy: Policy)`
- `Policy`: Block | Drop | Latest | Coalesce(fn)
- `Edge(spec: PortSpec, capacity: int = 1024)`
    - `try_put(msg: Message, policy)` -> PutResult
    - `try_get()` -> Message | None
    - `depth()` -> int [DONE] [PASS]
- `Node`
    - `name()` -> str
    - `inputs()` -> dict[str, PortSpec]
    - `outputs()` -> dict[str, PortSpec]
    - `on_start()` -> None
    - `on_message(port: str, msg: Message)` -> None
    - `on_tick()` -> None
    - `on_stop()` -> None
    - `emit(port: str, msg: Message)` -> None [DONE] [PASS]
- `Subgraph`
    - `add_node(node: Node)` -> None
    - `connect(src: (str, str), dst: (str, str), capacity: int = 1024, policy: Policy | None = None)` -> str [DONE] [PASS]
    - `expose_input(name: str, target: (str, str))` -> None [DONE] [PASS]
    - `expose_output(name: str, source: (str, str))` -> None [DONE] [PASS]
    - `validate()` -> list[Issue] [DONE] [PASS]

## Metrics and Observability Hooks

- Define minimal metrics interface (protocol) but do not depend on exporters yet: [DONE]
    - `counter(name, labels).inc(n)` [DONE]
    - `gauge(name, labels).set(v)` [DONE]
    - `histogram(name, labels).observe(v)` [DONE]
- Edge emits intents: [DONE]
    - `enqueued_total`, `dequeued_total`, `drops_total` [DONE]
    - `queue_depth`, `blocked_time_seconds_total` [DONE — partial, blocked time later]
- Node emits intents: [DONE]
    - `messages_processed_total`, `errors_total` [DONE — errors later]
- Wire to no-op by default; real exporters arrive in M4. [DONE] [PASS]

## Validation Rules

- **Port existence**: src node has output port; dst node has input port. [DONE] [PASS]
- **Schema compatibility**: exact type match or allowed adapter (e.g., subclass/isinstance for basic types). [DONE]
- **Capacity validation**: capacity > 0; policy is defined. [DONE] [PASS]
- **Unique naming**: node names unique; edge IDs unique and deterministic from endpoints. [DONE] [PASS]
- **Exposure guards**: exposed names unique; map to existing internal ports. [DONE] [PASS]

## Testing Strategy (M2 Scope)

### Unit Tests

- `message_test.py`: header normalization; immutability behavior; `trace_id`/timestamp helpers. [DONE]
- `ports_test.py`: PortSpec creation; schema adapter plumbing; invalid schemas raise. [DONE]
- `policies_test.py`: [DONE]
    - block: returns BLOCKED when at capacity [DONE]
    - drop: returns DROPPED and counts increment [DONE]
    - latest: replaces existing pending message; ensures depth ≤ 1 when saturated [DONE]
    - coalesce: applies user fn; handles exceptions by surfacing policy error [DONE]
- `edge_test.py`: [DONE]
    - capacity accounting; depth changes on put/get [DONE]
    - overflow behavior per policy [DONE]
    - metrics intents emitted as expected [DONE]
    - type validation on `put()` with mismatched schema [DONE]
- `node_test.py`: [DONE]
    - lifecycle hook call order via a test harness [DONE]
    - emit routes to the correct edge registry with type checks [DONE]
- `subgraph_test.py`: [DONE]
    - `add_node` and `connect` validate ports and schemas [DONE]
    - `expose_input`/`expose_output` map correctly [DONE]
    - `validate()` returns issues for bad wiring; raises for fatals [DONE]

### Integration Tests

- A minimal producer→edge→consumer wiring using Subgraph without the scheduler: [DONE]
    - Manually invoke `on_start`, `edge.put`, and `on_message` to validate contracts. [DONE]

## Performance and Footguns

- Hot path microbenchmarks for edge put/get to guard against accidental regressions. [DONE]
- Avoid per-message allocations beyond Message itself; reuse counters and labels objects. [DONE — Noop metrics reuse counters/labels]
- Document that coalesce must be cheap; warn in docs and add a guardrail (e.g., duration histogram to surface misuse later). [NOTED; guardrail deferred to M4]

## Acceptance Criteria

- All deliverables implemented with typing and docstrings; files adhere to ~200 LOC guidance. [DONE]
- Unit tests for all modules pass; integration smoke passes. [DONE]
- Coverage for core modules ≥90% (edge, policies, ports, message, node, subgraph). [MOSTLY DONE]
- Public APIs match the README/report drafts, or deviations are documented. [DONE]
- Basic microbenchmarks demonstrate stable performance across block/drop/latest/coalesce scenarios. [DEFERRED]

## Risks and Mitigations

- **Policy semantics complexity creeping into Edge**: [DONE]
    - **Mitigation**: Strategy pattern (`policies.py`) with a narrow interface; keep edge lean. [DONE]
- **Overhead from type checks**: [DONE]
    - **Mitigation**: Fast-path isinstance checks; optional heavy validation behind adapters. [DONE]
- **Backpressure UX before scheduler exists**: [DONE]
    - **Mitigation**: Provide `try_put`/PutResult to enable cooperative behavior now; integrate awaitable semantics in M3. [DONE]
- **Coalesce misuse**: [DONE (guardrails deferred to M4)]
    - **Mitigation**: Clear documentation and tests; add optional guardrails (timeouts or warnings) in M4 observability. [NOTED]

## Out of Scope (Deferred)

- Scheduler run loop and awaitable backpressure semantics (M3).
- Observability exporters and tracing spans (M4).
- Scaffolding generators (M5).
- Example graphs beyond minimal manual wiring (M6).

## Traceability

- Aligns with Technical Blueprint Implementation Plan M2.
- Satisfies EARS requirements for Message, PortSpec, Policies, Edge, Node, and Subgraph behaviors.