# Meridian Runtime — A Minimal, Reusable Graph Runtime for Python

Owner: GhostWeasel (Lead: doubletap-dave)

[![CI](https://github.com/GhostWeaselLabs/meridian-runtime/actions/workflows/ci.yml/badge.svg)](https://github.com/GhostWeaselLabs/meridian-runtime/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-site-brightgreen)](https://ghostweasellabs.github.io/meridian-runtime-docs/)
[![Docs Deploy](https://github.com/GhostWeaselLabs/meridian-runtime/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/GhostWeaselLabs/meridian-runtime/actions/workflows/gh-pages.yml)

Meridian Runtime is a lightweight, framework-agnostic graph runtime for building real‑time dataflows in Python. Model your application as small, single‑responsibility nodes connected by typed edges with bounded queues. Meridian’s scheduler enforces backpressure, supports control‑plane priorities (e.g., kill switch), and emits rich observability signals by design.

Key features
- Nodes, edges, subgraphs, scheduler — simple, composable primitives
- Bounded edges with configurable overflow policies (block, drop, latest, coalesce)
- Control‑plane priority for critical flows (kill switch, admin, rate‑limit signals)
- First‑class observability (structured logs, metrics, trace hooks)
- Small‑file, SRP/DRY‑friendly codebase (aim for ~200 lines per file)
- uv‑native development workflow (fast, reproducible)

Use cases
- Real‑time trading systems (market data, execution, risk)
- Event processing pipelines and enrichment
- Streaming ETL and log processing
- Control planes with prioritized signals

---

## Versioning & Deprecation Policy

- This project follows Semantic Versioning starting with v1.0.0 for the public API.
- Public, stable surfaces are documented across Concepts and Reference in the docs site.
- Deprecations are announced in a MINOR release and remain available for at least one subsequent MINOR before removal.
- See:
  - Versioning and policy overview: https://ghostweasellabs.github.io/meridian-runtime-docs/roadmap/release-v1.0.0/
  - API Reference: https://ghostweasellabs.github.io/meridian-runtime-docs/reference/api/
  - Concepts (Architecture, Patterns): https://ghostweasellabs.github.io/meridian-runtime-docs/concepts/architecture/

## Documentation

- Site: https://ghostweasellabs.github.io/meridian-runtime-docs/ — Deployed via GitHub Pages (source: GitHub Actions)
- Quickstart: https://ghostweasellabs.github.io/meridian-runtime-docs/getting-started/quickstart/
- API: https://ghostweasellabs.github.io/meridian-runtime-docs/reference/api/
- Patterns: https://ghostweasellabs.github.io/meridian-runtime-docs/concepts/patterns/
- Observability: https://ghostweasellabs.github.io/meridian-runtime-docs/concepts/observability/
- Troubleshooting: https://ghostweasellabs.github.io/meridian-runtime-docs/support/troubleshooting/
- **Interactive Notebooks**: [`notebooks/`](./notebooks/) — Jupyter notebooks for hands-on learning and experimentation
- Note: Analytics is enabled for the docs site; see mkdocs.yml for the tracking configuration.




## Quick start

Prereqs
- Python 3.11+
- uv (modern Python package manager)

Initialize environment
```bash
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

3) Run an example
```
uv run python -m examples.hello_graph.main
```

4) Try interactive notebooks
```bash
# Install notebook dependencies
uv sync --extra notebooks

# Start Jupyter
uv run jupyter lab

# Navigate to notebooks/ directory and try:
# - tutorials/01-getting-started.ipynb
# - examples/hello-graph-interactive.ipynb
```

4) Project layout (M1 scaffold)
```
src/meridian/
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
```python
from meridian.core import Node, Message, MessageType, Port, PortDirection, PortSpec

class Producer(Node):
    def __init__(self, n=5):
        super().__init__(
            name="producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))]
        )
        self._n = n
        self._i = 0

    def on_start(self):
        self._i = 0

    def _handle_tick(self):
        if self._i < self._n:
            self.emit("out", Message(type=MessageType.DATA, payload=self._i))
            self._i += 1
```

consumer.py
```python
from meridian.core import Node, Port, PortDirection, PortSpec

class Consumer(Node):
    def __init__(self):
        super().__init__(
            name="consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[]
        )

    def _handle_message(self, port, msg):
        print(f"got: {msg.payload}")
```

main.py
```python
from meridian.core import Subgraph, Scheduler, SchedulerConfig
from producer import Producer
from consumer import Consumer

g = Subgraph(name="hello_world")
g.add_node(Producer(n=3))
g.add_node(Consumer())
g.connect(("producer", "out"), ("consumer", "in"), capacity=16)

sch = Scheduler(SchedulerConfig())
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
- Target ~200 lines per file. Split responsibilities into multiple nodes or utilities.
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
- Keep files small (~200 lines) and responsibilities focused.
- Include unit tests for core changes; add integration tests for subgraph behavior.
- Update examples and docs for user‑facing features.
- Follow SemVer and add entries to CHANGELOG for notable changes.

License
- BSD 3-Clause (recommended) or your organization’s standard OSS license.

---

## FAQ

See our [FAQ page](https://ghostweasellabs.github.io/meridian-runtime/support/faq/) for answers to common questions about Meridian Runtime.

---

Happy building with Meridian Runtime.
