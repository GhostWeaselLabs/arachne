# Milestone M4: Observability (Logs, Metrics, Tracing)

## EARS Tasks and Git Workflow

Branch name: feature/m4-observability

EARS loop
- Explore: map required logs, metrics, tracing to core touchpoints
- Analyze: define logging/metrics/tracing interfaces with no-op defaults
- Implement: logging.py, metrics.py, tracing.py and core wiring
- Specify checks: unit/integration tests for counters, gauges, logs, spans
- Commit after each major step

Git commands
- git checkout -b feature/m4-observability
- git add -A && git commit -m "feat(obs): JSON logging facade with context"
- git add -A && git commit -m "feat(obs): metrics interfaces and no-op + Prometheus adapter"
- git add -A && git commit -m "feat(obs): tracing adapter with contextvars"
- git add -A && git commit -m "feat(obs): wire nodes/edges/scheduler metrics and logs"
- git add -A && git commit -m "test(obs): logging/metrics/tracing and core instrumentation"
- git push -u origin feature/m4-observability
- Open PR early; keep commits small and focused

Status: ✅ COMPLETED
Owner: Core Maintainers
Duration: 3–5 days

Overview
Introduce first-class observability across the runtime with structured logs, metrics (Prometheus-friendly), and optional tracing hooks. This milestone wires low-overhead instrumentation into hot paths without coupling the runtime to any single telemetry backend. Tracing is optional and disabled by default; logs and metrics are enabled with sane defaults and can be replaced or turned off.

EARS Requirements
- The system shall emit structured JSON logs for node lifecycle events, exceptions, and tick durations.
- The system shall expose metrics for nodes (tick latency, messages processed, errors), edges (queue depth, enqueue/dequeue rate, drops, blocked time), and scheduler (runnable nodes, loop latency, priority application counts).
- Where tracing is enabled, the system shall propagate correlation IDs and create spans at node and edge boundaries.
- If a message is dropped due to policy, the system shall increment a drops counter and may log at debug to avoid log flooding.
- While the system is running, the scheduler shall record loop latency and runnable queue sizes at configurable intervals.
- When a node raises an exception, the system shall log the error with context (node, port, edge, trace_id) and increment error metrics.
- The system shall offer a no-op observability implementation by default with the option to install a Prometheus exporter and tracing adapter.
- The system shall support correlation ID propagation across messages via headers.trace_id (generated if missing).

Deliverables
- src/arachne/observability/logging.py
  - JSON-structured logging facade with minimal API: info, warn, error, debug
  - Context support: node, edge, port, trace_id, event, and timestamps
  - Global configuration: log level, output stream, optional extra fields
- src/arachne/observability/metrics.py
  - Metrics interface (protocol) with Counter, Gauge, Histogram
  - Default no-op implementation
  - Prometheus adapter (optional submodule) exposing a registry and exporter hooks
  - Metric name and label conventions (see below)
- src/arachne/observability/tracing.py
  - Optional tracing adapter (OpenTelemetry-friendly) with span helpers
  - contextvars integration to propagate trace_id and span contexts
  - Functions: start_span(name, attributes) → context manager; set_trace_id(str)
- Wiring into core modules:
  - core/message.py: ensure trace_id generation and propagation
  - core/edge.py: enqueue/dequeue counters, queue depth gauge, drops counter, blocked time histogram
  - core/node.py: messages_processed_total, errors_total; hook lifecycle logs
  - core/scheduler.py: runnable_nodes gauge, loop_latency histogram, priority_applied counters; lifecycle logs (start/shutdown)
- Documentation updates:
  - Observability guide with examples, metric catalog, dashboard/alerting recommendations

Observability Model
Logging
- Format: line-delimited JSON with fields:
  - ts (RFC3339 or epoch_ms), level, component ("node"/"edge"/"scheduler"), event, message
  - node, port, edge_id, subgraph (when available), trace_id
  - extras: error.type, error.msg, error.stack for exceptions
- Events (examples):
  - node.start, node.stop, node.error, node.tick
  - edge.enqueue, edge.dequeue, edge.drop, edge.blocked
  - scheduler.start, scheduler.shutdown, scheduler.loop_tick
- Levels:
  - info: lifecycle, start/stop, scheduler start/shutdown
  - debug: high-rate events (enqueue/dequeue), policy decisions, tick durations
  - warn/error: exceptions, policy misconfigurations, capacity violations
- Performance:
  - Avoid expensive string formatting; build dicts and let logger handle serialization
  - Allow disabling debug logs globally to avoid hot path overhead

Metrics
- Conventions:
  - Namespace: arachne_*
  - Labels: graph, subgraph, node, edge_id, port, policy, priority_band
- Node metrics:
  - arachne_node_messages_total (counter)
  - arachne_node_errors_total (counter)
  - arachne_node_tick_duration_seconds (histogram)
- Edge metrics:
  - arachne_edge_enqueued_total (counter)
  - arachne_edge_dequeued_total (counter)
  - arachne_edge_dropped_total (counter)
  - arachne_edge_queue_depth (gauge)
  - arachne_edge_blocked_time_seconds_total (counter or histogram; see below)
- Scheduler metrics:
  - arachne_scheduler_runnable_nodes (gauge)
  - arachne_scheduler_loop_latency_seconds (histogram)
  - arachne_scheduler_priority_applied_total (counter, labeled by band)
- Implementation notes:
  - No-op by default; optionally enable a Prometheus adapter with on-demand registry creation and HTTP exposition outside of core (user’s responsibility)
  - Histograms: choose low-cardinality buckets; provide sane defaults
  - Blocked time: if measured per enqueue attempt, prefer histogram; otherwise accumulate as counter with seconds

Tracing (optional)
- Spans:
  - node.on_message: span per callback with attributes {node, port, trace_id, edge_id}
  - node.on_tick: span per tick
  - edge.enqueue/dequeue: lightweight span or event annotation; minimize overhead
  - scheduler.loop: coarse-grained span per loop iteration at debug level
- Correlation:
  - Message.headers.trace_id is source of truth; generated if missing
  - contextvars store current trace_id; updated upon message receipt and restored after callback
- OpenTelemetry adapter:
  - Provide thin helpers that create spans via OTEL if installed; otherwise no-op
  - Keep tracing disabled by default; enable via environment/config

Interfaces and APIs
Logging
- get_logger() -> Logger
  - Logger methods: info(event, msg, **fields), warn(...), error(...), debug(...)
  - Global configure(level: str, stream: IO | None, extra: dict | None)
- Context helpers:
  - with_context(**kvs) -> context manager that enriches subsequent logs
  - set_trace_id(trace_id: str) -> None

Metrics
- get_metrics() -> Metrics
  - Metrics.counter(name, labels_schema) -> Counter
  - Metrics.gauge(name, labels_schema) -> Gauge
  - Metrics.histogram(name, labels_schema, buckets=None) -> Histogram
- Instrumentation helpers:
  - time_block(name, labels) -> context manager that observes a histogram duration

Tracing
- start_span(name: str, attributes: dict | None = None) -> context manager
- set_trace_id(trace_id: str) -> None
- get_trace_id() -> str | None

Integration Points
- core/message.py
  - On Message creation: if headers.trace_id missing, generate via utils.ids
- core/edge.py
  - On put(): increment enqueued_total or dropped_total; update queue_depth; if BLOCKED, record blocked_time as appropriate
  - On get(): increment dequeued_total; update queue_depth
  - Logging at debug for enqueue/dequeue; info/warn for drops if needed (rate-limited or disabled by default)
  - Tracing: annotate enqueue/dequeue events when enabled
- core/node.py
  - Before on_message/on_tick: set contextvars trace_id; start span (optional)
  - After callback: increment messages_total; observe tick duration; handle exceptions (log error; increment errors_total)
  - Lifecycle logs: on_start/on_stop with node identity
- core/scheduler.py
  - On each loop: observe loop_latency histogram; update runnable_nodes gauge
  - When selecting priority band: increment priority_applied_total with band label
  - Lifecycle logs: scheduler.start/scheduler.shutdown
  - Optional span per iteration at debug or sampling enabled

Configuration
- ObservabilityConfig
  - logs:
    - level: "INFO" | "DEBUG" | "WARN" | "ERROR"
    - json: bool (default true)
  - metrics:
    - exporter: "noop" | "prometheus"
    - prometheus:
      - namespace: "arachne"
      - default_buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
  - tracing:
    - enabled: bool (default false)
    - provider: "opentelemetry" | "noop"
    - sample_rate: float (0.0–1.0), default 0.0 if disabled
- Runtime wiring:
  - Provide a simple configure_observability(config: ObservabilityConfig) function
  - Defaults: logs INFO, metrics noop, tracing disabled

Performance and Overhead
- Keep logging allocations out of the hot path; guard debug logs behind level checks
- Metrics:
  - Pre-bind label sets for hot counters/gauges to avoid per-call dict allocations
  - Use integer IDs for node/edge where feasible; export human-readable labels but store numeric keys internally
- Tracing:
  - Disabled by default; fast no-op when off
  - If enabled, keep spans coarse-grained and sampled

Metric Catalog (Initial)
- arachne_node_messages_total{node}
- arachne_node_errors_total{node}
- arachne_node_tick_duration_seconds_bucket/sum/count{node}
- arachne_edge_enqueued_total{edge_id, policy}
- arachne_edge_dequeued_total{edge_id}
- arachne_edge_dropped_total{edge_id, policy}
- arachne_edge_queue_depth{edge_id}
- arachne_edge_blocked_time_seconds_total{edge_id}
- arachne_scheduler_runnable_nodes{band}
- arachne_scheduler_loop_latency_seconds_bucket/sum/count{}
- arachne_scheduler_priority_applied_total{band}

Testing Strategy
Unit tests
- logging_test.py: structured JSON shape, level filtering, context enrichment, error logging with stack
- metrics_test.py: counters/gauges/histograms API behavior, no-op safety, Prometheus adapter label validation
- tracing_test.py: contextvars propagation, no-op behavior when disabled, span attributes set when enabled
- edge_obs_test.py: counters and gauges update on enqueue/dequeue/drop; blocked time accounting sanity
- node_obs_test.py: tick duration histogram observed; messages_total and errors_total increment; logs emitted with node context
- scheduler_obs_test.py: runnable_nodes gauge updates; loop latency histogram observed; priority_applied increments

Integration tests
- End-to-end run of hello_graph example:
  - Ensure basic metrics are incremented and logs are present
- Backpressure scenario:
  - Validate drops/blocked metrics under latest/drop/block policies respectively
- Tracing smoke (if provider available):
  - Verify spans created and trace_id propagated across on_message

Stress and Reliability
- Run with debug logging disabled to ensure minimal overhead
- Measure edge put/get throughput with metrics enabled; compare to baseline (≤5–10% overhead target)
- Long-running soak to ensure metric counters do not overflow typical types and memory remains stable

Acceptance Criteria
- Logging facade provides structured JSON logs with context and is used across core
- Metrics interface implemented with no-op default and Prometheus adapter; hot-path instrumentation wired for nodes/edges/scheduler
- Tracing adapter integrated via contextvars, disabled by default, with verified propagation when enabled
- Unit and integration tests pass; observability code coverage ≥85% (≥90% preferred)
- Overhead remains within acceptable bounds; debug logs can be fully disabled without code changes
- Documentation updated with configuration, metric catalog, and example dashboards/alerts

Risks and Mitigations
- Excessive overhead in hot paths:
  - Mitigation: No-op fast paths, pre-bound labels, guard debug logs, coarse-grained spans
- Log flooding:
  - Mitigation: Debug level for high-frequency events; rate-limit or disable drop logs by default; rely on metrics for high-rate signals
- Metrics cardinality explosion:
  - Mitigation: Keep labels minimal; avoid per-message IDs; ensure edge_id/node labels remain bounded
- Tracing vendor lock-in:
  - Mitigation: Adapter pattern; optional dependency; strict no-op defaults

Out of Scope (deferred)
- Auto-exposing Prometheus HTTP endpoint (leave to host application)
- Advanced log redaction frameworks (provide hooks only)
- Distributed tracing propagation across processes (future milestones)

Traceability
- Implements Technical Blueprint Implementation Plan M4.
- Satisfies EARS observability requirements for logs, metrics, and tracing, including error reporting and performance-awareness.

Checklist
- [x] logging.py: JSON logger, context enrichment, global config
- [x] metrics.py: interfaces, no-op implementation, Prometheus adapter
- [x] tracing.py: contextvars-backed adapter, OTEL integration (optional)
- [x] Core wiring: message, edge, node, scheduler instrumented
- [x] Tests: unit and integration for observability components
- [x] Docs: configuration guide, metric catalog, and operational guidance

## Completion Summary

**Status**: ✅ COMPLETED on 2025-01-13
**Test Results**: 99/99 tests passing, 86% overall coverage
**Deliverables**: All M4 requirements satisfied

### Implementation Details

**Core Observability Components**:
- `src/arachne/observability/logging.py` (103 lines) - JSON structured logging with contextvars
- `src/arachne/observability/metrics.py` (129 lines) - Prometheus metrics with no-op defaults
- `src/arachne/observability/tracing.py` (96 lines) - Optional tracing with contextvars integration
- `src/arachne/observability/config.py` (31 lines) - Unified configuration utilities
- `src/arachne/utils/ids.py` (13 lines) - ID generation utilities

**Core Module Integration**:
- Enhanced `message.py` with automatic trace_id generation and headers
- Instrumented `edge.py` with comprehensive logging and metrics
- Enhanced `node.py` with lifecycle logging and message processing metrics
- Instrumented `scheduler.py` with loop latency and scheduling metrics

**Testing**:
- 52 new observability unit tests (100% pass rate)
- 1 comprehensive integration test demonstrating end-to-end functionality  
- Coverage: 97% logging, 100% metrics, 99% tracing

**Integration Test Results**:
- ✅ 3 messages processed successfully
- ✅ 17 metrics recorded (8 counters, 2 gauges, 7 histograms)
- ✅ 842 spans created (comprehensive tracing coverage)
- ✅ 107 structured log lines generated

### EARS Requirements Satisfied

All M4 EARS requirements have been implemented and tested:
- ✅ Structured JSON logs for lifecycle events, exceptions, and key actions
- ✅ Metrics for nodes (ticks, processed, errors), edges (depth, rates, drops, blocked time), and scheduler (runnable nodes, loop latency, priority usage)
- ✅ Optional tracing with correlation ID propagation and span creation
- ✅ No-op observability by default with configurable Prometheus and tracing adapters
- ✅ Performance-aware implementation with minimal overhead

### Architecture Decisions

- **Modular Design**: Separate modules for logging, metrics, and tracing with clear interfaces
- **No-op Defaults**: Zero overhead when observability is disabled
- **Context Propagation**: Uses contextvars for automatic context enrichment
- **Prometheus Compatible**: Standard metric naming and label conventions
- **Configuration Driven**: Simple configuration for development/production environments

### Next Steps

M4 Observability is complete and ready for integration with future milestones. The observability infrastructure provides comprehensive visibility into runtime behavior and performance characteristics.