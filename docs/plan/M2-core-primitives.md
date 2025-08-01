# Milestone M2: Core Primitives

## EARS Tasks and Git Workflow

Branch name: feature/m2-core-primitives

EARS loop
- Explore: review Message, PortSpec, Policies, Edge, Node, Subgraph contracts and tests
- Analyze: define typing and policy interfaces; validate backpressure semantics
- Implement: add message.py, ports.py, policies.py, edge.py, node.py, subgraph.py [DONE]
- Specify checks: unit/integration tests and microbenchmarks; enforce typing and coverage [DONE] [PASS]
- Commit after each major step

Git commands
- git checkout -b feature/m2-core-primitives
- git add -A && git commit -m "feat(core): add Message and header helpers"
- git add -A && git commit -m "feat(core): introduce PortSpec and overflow Policy types"
- git add -A && git commit -m "feat(core): implement Edge with bounded queue and policies"
- git add -A && git commit -m "feat(core): add Node base with lifecycle and emit"
- git add -A && git commit -m "feat(core): add Subgraph composition and validation"
- git add -A && git commit -m "test(core): cover policies, edge behavior, and validation"
- git push -u origin feature/m2-core-primitives
- Open PR early; keep commits small and focused

Status: Planned [DONE] [PASS]
Owner: Core Maintainers
Duration: 3–5 days

Overview
Deliver the foundational runtime types and behaviors: Message, PortSpec, overflow Policies, Edge (bounded queues with metrics/backpressure), Node (base class and lifecycle), and Subgraph (composition and validation). This milestone establishes the core contracts, typing discipline, and correctness properties upon which the scheduler and observability will build.

EARS Requirements
- The system shall define Message with payload and headers (trace_id, timestamp, schema_version, content_type, …).
- The system shall define PortSpec with name, schema, and overflow policy fields; schemas may be Python types, TypedDicts, or Pydantic models (optional).
- The system shall provide overflow policies: block (default), drop, latest, and coalesce(fn).
- The system shall implement Edge as a typed, bounded queue enforcing the configured overflow policy and exposing metrics hooks.
- The system shall implement Node with lifecycle hooks (on_start, on_message, on_tick, on_stop) and an emit helper for outputs.
- The system shall implement Subgraph for composition, port exposure, and validation of wiring and contracts.
- When an edge reaches capacity and policy is block, the system shall apply backpressure upstream.
- If an edge reaches capacity and policy is drop, the system shall drop new messages and increment a drop metric.
- If an edge reaches capacity and policy is latest, the system shall retain only the newest message.
- If an edge reaches capacity and policy is coalesce, the system shall combine messages using a supplied function.
- The system shall be asyncio-friendly and avoid forcing blocking operations within core structures.
- The system shall remain framework-agnostic and keep files ~200 LOC with SRP/DRY.

Deliverables
- src/arachne/core/message.py
  - Message dataclass: payload: Any; headers: dict[str, Any]; helpers for timestamp and trace_id.
  - Header normalization and validation helpers.
- src/arachne/core/ports.py
  - PortSpec: name, schema, policy enum or object; optional codec placeholder.
  - Schema adapters: stdlib typing, TypedDict; Pydantic integration hooks (no hard dependency).
- src/arachne/core/policies.py
  - Policy definitions: Block, Drop, Latest, Coalesce(fn).
  - Common interface: on_enqueue(queue_state, item) -> Action and metrics intent.
- src/arachne/core/edge.py
  - Edge[T]: bounded queue with capacity; typed per PortSpec.
  - Operations: put(msg), get() -> msg, try_put/try_get where appropriate.
  - Backpressure behavior for block; accounting for drops/latest/coalesce.
  - Metrics hooks: queue_depth, enq/deq counts, drops, blocked_time (interfaces only; wired in M4).
  - Introspection: id, src/dst endpoints, capacity, policy, type/schema.
- src/arachne/core/node.py
  - Node base class with lifecycle hooks and emit(port, msg) helper.
  - Output registration and type checking against PortSpec.
  - Error policy placeholder (retry/skip/dead-letter) to be expanded later.
- src/arachne/core/subgraph.py
  - Composition: add_node, connect((node, port), (node, port), capacity, policy).
  - Expose: expose_input(name, target), expose_output(name, source).
  - Validation: unique node/edge names, port existence and type compatibility, acyclic wiring checks (best-effort).
  - Contract: returns issues/warnings list; raise on fatal validation errors.

Key Design Decisions
- Message immutability: Treat Message as effectively immutable once enqueued; copy-on-write for header enrichment.
- Type validation costs: Perform cheap runtime checks by default; allow pluggable heavy validators (Pydantic) behind an adapter.
- Edge queue implementation: Start with a deque + simple counters; encapsulate policy behavior to avoid branching all over the hot path.
- Backpressure semantics: put() for block policy must be awaitable-friendly in M3 scheduler integration; for now, expose non-blocking try_put and a BLOCKED result for callers to cooperatively yield.
- Coalesce function contract: fn(old: T, new: T) -> T must be pure and fast; document that long operations are forbidden inside coalesce.
- Error surfaces: Avoid raising from hot paths for flow control; use return codes/enums where performance matters, exceptions for programmer errors.
- Strict SRP: Keep each file close to ~200 LOC; extract helpers into utils when approaching limits.

Public API Sketches (non-normative)
- Message(payload: Any, headers: dict[str, Any] | None = None)
- PortSpec(name: str, schema: type | TypedDict | PydanticModelLike, policy: Policy)
- Policy: Block | Drop | Latest | Coalesce(fn)
- Edge(spec: PortSpec, capacity: int = 1024)
  - put(msg: Message) -> PutResult
  - get() -> Message | None
  - depth() -> int
- Node
  - name() -> str
  - inputs() -> dict[str, PortSpec]
  - outputs() -> dict[str, PortSpec]
  - on_start() -> None
  - on_message(port: str, msg: Message) -> None
  - on_tick() -> None
  - on_stop() -> None
  - emit(port: str, msg: Message) -> None
- Subgraph
  - add_node(node: Node) -> None
  - connect(src: (str, str), dst: (str, str), capacity: int = 1024, policy: Policy | None = None) -> str
  - expose_input(name: str, target: (str, str)) -> None
  - expose_output(name: str, source: (str, str)) -> None
  - validate() -> list[Issue]

Metrics and Observability Hooks
- Define minimal metrics interface (protocol) but do not depend on exporters yet:
  - counter(name, labels).inc(n)
  - gauge(name, labels).set(v)
  - histogram(name, labels).observe(v)
- Edge emits intents:
  - enqueued_total, dequeued_total, drops_total
  - queue_depth, blocked_time_seconds_total
- Node emits intents:
  - messages_processed_total, errors_total
- Wire to no-op by default; real exporters arrive in M4.

Validation Rules
- Port existence: src node has output port; dst node has input port.
- Schema compatibility: exact type match or allowed adapter (e.g., subclass/isinstance for basic types).
- Capacity validation: capacity > 0; policy is defined.
- Unique naming: node names unique; edge IDs unique and deterministic from endpoints.
- Exposure guards: exposed names unique; map to existing internal ports.

Testing Strategy (M2 scope)
Unit tests
- message_test.py: header normalization; immutability behavior; trace_id/timestamp helpers.
- ports_test.py: PortSpec creation; schema adapter plumbing; invalid schemas raise.
- policies_test.py:
  - block: returns BLOCKED when at capacity
  - drop: returns DROPPED and counts increment
  - latest: replaces existing pending message; ensures depth ≤ 1 when saturated
  - coalesce: applies user fn; handles exceptions by surfacing policy error
- edge_test.py:
  - capacity accounting; depth changes on put/get
  - overflow behavior per policy
  - metrics intents emitted as expected
  - type validation on put() with mismatched schema
- node_test.py:
  - lifecycle hook call order via a test harness
  - emit routes to the correct edge registry with type checks
- subgraph_test.py:
  - add_node and connect validate ports and schemas
  - expose_input/expose_output map correctly
  - validate() returns issues for bad wiring; raises for fatals

Integration tests
- A minimal producer→edge→consumer wiring using Subgraph without the scheduler:
  - Manually invoke on_start, edge.put, and on_message to validate contracts.

Performance and Footguns
- Hot path microbenchmarks for edge put/get to guard against accidental regressions.
- Avoid per-message allocations beyond Message itself; reuse counters and labels objects.
- Document that coalesce must be cheap; warn in docs and add a guardrail (e.g., duration histogram to surface misuse later).

Acceptance Criteria
- All deliverables implemented with typing and docstrings; files adhere to ~200 LOC guidance.
- Unit tests for all modules pass; integration smoke passes.
- Coverage for core modules ≥90% (edge, policies, ports, message, node, subgraph).
- Public APIs match the README/report drafts, or deviations are documented.
- Basic microbenchmarks demonstrate stable performance across block/drop/latest/coalesce scenarios.

Risks and Mitigations
- Policy semantics complexity creeping into Edge:
  - Mitigation: Strategy pattern (policies.py) with a narrow interface; keep edge lean.
- Overhead from type checks:
  - Mitigation: Fast-path isinstance checks; optional heavy validation behind adapters.
- Backpressure UX before scheduler exists:
  - Mitigation: Provide try_put/PutResult to enable cooperative behavior now; integrate awaitable semantics in M3.
- Coalesce misuse:
  - Mitigation: Clear documentation and tests; add optional guardrails (timeouts or warnings) in M4 observability.

Out of Scope (deferred)
- Scheduler run loop and awaitable backpressure semantics (M3).
- Observability exporters and tracing spans (M4).
- Scaffolding generators (M5).
- Example graphs beyond minimal manual wiring (M6).

Traceability
- Aligns with Technical Blueprint Implementation Plan M2.
- Satisfies EARS requirements for Message, PortSpec, Policies, Edge, Node, and Subgraph behaviors.