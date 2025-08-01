# Graph Runtime: Extraction Plan and Technical Blueprint

This report outlines the rationale, architecture, API design, implementation plan, testing strategy, and operational guidelines for extracting the Graph Runtime into a standalone, reusable project suitable for future systems beyond Kraken.

## Executive Summary

We will extract the Graph Runtime (GR) into an independent project that provides a lightweight, framework-agnostic dataflow engine. The GR models applications as graphs of small, single-responsibility nodes connected by typed edges, executed by a scheduler with built-in backpressure and observability. It enforces SRP/DRY, encourages files of ~200 LOC, and integrates cleanly with `uv` for package management.

Key outcomes:
- Reusable runtime usable by any project (trading systems, ETL, realtime analytics).
- Deterministic, typed message-passing between nodes/subgraphs with bounded queues.
- Clean separation from exchange-specific logic; Kraken system becomes a client of GR.
- Comprehensive test harness for node/subgraph/graph levels.

---

## Goals and Non-Goals

Goals
- Provide a minimal, composable Graph Runtime with a clear, documented API.
- Support push/pull/hybrid scheduling, bounded edges (backpressure), and control-plane priority.
- Offer first-class observability hooks (logs, metrics, traces).
- Keep code modular and small (~200 LOC per file), DRY, SRP-compliant.
- Deliver scaffold tooling to generate new nodes/subgraphs consistently.
- Integrate `uv` for reproducible dev and CI workflows.

Non-Goals
- Domain-specific nodes (e.g., Kraken API clients) — those live in downstream projects.
- Full-blown stream processing DSL or query engine (focus on a pragmatic runtime).
- Distributed runtime for v1 (single-process, multi-thread/async friendly, with a roadmap for distributed later).

---

## High-Level Architecture

Core components
- Node: Single-responsibility unit with typed input/output ports.
- Edge: Bounded queue connecting node ports; enforces backpressure.
- Subgraph: Composition of nodes into a logical unit with exposed inputs/outputs.
- Scheduler: Advances nodes based on readiness, capacity, and priorities.
- Message: Versioned, typed payload with optional headers/metadata.
- Observability: Metrics, structured logs, trace correlation IDs at node/edge/graph boundaries.

Conceptual diagram (text)
- Graph
  - Subgraph(s)
    - Node A -> Edge (bounded) -> Node B -> ...
  - Control edges (priority) for kill switch, rate-limit signals, admin commands
- Scheduler orchestrates node lifecycle: on_start, on_message, on_tick, on_stop

---

## API Design (Draft)

Interfaces (Python-style pseudocode)

Node
- name() -> str
- inputs() -> dict[str, PortSpec]
- outputs() -> dict[str, PortSpec]
- on_start() -> None
- on_message(port: str, msg: Message) -> None
- on_tick() -> None
- on_stop() -> None

Subgraph
- add_node(node: Node) -> None
- connect(src: (node, port), dst: (node, port), capacity: int = 1024) -> None
- expose_input(name: str, target: (node, port)) -> None
- expose_output(name: str, source: (node, port)) -> None
- validate() -> list[Issue]

Scheduler
- register(unit: Node | Subgraph) -> None
- run() -> None
- shutdown() -> None
- set_priority(edge_id: str, priority: int) -> None
- set_capacity(edge_id: str, capacity: int) -> None

Message
- headers: dict[str, Any] (trace_id, ts, schema_ver, content_type)
- payload: Any (type enforced by PortSpec)

PortSpec
- name: str
- schema: type | TypedDict | Pydantic model (pluggable)
- policy: {drop, block, latest, coalesce(fn)} on overflow
- codec: serializer/deserializer plugin if crossing process boundary (future)

Policies and behaviors
- Backpressure: default blocking on bounded queues; overflow policy configurable per edge.
- Priorities: control-plane edges prioritized (kill switch, admin signals).
- Ticks: periodic on_tick for timers/housekeeping; configurable cadence.
- Error handling: per-node error policy (retry, skip, dead-letter queue).

---

## Observability

Events
- Node lifecycle: start/stop, exceptions, tick durations.
- Edge metrics: queue depth, enqueue/dequeue rates, drops, backpressure time.
- Scheduler metrics: loop latency, runnable nodes, starvation, priorities applied.
- Message tracing: correlation IDs across edges/nodes.

Export
- Structured logs (JSON) with timestamps and correlation IDs.
- Metrics exporters (e.g., Prometheus) with a narrow, well-defined namespace.
- Optional tracing hooks (OpenTelemetry) behind a simple interface.

---

## Project Layout and Conventions

Repository structure (suggested)
- graph-runtime/
  - src/graph_runtime/
    - core/
      - node.py
      - subgraph.py
      - edge.py
      - scheduler.py
      - message.py
      - ports.py
      - policies.py
    - observability/
      - logging.py
      - metrics.py
      - tracing.py
    - utils/
      - time.py
      - ids.py
      - validation.py
    - scaffolding/
      - generate_node.py
      - generate_subgraph.py
  - tests/
    - unit/
    - integration/
  - examples/
    - hello_graph/
    - pipeline_demo/
  - pyproject.toml (uv-managed)
  - README.md
  - CHANGELOG.md
  - LICENSE

Conventions
- ~200 LOC per file target; split by concern and compose via subpackages.
- SRP and DRY: one responsibility per file; shared helpers in utils.
- Explicit typing for public APIs; minimal runtime reflection/magic.
- Markdown docs with runnable examples in examples/.

---

## Implementation Plan (Milestones)

M1: Project bootstrap with uv
- Initialize repo, license, CODEOWNERS.
- uv init, pin Python version, uv lock, uv sync.
- CI: lint (ruff), type-check (mypy/pyright), tests (pytest), coverage.

M2: Core primitives
- Message, PortSpec, policies (backpressure, overflow).
- Edge (bounded queue, metrics).
- Node base class (lifecycle, error policy).
- Subgraph (composition, validation).

M3: Scheduler
- Runnable queue, fairness policy, priorities.
- on_message/on_tick orchestration; cadence control.
- Shutdown semantics and graceful stop.

M4: Observability
- Structured logging facade.
- Metrics interface + default Prometheus exporter.
- Trace correlation IDs pluggable via contextvars.

M5: Utilities and scaffolding
- Node/Subgraph generators (templates).
- Validation helpers and schema adapters (pydantic optional).

M6: Examples and documentation
- Hello graph (single producer/consumer).
- Data pipeline demo (validator -> transformer -> sink with backpressure).
- Docs site pages: quickstart, API reference, patterns, troubleshooting.

M7: Testing and hardening
- Unit tests: core classes, policies, edge semantics.
- Integration tests: subgraph composition, scheduler behavior, backpressure.
- Stress tests: high-throughput edges, starvation avoidance, priority paths.
- Coverage targets (≥90% core/ ≥80% overall).

M8: Release v1.0.0
- Tag, changelog, versioning policy (SemVer).
- Artifact publishing (e.g., PyPI).
- Announce and integrate with Kraken project as an external dependency.

---

## Testing Strategy

Unit tests
- Node lifecycle: start/stop, error handling.
- Edge behavior: capacity, overflow policies, queue depth metrics.
- Message typing and schema validation.
- Scheduler: fairness, priority ordering, tick cadence.

Integration tests
- Subgraph composition and edge validation.
- Backpressure propagation end-to-end.
- Control-plane priority (kill switch vs. normal flow).
- Observability: metrics and logs emitted under load.

Stress and reliability
- Throughput benchmarks and latency histograms.
- Long-running stability (hours) without memory growth.
- Fault injection: node exceptions, slow consumers, overflow policies.

Security and compliance
- No secret handling in runtime (test that configuration is externalized).
- Log redaction hooks for user payloads (opt-in).

---

## Compatibility and Extensibility

Language/runtime
- Python-first; aim for Python 3.11+ with asyncio-friendly APIs.
- Design for future multi-process/distributed extensions (edge codecs, IPC).

Schema adapters
- Pluggable schema layer: support stdlib typing, TypedDict, Pydantic (optional).

Scheduling strategies
- Start with cooperative scheduler; allow plugin for alternate strategies.

Roadmap (post v1)
- Multi-process edges (shared memory/IPC).
- Distributed graphs (brokered edges with codecs).
- Visual graph tooling and hot-reload for node graphs.

---

## Operational Guidance

Package management
- Use `uv`:
  - uv init
  - uv lock
  - uv sync
  - uv run pytest
- Pin Python and dependency versions in pyproject.
- Provide a constraints file if needed for downstream reproducibility.

Versioning and releases
- Semantic Versioning.
- CHANGELOG per release.
- Deprecation policy with transition notes for API changes.

Observability defaults
- Emit metrics and logs by default with sane labels.
- Allow disabling or customizing exporters.

---

## Risks and Mitigations

- Risk: Overengineering the runtime.
  - Mitigation: Keep v1 minimal (single-process, bounded edges, simple scheduler).
- Risk: Hidden coupling to Kraken domain.
  - Mitigation: Strict separation; no Kraken types in GR; examples remain neutral.
- Risk: Performance regressions under load.
  - Mitigation: Benchmarks in CI; profiling before releases; capacity planning guidance.
- Risk: API instability early on.
  - Mitigation: Clear v0.x pre-release policy; stabilize core before 1.0.

---

## Acceptance Criteria

- A standalone repository with documented, versioned Graph Runtime.
- Public APIs for Node, Edge, Subgraph, Scheduler, Message, and Observability.
- Examples and tutorials that run with `uv run`.
- ≥90% coverage for core modules, CI passing, and SemVer releases.
- Kraken project updated to depend on the Graph Runtime as an external package.

---

## Appendix: Example Node (Pseudo-Implementation)

```python
# src/graph_runtime/examples/hello_graph/producer.py
from graph_runtime.core import Node, Message

class Producer(Node):
    def __init__(self, n=10):
        self._n = n
        self._i = 0

    def name(self) -> str:
        return "producer"

    def inputs(self) -> dict[str, None]:
        return {}

    def outputs(self) -> dict[str, str]:
        return {"out": "int"}

    def on_start(self) -> None:
        self._i = 0

    def on_tick(self) -> None:
        if self._i < self._n:
            self.emit("out", Message(payload=self._i))
            self._i += 1
```

```python
# src/graph_runtime/examples/hello_graph/consumer.py
from graph_runtime.core import Node

class Consumer(Node):
    def name(self) -> str:
        return "consumer"

    def inputs(self) -> dict[str, str]:
        return {"in": "int"}

    def outputs(self) -> dict[str, None]:
        return {}

    def on_message(self, port: str, msg):
        print(f"got: {msg.payload}")
```

```python
# src/graph_runtime/examples/hello_graph/main.py
from graph_runtime.core import Subgraph, Scheduler
from producer import Producer
from consumer import Consumer

g = Subgraph()
g.add_node(Producer(n=3))
g.add_node(Consumer())
g.connect(("producer", "out"), ("consumer", "in"), capacity=16)

sch = Scheduler()
sch.register(g)
sch.run()
```

---