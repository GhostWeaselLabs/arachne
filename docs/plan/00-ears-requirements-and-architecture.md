# EARS Master Requirements and Architecture

Status: Master Plan (authoritative source)
Owners: Core Maintainers
Version: 1.0 (pre-implementation)
Scope: Arachne Graph Runtime (in‑process, single‑runtime, asyncio‑friendly)

Overview
This document codifies the essential requirements using the EARS pattern and establishes the top‑level architecture for Arachne’s minimal, reusable graph runtime. It governs the design, implementation, testing, and operations of v1 and aligns downstream plans and milestone files.

Legend (EARS)
- Ubiquitous: “The system shall …”
- Event-driven: “When <event>, the system shall …”
- Unwanted behavior: “If <condition>, the system shall …”
- State-driven: “While <state>, the system shall …”
- Complex: “Where <context>, the system shall …”


1) EARS Requirements

1.1 Core Model and APIs
- Ubiquitous: The system shall model applications as graphs of Nodes connected by typed Edges and composed into Subgraphs.
- Ubiquitous: The system shall expose public APIs for Node, Edge, Subgraph, Scheduler, Message, PortSpec, and Policies.
- Ubiquitous: The system shall be framework‑agnostic and in‑process, with APIs friendly to asyncio usage without requiring it.
- Ubiquitous: The system shall prefer small files (~200 LOC/file) and SRP/DRY throughout the codebase.
- Ubiquitous: The system shall provide reproducible development with a uv‑native workflow (init, lock, sync, run).

1.2 Node Lifecycle and Behavior
- Ubiquitous: The system shall define Node lifecycle hooks: on_start, on_message, on_tick, on_stop.
- Event-driven: When a message arrives on an input port, the system shall invoke on_message(port, msg) for the target Node.
- Event-driven: When the configured tick cadence elapses, the system shall invoke on_tick for runnable Nodes.
- Unwanted: If a Node raises an exception in a lifecycle hook, the system shall capture and report it via observability and apply the Node’s error policy (default: skip and continue).

1.3 Messaging, Types, and Ports
- Ubiquitous: The system shall define Message with payload and headers (trace_id, timestamp, schema_version, content_type, …).
- Ubiquitous: The system shall define PortSpec with name, schema/type, and overflow policy fields.
- Complex: Where a schema adapter (e.g., Pydantic) is present, the system shall validate payloads according to the provided model without adding a hard dependency.

1.4 Edges, Capacity, and Overflow Policies
- Ubiquitous: The system shall implement typed, bounded Edges with capacity.
- Ubiquitous: The system shall support overflow policies: block (default), drop, latest, and coalesce(fn).
- Unwanted: If an Edge reaches capacity with policy block, the system shall apply backpressure upstream and avoid busy‑waiting.
- Unwanted: If an Edge reaches capacity with policy drop, the system shall drop new messages and increment a drop metric.
- Unwanted: If an Edge reaches capacity with policy latest, the system shall retain only the newest message, discarding older ones beyond the limit.
- Unwanted: If an Edge reaches capacity with policy coalesce, the system shall combine messages using the supplied function and preserve type correctness.

1.5 Scheduler, Readiness, and Priorities
- Ubiquitous: The system shall provide a cooperative Scheduler that advances Nodes based on readiness (messages/ticks), fairness, and priorities.
- Complex: Where an Edge is marked control‑plane, the Scheduler shall prioritize its processing over normal data‑plane work.
- State-driven: While the Scheduler is running, it shall maintain fair service among runnable Nodes to avoid starvation.
- Event-driven: When shutdown is requested, the system shall gracefully stop Nodes and drain/flush Edges according to policies and timeout.
- Ubiquitous: The system shall expose runtime mutators for edge priority and capacity with validation and safe application.

1.6 Observability (Logs, Metrics, Tracing)
- Ubiquitous: The system shall emit structured JSON logs for lifecycle events, exceptions, and key actions.
- Ubiquitous: The system shall expose metrics for Nodes (ticks, processed, errors), Edges (depth, rates, drops, blocked time), and Scheduler (runnable nodes, loop latency, priority usage).
- Complex: Where tracing is enabled, the system shall propagate correlation IDs and create spans at Node and Edge boundaries.
- Unwanted: If a message is dropped, the system shall increment a drop metric and avoid log flooding (debug‑level or rate‑limited logs).

1.7 Validation, Composition, and Contracts
- Ubiquitous: The system shall validate Subgraph composition: unique names, port existence, schema compatibility, positive capacities, and consistent policies.
- Unwanted: If validation fails for a fatal issue, the system shall report validation errors clearly and refuse to run the invalid graph.
- Complex: Where adapters are available, the system shall optionally perform richer schema checks without introducing mandatory dependencies.

1.8 Operations, Tooling, and Release Quality
- Ubiquitous: The system shall support uv workflows for development, testing, and examples.
- Ubiquitous: The system shall provide scaffolding commands to generate Node/Subgraph skeletons with typing and tests.
- Ubiquitous: The system shall maintain high coverage (≥90% core; ≥80% overall), linting, and typing gates in CI.
- Ubiquitous: The system shall follow Semantic Versioning and publish artifacts with a documented deprecation policy.

1.9 Performance and Reliability
- State-driven: While under sustained load, the system shall maintain bounded queue depths by applying backpressure and configured policies.
- Unwanted: If the system is idle (no runnable Nodes), it shall avoid busy loops and use an efficient idle strategy.
- Complex: Where observability is enabled, the system shall remain low‑overhead; tracing shall be disabled by default and fast no‑op when off.
- Event-driven: When bursts occur, the system shall enforce overflow policies deterministically and preserve fairness guarantees.

1.10 Security and Compliance
- Ubiquitous: The system shall not embed secrets and shall recommend external configuration for sensitive data.
- Complex: Where payloads might include sensitive information, the system shall provide hooks for log redaction at the application layer.


2) Architecture

2.1 Package Layout (Top‑Level)
- core/
  - message.py — Message and header helpers (trace/timestamps).
  - ports.py — PortSpec, schema typing, adapter glue.
  - policies.py — Overflow policies: block/drop/latest/coalesce.
  - edge.py — Bounded queue, typed, metrics hooks, backpressure.
  - node.py — Base class, lifecycle, emit routing.
  - subgraph.py — Composition, expose ports, validation.
  - scheduler.py — Cooperative loop, priorities, fairness, shutdown.
- observability/
  - logging.py — JSON logs, context enrichment.
  - metrics.py — Interfaces, no‑op default, Prometheus adapter.
  - tracing.py — Optional tracing adapter, contextvars propagation.
- utils/
  - ids.py — Correlation/IDs helpers.
  - time.py — Time/timing helpers, monotonic clocks.
  - validation.py — Contract checks for ports/graphs; Issue model.
- scaffolding/
  - generate_node.py — Node generator CLI and templates.
  - generate_subgraph.py — Subgraph generator CLI and templates.
- examples/
  - hello_graph/, pipeline_demo/ — Runnable examples.

2.2 Core Responsibilities and Interactions
- Message: Immutable‑by‑convention container with headers; ensures trace_id presence.
- PortSpec: Describes port schema and default policy; drives Edge typing and validation.
- Policy: Encapsulates overflow behavior; returns decisions that Edge applies.
- Edge: Owns capacity, queue, and applies policy; exposes metrics intents and depth.
- Node: Implements lifecycle; uses emit() to push messages through output ports.
- Subgraph: Manages Nodes, connects ports via Edges, exposes inputs/outputs; validates wiring.
- Scheduler: Discovers readiness (messages or tick), enforces priorities and fairness, drives Node hooks, cooperates with backpressure.

2.3 Scheduling Model
- Readiness Sources:
  - Message‑ready: Node has non‑empty input queues.
  - Tick‑ready: Node’s tick interval elapsed (global cadence with hints).
- Priority Bands:
  - Control-plane > High > Normal (simple ratios, e.g., 4:2:1).
  - Node’s effective band is the highest of its ready inputs.
- Fairness:
  - Round‑robin within band; bounded work per turn (batch size) to control tail latency.
- Backpressure Cooperation:
  - emit() → Edge.put() returns PutResult: OK | BLOCKED | DROPPED | COALESCED.
  - BLOCKED yields producer slot; consumer is scheduled to make forward progress.

2.4 Validation Model
- Graph Validation:
  - Unique node names; unique edge IDs; valid capacities (>0).
  - Port existence and schema compatibility; exposure maps to real ports.
  - Policy presence and sensible defaults.
- Issues:
  - Severity: error | warning; clear messages with location (node/port/edge).
  - Fatal errors prevent run; warnings logged for visibility.

2.5 Observability Model
- Logs:
  - Line‑delimited JSON; fields include ts, level, component, event, node, port, edge_id, trace_id.
  - Levels: info for lifecycle; debug for high‑rate events; warn/error for issues.
- Metrics:
  - Node: messages_total, errors_total, tick_duration histogram.
  - Edge: enqueued_total, dequeued_total, dropped_total, queue_depth, blocked_time seconds.
  - Scheduler: runnable_nodes, loop_latency histogram, priority_applied counters.
- Tracing:
  - Optional spans for on_message/on_tick and edge events; correlation via headers.trace_id and contextvars.

2.6 Configuration and Mutability
- SchedulerConfig (constructor or builder):
  - tick_interval_ms, fairness_ratio, max_batch_per_node, idle_sleep_ms, shutdown_timeout_s.
- Runtime Mutators:
  - set_priority(edge_id, priority)
  - set_capacity(edge_id, capacity)
- ObservabilityConfig:
  - logs: level, json
  - metrics: exporter=noop|prometheus, buckets
  - tracing: enabled, provider=opentelemetry|noop, sample_rate

2.7 Performance Principles
- Keep hot paths allocation‑light; prebind metric label handles.
- Use integer IDs internally; map to labels lazily for export.
- Avoid per‑message heavy validation; support adapters for strict modes.
- Bound per‑iteration work to avoid tail‑latency blowups.

2.8 Error Handling and Shutdown
- Node Errors:
  - Catch and record; default policy “skip and continue” until a more advanced policy is configured.
- Shutdown:
  - Stop accepting new inputs; attempt drain per policy; on timeout, finalize with best effort.
  - Invoke on_stop in reverse topological order.

2.9 Security and Compliance Considerations
- No embedded secrets; configuration externalized.
- Log redaction hooks available for payloads; off by default.
- Documentation notes for safe deployment patterns.


3) Traceability to Milestones

- M1 Bootstrap & CI: Satisfies Ops and Release Quality requirements (1.8).
- M2 Core Primitives: Satisfies Core Model/APIs (1.1), Node/Ports/Messaging (1.2–1.4), and Validation (1.7).
- M3 Scheduler: Satisfies Scheduling (1.5), Backpressure cooperation, and Shutdown semantics.
- M4 Observability: Satisfies Observability (1.6), including logs/metrics/tracing wiring.
- M5 Utilities & Scaffolding: Satisfies Operations/Tooling (1.8) and Validation helpers (1.7).
- M6 Examples & Docs: Demonstrates Core, Policies, Priorities, and Observability in runnable form.
- M7 Testing & Hardening: Satisfies Performance and Reliability (1.9), coverage targets, and soak/stress.
- M8 Release: Satisfies Versioning/Artifacts and deprecation policies under (1.8).


4) Acceptance Criteria (Master)

- Public APIs for Node, Edge, Subgraph, Scheduler, Message, PortSpec, and Policies are implemented and documented.
- Scheduler enforces readiness, fairness, and control‑plane priority; backpressure is cooperative and non‑busy.
- Bounded Edges enforce capacity with policies block/drop/latest/coalesce and expose depth/rate/drop metrics.
- Observability provides JSON logs, metrics interface (no‑op + Prometheus adapter), and optional tracing hooks; overhead acceptable.
- Validation guards composition with explicit Issues and clear errors for fatal misconfigurations.
- Examples run via uv; docs provide quickstart, API overview, patterns, troubleshooting, and observability guidance.
- CI gates: lint, type, tests, coverage; core ≥90%, overall ≥80%.
- Semantic Versioning process in place; initial stable release criteria met.


5) Risks and Mitigations

- Overengineering Scheduler or Policies:
  - Mitigation: Keep v1 cooperative and band‑biased; no complex RT algorithms; policies encapsulated with small interfaces.
- Hidden Domain Coupling:
  - Mitigation: No domain‑specific types; examples remain neutral; adapters optional.
- Observability Overhead:
  - Mitigation: No‑op defaults; guard debug logs; pre‑bound labels; tracing disabled by default.
- API Instability:
  - Mitigation: EARS master governs changes; changelog and deprecations formalized; tests enforce contracts.
- Performance Regressions:
  - Mitigation: Benchmarks with budgets; CI regression checks; profiling before release.


6) Glossary

- Control‑plane: Edges carrying critical signals (e.g., kill switch) that must preempt data‑plane work.
- Backpressure: Mechanism to slow upstream producers when downstream capacity is exhausted.
- Coalesce: Policy that merges multiple queued messages into a single representative message to compress bursts.
- Runnable: A Node ready to execute due to available input or elapsed tick cadence.
- Fairness: Guarantee that no ready Node remains perpetually starved under the Scheduler’s policy.


7) Change Management

- Any change to public APIs or core semantics must update this master file and relevant milestone plans.
- Deviations from EARS requirements must be discussed, recorded here, and reflected in docs and tests before merging.
- Version bumps and deprecations follow the Release milestone policy.
