# Frequently Asked Questions (FAQ)

This page consolidates common questions about Meridian Runtime, organized by topic.

---

## General Questions

### What is Meridian Runtime and what are its core components?

Meridian Runtime is a minimal, reusable, graph-based runtime for Python designed for building real-time, observable dataflows. It models applications as graphs of `Node`s connected by typed `Edge`s and composed into `Subgraph`s. The execution is coordinated by a `Scheduler`.

**Core components**:

- **Nodes**: Single-responsibility processing units that consume messages, perform work, and emit messages. They have lifecycle hooks (`on_start`, `on_message`, `on_tick`, `on_stop`) and handle errors locally.
- **Edges**: Typed, bounded queues connecting two nodes. They enforce message schemas, provide flow control, and apply overflow policies when capacity is reached. Edges are always bounded to prevent memory exhaustion.
- **Subgraphs**: Reusable compositions of nodes and edges that encapsulate a set of functionalities with defined inputs and outputs, allowing for modularity and reuse.
- **Scheduler**: The orchestrator of the runtime, responsible for dispatching ready work units, honoring priorities (e.g., control-plane over data-plane), managing concurrency and fairness, and facilitating graceful shutdown.
- **Messages**: Immutable containers carrying payloads and headers (e.g., `trace_id`, timestamp) across edges. They can be classified as `DATA`, `CONTROL`, or `ERROR` messages, influencing their routing and priority.
- **PortSpec**: Defines the name, schema/type, and overflow policy for a port, driving `Edge` typing and validation.

### Is a graph runtime overkill for my use case?

For simple, linear pipelines a small asyncio app may suffice. Meridian shines when you have multiple interacting flows, need backpressure and priorities, and value observability and reuse.

### Does Meridian require a specific web framework or broker?

No. It is framework‑agnostic and runs in‑process. Brokers/codecs become relevant in future distributed modes.

### Can I use Pydantic/Pyright/MyPy with Meridian?

Yes. Meridian encourages explicit typing and can integrate optional schema libraries. Choose what fits your project's standards.

### How do I handle long‑running or blocking work?

Prefer async IO; for CPU‑bound tasks, offload to thread/process pools and keep nodes responsive. Use backpressure to prevent overload.

---

## Architecture and Design

### How does Meridian Runtime ensure predictability and stability under load?

Meridian Runtime prioritizes predictability and stability through several key design principles and mechanisms:

- **Bounded Edges with Overflow Policies**: All edges have a fixed capacity. When an edge reaches capacity, a configured overflow policy (e.g., `block`, `drop`, `latest`, `coalesce`) is applied, preventing unbounded queue growth and memory exhaustion. The `block` policy applies backpressure upstream, signaling producers to slow down.
- **Cooperative Scheduler with Priorities and Fairness**: The scheduler dispatches work based on node readiness (messages or ticks) while maintaining fairness among runnable nodes to avoid starvation. It also supports priority bands (e.g., Control-plane > High > Normal), ensuring critical operations are processed first, even under heavy data-plane load.
- **Graceful Shutdown**: The system is designed to stop gracefully upon request, draining in-flight messages according to policies and invoking `on_stop` hooks on nodes in reverse topological order, ensuring resources are released cleanly.
- **Error Handling Policies**: If a node raises an exception in a lifecycle hook, the system captures and reports it via observability, applying the node's error policy (default: skip and continue) without crashing the entire scheduler.
- **Low-Overhead Observability**: While under sustained load, the system maintains bounded queue depths and an efficient idle strategy to avoid busy loops, ensuring that observability features (logs, metrics, tracing) have minimal overhead when enabled and are fast no-ops when off.

### How are applications structured and composed in Meridian Runtime?

Meridian Runtime promotes a modular and composable approach to application structuring, centered around `Node`s and `Subgraph`s:

- **Graph of Nodes and Edges**: Applications are modeled as directed graphs where individual `Node`s (single-responsibility processing units) are connected by typed, bounded `Edge`s.
- **Subgraph Composition**: `Subgraph`s are reusable composite units that encapsulate a set of nodes and edges with defined input and output ports. This allows for hierarchical composition, where smaller subgraphs can be nested into larger ones, promoting reusability and local reasoning about performance and failure modes.
- **Clear Boundaries**: Each component (`Node`, `Edge`, `Subgraph`, `Scheduler`) has a clear, narrow purpose, adhering to the Single Responsibility Principle (SRP). This design philosophy leads to smaller, more testable modules (guidance of ~200 LOC per file) and avoids hidden domain coupling.
- **Explicit Wiring and Validation**: Connections between nodes within a subgraph, and exposed ports of subgraphs, are explicitly defined. The system performs comprehensive validation during graph composition (e.g., unique names, port existence, schema compatibility, positive capacities, consistent policies) to ensure structural integrity and refuse to run invalid graphs.
- **Framework-Agnostic and In-Process**: The runtime is designed to be framework-agnostic and in-process, providing APIs that are friendly to asyncio usage without requiring it, enhancing its portability and ease of integration into existing Python applications.

### How does Meridian Runtime handle backpressure and overflow conditions on its edges?

Meridian Runtime's design fundamentally incorporates backpressure and explicit overflow policies on its bounded edges to ensure system stability and predictable behavior under varying loads:

- **Bounded Edges**: Every `Edge` has a defined, finite capacity. This is a critical design choice, as unbounded queues are explicitly not supported to prevent memory exhaustion.
- **Overflow Policies**: When an `Edge`'s capacity is reached, one of the following configurable overflow policies is applied:
  - **Block (Default)**: The system applies backpressure upstream, causing the producer node to yield or block until space becomes available in the queue. This ensures lossless delivery for critical data.
  - **Drop**: New messages are immediately discarded if the queue is full, and a drop metric is incremented. This is suitable for telemetry or low-importance streams where freshness is more critical than completeness.
  - **Latest**: Only the newest message is retained, discarding older messages beyond the capacity limit. This is useful for UI state updates or configuration changes where only the most recent value matters.
  - **Coalesce**: Incoming messages are combined with existing queued messages using a supplied, deterministic function. This policy is effective for aggregating or summarizing bursty data, preserving type correctness while compressing bursts (e.g., combining sensor readings into a single aggregate).
- **Cooperative Backpressure**: The `Scheduler` cooperates with these policies. If an output edge signals `BLOCKED`, the scheduler avoids busy-waiting and reschedules the producer, prioritizing consumers to make forward progress. This mechanism prevents deadlocks and ensures efficient resource utilization.
- **Metrics for Visibility**: Edges expose metrics such as `queue_depth`, `drops_total`, and `blocked_time_seconds`, providing crucial visibility into how backpressure and overflow policies are performing and where bottlenecks might occur.

---

## Observability

### What are the observability features in Meridian Runtime?

Meridian Runtime provides first-class, built-in observability through structured logging, metrics collection, and distributed tracing. These features are designed for low overhead and seamless integration with external monitoring systems.

- **Structured JSON Logs**: The system emits line-delimited JSON logs for lifecycle events, exceptions, and key actions. Logs include contextual fields like `ts`, `level`, `component`, `node`, `port`, `edge_id`, and `trace_id`, making them machine-readable and easy to aggregate. Debug-level logs are used for high-frequency events and can be disabled to minimize overhead.
- **Metrics Collection**: The system exposes a variety of metrics for different components:
  - **Nodes**: `messages_total`, `errors_total`, `tick_duration_seconds` (histogram).
  - **Edges**: `enqueued_total`, `dequeued_total`, `dropped_total`, `queue_depth` (gauge), `blocked_time_seconds` (counter/histogram).
  - **Scheduler**: `runnable_nodes` (gauge), `loop_latency_seconds` (histogram), `priority_applied_total` (counter labeled by band). Metrics follow Prometheus-compatible conventions and are accessible via an interface, with a no-op default and an optional Prometheus adapter.
- **Distributed Tracing**: When enabled, the system propagates correlation IDs (`trace_id`) across messages and creates spans at node and edge boundaries. This is achieved through `contextvars` integration and an optional OpenTelemetry-friendly adapter. Tracing is disabled by default to ensure zero overhead when not needed.
- **Privacy-Safe Diagnostics**: The system ensures that sensitive information (secrets, PII, payload contents) is scrubbed or omitted by default from logs and diagnostics bundles, providing hooks for log redaction at the application layer.

### How do I enable metrics and tracing?

Metrics are enabled by default with no-op implementation. To enable Prometheus metrics:

```python
from meridian.observability import configure_observability

configure_observability({
    "metrics": {"exporter": "prometheus"}
})
```

Tracing is disabled by default. Enable with:

```python
configure_observability({
    "tracing": {"enabled": True, "provider": "opentelemetry"}
})
```

### What metrics should I monitor?

Key metrics to watch:
- **Node metrics**: `meridian_node_messages_total`, `meridian_node_errors_total`, `meridian_node_tick_duration_seconds`
- **Edge metrics**: `meridian_edge_queue_depth`, `meridian_edge_dropped_total`, `meridian_edge_blocked_time_seconds_total`
- **Scheduler metrics**: `meridian_scheduler_runnable_nodes`, `meridian_scheduler_loop_latency_seconds`

### How do I handle high-throughput scenarios?

1. Use appropriate edge capacities and policies
2. Monitor for backpressure and adjust accordingly
3. Consider using `Latest` or `Coalesce` policies for burst handling
4. Profile node processing times and optimize bottlenecks

---

## Development and Contributing

### What development and operational tooling does Meridian Runtime provide?

Meridian Runtime offers a robust set of tooling and practices to ensure a smooth developer experience, high quality, and predictable operations:

- **Reproducible Development Workflow**: The system supports a `uv`-native workflow (`uv init`, `uv lock`, `uv sync`, `uv run` / `uvx`) for consistent and reproducible development, testing, and examples across environments.
- **Scaffolding Commands**: CLI commands are provided to generate `Node` and `Subgraph` skeletons, including class structure, explicit typing, docstrings, and basic unit/integration tests, accelerating consistent and convention-adhering development.
- **Automated Quality Gates**: Continuous Integration (CI) enforces high quality standards by running linting (`ruff`), formatting (`black`), static type analysis (`mypy`), and automated tests (`pytest`) with strict coverage thresholds (≥90% for core, ≥80% overall). These checks are mandatory for merging code.
- **Semantic Versioning and Release Process**: The project adheres to Semantic Versioning for its public API, publishing artifacts to package registries (e.g., PyPI) with signed distributions. A formal deprecation policy ensures API stability and provides clear migration guidance for users.
- **Comprehensive Documentation**: All aspects of the runtime, from installation and core concepts to API references, common patterns, troubleshooting guides, and observability configuration, are thoroughly documented. Examples are runnable, modular, and demonstrate best practices, aiding in faster adoption and understanding.
- **Diagnostics and Troubleshooting**: The CLI supports gathering anonymized runtime metadata, environment info, and logs into a diagnostics bundle to assist in troubleshooting issues, with built-in redaction rules for sensitive data.

### Why keep milestone files in Git?

It ensures plans are versioned with code, discussed via PRs, and discoverable close to implementation.

### How do milestones relate to issues/PRs?

Each milestone should link to a tracking issue or project board; individual items are implemented via issues/PRs that reference the milestone.

### What's the file size guidance for contributions?

Keep files small (~200 LOC) and responsibilities focused. Include unit tests for core changes; add integration tests for subgraph behavior.

### How does Meridian Runtime prioritize quality and maintainability?

Meridian Runtime is built with a strong emphasis on quality and maintainability, driven by clear principles and continuous integration practices:

- **Single Responsibility Principle (SRP) and DRY**: Components are designed with a clear, narrow purpose, and the codebase adheres to SRP and "Don't Repeat Yourself" (DRY) principles, with a guidance of keeping files small (~200 LOC per file).
- **Async-Friendly and Framework-Agnostic**: Implemented in Python 3.11+, the system is designed to be asyncio-friendly without imposing asyncio requirements, enhancing its adaptability and reducing coupling. It avoids global mutable state, preferring explicit dependency injection.
- **Comprehensive Testing**: The project maintains high code coverage (≥90% for core modules, ≥80% overall), enforced by CI gates. This includes extensive unit tests for core primitives, integration tests for end-to-end scenarios (e.g., backpressure propagation, control-plane priority, graceful shutdown), and plans for stress and soak tests to validate performance and detect resource leaks under load.
- **Static Analysis and Linting**: CI checks enforce code quality through linting (`ruff`), formatting (`black`), and static type analysis (`mypy`) to ensure consistency and catch errors early.
- **Structured Logging and Error Handling**: The system emits structured JSON logs for all key events and errors, ensuring consistent, machine-readable output. Error messages are meaningful, provide contextual metadata, and omit sensitive payloads by default. Node exceptions are captured and handled gracefully without crashing the scheduler.
- **Docs-as-Product**: Documentation is treated as a first-class product artifact. It includes comprehensive guides, API references, common patterns, troubleshooting steps, and runnable examples. Documentation quality is also verified in CI for correct rendering, valid links, and code snippet execution.
- **Semantic Versioning and API Stability**: Public APIs are clearly defined and follow Semantic Versioning, with documented deprecation policies and migration notes to ensure backward compatibility and predictable evolution for users.
- **Performance Principles**: Hot paths are designed to be allocation-light, with pre-bound metric label handles and internal integer IDs to optimize performance. Performance budgets and CI regression checks are planned to prevent slowdowns.

---

## Issue Reporting and Support

### Can I share payload data if it seems harmless?

**No.** Share schemas or field names only. Keep values redacted.

### I can't create a minimal repro. What should I do?

Provide the smallest set of sanitized logs, graph configuration details (edge bounds/policies), and environment info you can. Maintainers may suggest a narrowed test based on your description.

### What if the issue is security‑sensitive?

Use a private reporting channel if available. Do not share details publicly. Briefly describe impact and request a secure handoff.

### Will maintainers sign NDAs?

The project is designed to avoid the need for sensitive data. We strongly prefer anonymized, redacted artifacts.

---

## Roadmap and Planning

### What is the post-v1 roadmap for Meridian Runtime?

The post-v1 roadmap for Meridian Runtime outlines high-value initiatives beyond the initial 1.0.0 release, guided by themes such as composability, predictable performance, operational transparency, developer ergonomics, and incremental feature delivery. It is organized into near-term (v1.x), mid-term (v2.x), and long-term (v3.x+) horizons:

**Horizon 1: Near-Term (v1.x series)** focuses on enhancing developer experience and performance optimizations:

- **CLI Enhancements**: Diagnostics collection with redaction, graph validation, linting, quick profiling, and topology export.
- **Rust Fast Path Extensions**: Optional `meridian_fast` extension for performance-critical components (e.g., bounded ring buffers for edges, scheduler primitives) via PyO3, with graceful fallback to pure Python.
- **CPU Topology Awareness**: Optional CPU affinity setting for process pinning on Linux.
- **Deterministic Metrics Overhead Minimization**: Ensuring metrics have zero overhead when disabled and batch increments for efficiency.
- **Graph Inspector (TUI)**: A terminal user interface for runtime introspection.
- **Schema and Validation Ergonomics**: Improved optional validators (e.g., Pydantic) and structured error mapping.
- **Scheduler Profiling and Fairness Tuning**: Recording scheduling latencies and supporting configurable fairness strategies.
- **Persistence-Friendly Hooks**: Extension points for durable inbox/outbox adapters.

**Horizon 2: Mid-Term (v2.x series)** introduces more advanced capabilities and tools:

- **Visual Graph Inspector**: An optional web or local visualizer for graph topology and metrics.
- **Pluggable Storage for Edges**: Allowing edge queues to use various storage backends (memory, mmap, local DB).
- **Extended Backpressure Strategies**: Advanced configurations like watermarks and adaptive coalescing.
- **Graph Versioning and Migration Aids**: Strategies for upgrading graph definitions.
- **Replay and Time-Travel Debugging**: Opt-in local replay from persisted event logs.
- **Policy-Driven Error Handling**: Configurable error policies like retry with backoff or circuit breakers.
- **Structured Configuration Layer**: Loading configuration from files (TOML/YAML) with strict validation.

**Horizon 3: Long-Term (v3.x+)** explores distributed execution and advanced system-level features:

- **Multi-Process/Distributed Execution**: Support for partitioned execution across processes or hosts, likely leveraging Rust bridges for shared memory or lock-free queues.
- **Adaptive Scheduling and QoS**: Scheduler adapting priorities based on QoS classes and queue depth.
- **Formal Verification Aids**: Optional formal models for critical components.
- **Pluggable Security Posture**: Policy modules for encryption, signed configurations, and policy-as-code redaction.
- **Remote Control Plane**: Secure remote operations (pause/resume nodes, swap subgraphs).

Cross-cutting concerns like observability, privacy/redaction, performance, and API stability will continue to be prioritized throughout all horizons.

### How do I propose changes to the roadmap?

For small edits to existing milestones, make a PR that clearly states the change and links to evidence when changing scope or risk.

For new milestones:
1. Copy the template from the roadmap into a new `Mx-title.md` file
2. Open a PR and request review from maintainers

### Can milestone numbers be reordered?

Avoid churn. If order must change, prefer updating dependencies and "Order of operations" instead of renaming files. If a rename is necessary, include redirect notes in docs and update references across the repo.

---

## Troubleshooting

### My graph isn't processing messages. What should I check?

1. Verify all nodes are properly connected with valid port types
2. Check that the scheduler is running (`scheduler.run()`)
3. Ensure nodes are emitting messages to their output ports
4. Look for validation errors in the logs

### How do I debug backpressure issues?

1. Check edge capacities and policies
2. Monitor queue depth metrics
3. Look for `BLOCKED` or `DROP` events in logs
4. Verify consumer nodes are processing messages at expected rates

### Why are my messages being dropped?

This could be due to:
- Edge capacity limits with `Drop` or `Latest` policies
- Type validation failures at edge boundaries
- Consumer nodes not processing messages fast enough

Check the edge policy configuration and monitor drop counters in metrics.

---

## Migration and Upgrades

### How do I upgrade between versions?

1. Check the `CHANGELOG` for breaking changes
2. Update your dependency version
3. Run your test suite
4. Review any deprecation warnings
5. Update code if needed based on breaking changes

### What's the deprecation policy?

- Deprecated APIs are marked with warnings and docstrings
- Minimum deprecation window: one `MINOR` release before removal
- Deprecations are documented in `CHANGELOG` and API docs

---

## Still Have Questions?

- Check the [troubleshooting guide](./troubleshooting.md) for common issues
- Review the [API documentation](../reference/api.md) for detailed usage
- Search [existing issues](https://github.com/your-org/meridian-runtime/issues) for similar questions
- Open a new issue if your question isn't covered here
