# Milestone M3: Scheduler

## EARS Tasks and Git Workflow

**Branch name**: `feature/m3-scheduler`

### EARS Loop

- **Explore**: review readiness signals, priority bands, backpressure cooperation
- **Analyze**: design runnable queues, tick cadence, and BLOCKED handling
- **Implement**: `scheduler.py` run loop, `runtime_plan`, mutators
- **Specify checks**: unit/integration tests for fairness, priorities, shutdown, backpressure
- **Commit** after each major step

### Git Commands

```bash
git checkout -b feature/m3-scheduler
git add -A && git commit -m "feat(scheduler): add Scheduler skeleton and registration"
git add -A && git commit -m "feat(scheduler): implement runnable queues and priority bands"
git add -A && git commit -m "feat(scheduler): cooperative loop with tick cadence and backpressure"
git add -A && git commit -m "feat(scheduler): runtime mutators and graceful shutdown"
git add -A && git commit -m "test(scheduler): fairness, priority bias, shutdown semantics"
git push -u origin feature/m3-scheduler
```

## Overview

Implement the cooperative scheduler that drives node lifecycle and message delivery across the graph. The scheduler evaluates node readiness, drains edges with priority bias for control-plane traffic, and invokes `on_message`/`on_tick` and start/stop hooks. It integrates non-blocking backpressure semantics introduced in M2 and readies the runtime for observability wiring in M4.

## EARS Requirements

- The system shall provide a Scheduler with public APIs:
    - `register(unit: Node | Subgraph)` -> None
    - `run()` -> None
    - `shutdown()` -> None
    - `set_priority(edge_id: str, priority: int)` -> None
    - `set_capacity(edge_id: str, capacity: int)` -> None
- When the scheduler starts, the system shall invoke `on_start` for all nodes exactly once.
- When a message is available on an input edge for a node, the system shall invoke `on_message(port, msg)` respecting type/port contracts.
- When the tick cadence elapses, the system shall invoke `on_tick` on nodes that are runnable.
- If a shutdown is requested, the system shall gracefully stop the graph, invoking `on_stop` on each node, and handle draining/flushing of edges according to policy.
- The system shall prioritize control-plane edges over data-plane edges where priorities are configured.
- While running, the scheduler shall maintain fairness to avoid starvation across runnable nodes.
- If a node raises an exception in a lifecycle callback, the system shall capture it and surface through error channels (logs/metrics in M4), and apply node error policy (retry/skip/stop stubbed for now).
- The system shall support cooperative backpressure: if an output edge signals BLOCKED, the scheduler shall avoid busy-waiting and reschedule producer/consumer appropriately.
- The system shall remain single-process and asyncio-friendly without requiring async to use it (adapter layer can be added later).

## Deliverables

- `src/meridian/core/scheduler.py`
    - Scheduler class and run loop [DONE]
    - Registration of graphs/subgraphs with expansion into an internal plan (nodes, edges, ports) [DONE]
    - Runnable queues and priority biasing [DONE]
    - Tick cadence control [DONE]
    - Graceful shutdown and stop semantics [DONE]
    - Runtime mutators: `set_priority`, `set_capacity` (with validation and safe application) [DONE]
    - Backpressure-aware emit routing glue between `Node.emit` and `Edge.put`/`try_put` [DONE]
- `src/meridian/core/runtime_plan.py` (optional small helper)
    - Flatten Subgraph into execution plan: topo order, node/edge indices, port maps [DONE - integrated into scheduler]
    - Deterministic IDs for edges and addressable endpoints [DONE]
- Minimal integration hooks
    - Metrics/tracing placeholders (no-op) called at key points (loop iteration start/end, callbacks, enqueue/dequeue) [DONE]
- Tests (see Testing Strategy) [DONE - comprehensive unit tests]

## Scheduling Model

- **Cooperative loop**: [DONE]

    - Maintain two primary readiness signals: [DONE]
        1. Message-ready: input queues non-empty for a node [DONE]
        2. Tick-ready: elapsed tick interval for a node (global cadence with per-node hints) [DONE]
    - Maintain a runnable structure keyed by `(priority_class, node_id)` with round-robin within class [DONE]

- **Priorities**: [DONE]

    - Edge priority integer; map to bands (e.g., control-plane > high > normal) [DONE]
    - Node effective class derived from its highest-priority ready input; if none, normal [DONE]
    - Bias: service higher bands more frequently with a simple ratio (e.g., 4:2:1) [DONE]

- **Fairness**: [DONE]

    - Within a band, nodes are scheduled round-robin to avoid starvation [DONE]
    - Limit per-iteration work with a budget (e.g., max messages per node per turn) to bound tail latency [DONE]

- **Backpressure handling**: [DONE]

    - `Node.emit` → `Edge.put` returns PutResult: OK, BLOCKED, DROPPED, COALESCED [DONE]
    - On BLOCKED: mark producing node as yield-required; give consumers a chance; requeue producer later [DONE]
    - Avoid busy waits by tracking edges that caused BLOCKED and revisiting when downstream consumption occurs [DONE]

## Lifecycle and Semantics

- **start()**:

    - Expand subgraphs, allocate runtime plan
    - Initialize nodes: `on_start` in topo order (producers first); catch exceptions
    - Prime tick timers

- **run()**: [DONE]

    - Loop until shutdown flag set and all outstanding work quiesces (subject to policy) [DONE]
    - Each iteration:
        - Pull next node from runnable queues according to priority bands and fairness [DONE]
        - If message-ready: pop one (or small batch) from input edges and invoke `on_message` [DONE]
        - Else if tick-ready: invoke `on_tick` [DONE]
        - Track work done; update metrics intents [DONE]

     - Idle strategy: brief sleep/yield when no work (configurable) [DONE]

- **shutdown()**:

    - Stop accepting new external inputs (if applicable)
    - Drain policy:
        - block: attempt graceful draining until timeout; then stop
        - drop/latest/coalesce: allow loop to quiesce; then stop
    - `on_stop` in reverse topo order (consumers first)

## Public APIs

- `register(unit: Node | Subgraph)` -> None [DONE]
    - Accept a Node or Subgraph; multiple calls allowed before `run()` [DONE]
    - Validate names and conflicts across registrations [DONE]
- `run()` -> None [DONE]
    - Blocking call that runs until shutdown requested [DONE]
    - Optional parameters via constructor: `tick_interval`, `max_batch_per_node`, `idle_sleep_ms` [DONE]
- `shutdown()` -> None [DONE]
    - Signals loop to exit; `run()` returns after graceful stop [DONE]
- `set_priority(edge_id: str, priority: int)` -> None [DONE]
    - Validate edge exists; adjust band assignment atomically [DONE]
- `set_capacity(edge_id: str, capacity: int)` -> None [DONE]
    - Validate and apply to the underlying Edge safely (may require temporary lock) [DONE]

## Configuration

- **SchedulerConfig**
    - `tick_interval_ms`: default tick cadence baseline (e.g., 50–100ms)
    - `fairness_ratio`: e.g., {control: 4, high: 2, normal: 1}
    - `max_batch_per_node`: to bound per-iteration work
    - `idle_sleep_ms`: backoff when no runnable nodes
    - `shutdown_timeout_s`: soft limit for drain on shutdown
- **Node hints** (optional):
    - `desired_tick_interval_ms`
    - `priority_override` for special nodes (discouraged; use edge priorities instead)

## Data Structures

- **Ready queues**:
    - Per-band deque of `node_ids`
    - Map `node_id` -> ReadyState {`message_ready`, `tick_ready`, `blocked_edges`}
- **Edge registry**:
    - `edge_id` -> EdgeRef {`capacity`, `policy`, `priority_band`, `src`, `dst`}
- **Node registry**:
    - `node_id` -> NodeRef {`instance`, `inputs`, `outputs`, `tick_timer`, `error_policy`}
- **Port map**:
    - `(node_id, port_name)` -> `edge_id` for inputs/outputs
- **Message buffers**:
    - Per-input-port pending deque (reads from Edge, small batch caching)

## Error Handling

- **Catch exceptions from hooks**:
    - `on_message`/`on_tick`/`on_start`/`on_stop` wrapped with try/except
    - Record error intent; apply node error policy (default: skip and continue; configurable later)
    - Avoid bringing down the scheduler unless policy demands
- **Misconfiguration at runtime mutators**:
    - `set_priority`/`set_capacity` validate and raise ValueError with context
- **Backpressure and drops**:
    - Respect PutResult; never spin; ensure progress via consumer scheduling

## Testing Strategy

### Unit Tests

- **Ready queues and fairness**:
    - Round-robin servicing within band; ratio across bands respected
- **Priority bias**:
    - Control-plane inputs preempt data-plane consistently
- **Tick cadence**:
    - Tick-ready nodes get scheduled at configured intervals
- **Backpressure flow**:
  -  Producer with BLOCKED result yields; consumer runs; producer resumes successfully
- **Shutdown semantics**:
    - Graceful stop invokes `on_stop` in reverse topo; drain behavior matches policy
- **Runtime mutators**:
    - `set_priority` changes servicing band immediately
    - `set_capacity` applied, validated, and reflected in Edge

### Integration Tests

- **Producer → Edge (block) → Slow Consumer**:
    - Observe producer backpressure and steady-state throughput
- **Control-plane kill switch**:
    - Control edge triggers immediate `on_message` even under heavy data-plane load
- **Mixed policies**:
    - latest/coalesce edges behave under burst; end-to-end message correctness
- **Error propagation**:
    - Node raising in `on_message` doesn't crash loop; error counted and flow continues

### Stress and Reliability

- High-throughput graph (multiple producers/consumers) to validate scheduler loop latency bounds
- Starvation avoidance under varied ready patterns
- Long-running test (30–60 min) without memory growth

## Performance Guidance

- Minimize allocations in loop; pre-allocate small objects where possible
- Prefer integer `node_ids`/`edge_ids` and array-backed structures for hot paths
- Bound per-iteration work to keep tail latency predictable
- Use simple timing (monotonic) and avoid per-iteration system time calls when possible

## Acceptance Criteria

- Scheduler supports run, shutdown, registration of at least one Subgraph
- Priority bias demonstrably preempts data-plane under load
- Backpressure semantics validated with block policy
- Tick cadence operates within tolerance (±1 tick interval under light load)
- All unit/integration tests for scheduler pass; coverage for scheduler ≥90%
- Public API conforms to the draft (README/report), or deviations documented

## Risks and Mitigations

- **Over-engineering scheduling policy**:
    - **Mitigation**: Keep bias ratios simple; no complex RT algorithms in v1
- **Busy waiting under backpressure**:
    - **Mitigation**: Explicit BLOCKED handling and consumer-first scheduling
- **Priority inversion**:
    - **Mitigation**: Band-based ready queues; derive node band from highest-priority ready input
- **Complexity in subgraph expansion**:
    - **Mitigation**: `runtime_plan` helper with deterministic IDs and small surface area
- **Shutdown hangs**:
    - **Mitigation**: Shutdown timeout; policy-aware drain; robust stop ordering

## Out of Scope (Deferred)

- Async/await-native scheduler APIs (adapter can be added post-v1)
- Multi-process or distributed scheduling
- Advanced error policies (retries with jitter, DLQ routing) beyond placeholders
- Full observability (wired in M4)

## Traceability

- Implements Technical Blueprint Implementation Plan M3.
- Fulfills EARS requirements for lifecycle orchestration, priorities, backpressure cooperation, fairness, and graceful shutdown.

## Checklist

- [x] `scheduler.py`: run loop, readiness detection, lifecycle calls
- [x] Priority bands and fairness ratio implemented
- [x] Backpressure-aware emit routing
- [x] Shutdown semantics with reverse topo `on_stop`
- [x] Runtime mutators (priority, capacity) with validation
- [x] Unit/integration tests and coverage ≥90% for scheduler