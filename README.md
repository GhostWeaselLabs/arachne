# Arachne — A Minimal, Reusable Graph Runtime for Python

Owner: GhostWeasel (Lead: doubletap-dave)

Arachne is a lightweight, framework-agnostic graph runtime for building real‑time dataflows in Python. Model your application as small, single‑responsibility nodes connected by typed edges with bounded queues. Arachne’s scheduler enforces backpressure, supports control‑plane priorities (e.g., kill switch), and emits rich observability signals by design.

Key features
- Nodes, edges, subgraphs, scheduler — simple, composable primitives
- Bounded edges with configurable overflow policies (block, drop, latest, coalesce)
- Control‑plane priority for critical flows (kill switch, admin, rate‑limit signals)
- First‑class observability (structured logs, metrics, trace hooks)
- Small‑file, SRP/DRY‑friendly codebase (aim for ~200 LOC per file)
- uv‑native development workflow (fast, reproducible)

Use cases
- Real‑time trading systems (market data, execution, risk)
- Event processing pipelines and enrichment
- Streaming ETL and log processing
- Control planes with prioritized signals

---

## Documentation Map

- Governance and Overview (M0): docs/plan/M0-governance-and-overview.md
- Post‑v1 Roadmap: docs/plan/99-post-v1-roadmap.md
- Contributing Guide: docs/contributing/CONTRIBUTING.md
- Releasing Guide: docs/contributing/RELEASING.md
- How to Report Issues: docs/support/HOW-TO-REPORT-ISSUES.md
- Troubleshooting: docs/support/TROUBLESHOOTING.md
- Issue Templates:
  - General: docs/support/templates/ISSUE_TEMPLATE.md
  - Bug Report: docs/support/templates/BUG_REPORT.md
  - Feature Request: docs/support/templates/FEATURE_REQUEST.md

## Quickstart

Prereqs
- Python 3.11+
- uv (modern Python package manager)

1) Initialize environment
```
uv lock
uv sync
```

2) Dev loop
```
# Lint
uv run ruff check .

# Format check
uv run black --check .

# Type-check
uv run mypy src

# Tests with coverage
uv run pytest
```

3) Run an example (placeholder)
```
# Examples will be added in later milestones; the package scaffolding is present.
# For now, integration tests include a minimal smoke scenario.
```

4) Project layout (M1 scaffold)
```
src/arachne/
  __init__.py
  core/
    __init__.py
  observability/
    __init__.py
  utils/
    __init__.py
examples/
  __init__.py
tests/
  unit/
    test_smoke.py
  integration/
    test_examples_smoke.py
pyproject.toml
ruff.toml
mypy.ini
.editorconfig
.github/workflows/ci.yml
```

---

## Core Concepts

Node
- Single‑responsibility processing unit with typed input/output ports
- Lifecycle hooks: on_start, on_message, on_tick, on_stop
- Emits Messages on output ports

Edge
- Typed, bounded queue connecting node ports
- Overflow policies: block (default), drop, latest, coalesce(fn)
- Exposes queue depth, throughput, and backpressure metrics

Subgraph
- Composition of nodes into a reusable unit
- Exposes its own typed inputs/outputs
- Validates internal wiring and contracts

Scheduler
- Advances nodes based on readiness, priorities, and capacity
- Drives ticks (timers/housekeeping), supports graceful shutdown
- Prioritizes control‑plane edges/messages

Message
- payload: Any (type tracked by PortSpec)
- headers: {trace_id, timestamp, schema_version, content_type, ...}

PortSpec
- name: str
- schema/type: Python types, TypedDict, or Pydantic models (pluggable)
- policy: overflow handling per edge (block/drop/latest/coalesce)

Observability
- Structured logs (JSON) with correlation IDs
- Metrics (Prometheus) for nodes/edges/scheduler
- Optional tracing (OpenTelemetry hooks)

---

## Minimal Example

producer.py
```
from arachne.core import Node, Message

class Producer(Node):
    def __init__(self, n=5):
        self._n = n
        self._i = 0

    def name(self): return "producer"
    def inputs(self): return {}
    def outputs(self): return {"out": int}

    def on_start(self):
        self._i = 0

    def on_tick(self):
        if self._i < self._n:
            self.emit("out", Message(payload=self._i))
            self._i += 1
```

consumer.py
```
from arachne.core import Node

class Consumer(Node):
    def name(self): return "consumer"
    def inputs(self): return {"in": int}
    def outputs(self): return {}

    def on_message(self, port, msg):
        print(f"got: {msg.payload}")
```

main.py
```
from arachne.core import Subgraph, Scheduler
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

Run:
```
uv run python -m examples.hello_graph.main
```

---

## Patterns and Guidance

File size and modularity
- Target ~200 LOC per file. Split responsibilities into multiple nodes or utilities.
- SRP and DRY: nodes do one thing; share common helpers in utils/.
- Prefer small subgraphs over monolith graphs for composition and reuse.

Backpressure and overflow
- Default policy: block (applies backpressure upstream).
- For sporadic spikes: latest policy can drop stale data in favor of the newest.
- For aggregations: coalesce can compress bursts (e.g., merge updates).

Priorities
- Assign higher priority to control‑plane edges (e.g., kill switch, cancel_all).
- Keep control messages small and fast; avoid heavy work in control nodes.

Message schemas
- Use precise Python types or TypedDicts for ports.
- Optionally integrate Pydantic for richer validation without coupling the runtime.

Error handling
- Prefer local handling in nodes; escalate via dead‑letter subgraph if needed.
- Use retries with jitter and circuit‑breaker patterns for external IO nodes.

---

## Observability

Logs
- JSON‑structured logs with timestamps and correlation IDs (trace_id)
- Node lifecycle events, exceptions, tick durations

Metrics (Prometheus)
- Node: tick latency, messages processed, errors
- Edge: queue depth, enqueue/dequeue rate, drops, backpressure time
- Scheduler: runnable nodes, loop latency, priority applications

Tracing (optional)
- Hook into OpenTelemetry: annotate message paths and node spans
- Keep tracing optional to avoid overhead where unnecessary

Dashboards and alerts
- Track queue depths and backpressure saturation
- Alert on sustained scheduler latency or starved nodes
- Monitor error rates per node and dropped messages per edge

---

## Roadmap

v1 (initial release)
- In‑process runtime, asyncio‑friendly
- Nodes, edges (bounded queues), subgraphs, scheduler (fair scheduling)
- Observability: logs, metrics, basic trace hooks
- Examples and scaffolding scripts

v1.x
- Schema adapters (Pydantic), richer overflow policies
- More node templates and utilities
- Improved testing harness and fixtures

v2+
- Multi‑process edges (shared memory/IPC)
- Distributed graphs (brokers + codecs)
- Visual tooling and hot‑reload for graphs

---

## Development (with uv)

Install and sync
```
uv init
uv lock
uv sync
```

Run tests
```
uv run pytest
```

Lint and type‑check (example)
```
uv run ruff check .
uv run mypy src
```

Run an example
```
uv run python -m examples.hello_graph.main
```

Contributing
- Keep files small (~200 LOC) and responsibilities focused.
- Include unit tests for core changes; add integration tests for subgraph behavior.
- Update examples and docs for user‑facing features.
- Follow SemVer and add entries to CHANGELOG for notable changes.

License
- BSD 3-Clause (recommended) or your organization’s standard OSS license.

---

## FAQ

Is a graph runtime overkill?
- For simple, linear pipelines a small asyncio app may suffice. Arachne shines when you have multiple interacting flows, need backpressure and priorities, and value observability and reuse.

Does Arachne require a specific web framework or broker?
- No. It is framework‑agnostic and runs in‑process. Brokers/codecs become relevant in future distributed modes.

Can I use Pydantic/Pyright/MyPy with Arachne?
- Yes. Arachne encourages explicit typing and can integrate optional schema libraries. Choose what fits your project’s standards.

How do I handle long‑running or blocking work?
- Prefer async IO; for CPU‑bound tasks, offload to thread/process pools and keep nodes responsive. Use backpressure to prevent overload.

---

Happy weaving with Arachne.
