# Observability

Logging
- JSON logs for lifecycle and events; avoid secrets

Metrics
- Node: messages_total, errors_total, tick_duration
- Edge: enqueued_total, dequeued_total, dropped_total, queue_depth, blocked_time
- Scheduler: runnable_nodes, loop_latency, priority_applied

Tracing (optional)
- Correlate via trace_id; spans around node and edge operations when enabled

Enable
- Defaults are no-op; enable adapters via configuration flags or optional deps
