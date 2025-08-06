---
title: Observability
description: Comprehensive guide to structured logging, metrics collection, and distributed tracing in Meridian Runtime, including configuration, usage patterns, and integration examples.
tags:
  - observability
  - logging
  - metrics
  - tracing
  - monitoring
  - debugging
---

# Observability

Meridian Runtime provides a comprehensive observability system with structured logging, metrics collection, and distributed tracing. All subsystems are designed to be zero-cost when disabled and integrate seamlessly with external monitoring systems.

!!! info "See Also"
    Check the [API Reference](../reference/api.md) for detailed API documentation and the [Patterns](../concepts/patterns.md) for observability usage patterns.

## Tutorial: Getting Started

### Basic Configuration

Configure all observability subsystems with a single configuration object:

```python
from meridian.observability.config import ObservabilityConfig, configure_observability

# Simple development setup
config = ObservabilityConfig(
    log_level="INFO",
    log_json=True,
    metrics_enabled=True,
    metrics_namespace="myapp",
    tracing_enabled=True,
    tracing_provider="inmemory",
    tracing_sample_rate=1.0
)

configure_observability(config)
```

### Pre-configured Environments

Use built-in configurations for common environments:

```python
from meridian.observability.config import get_development_config, get_production_config

# Development: full observability for debugging
dev_config = get_development_config()
configure_observability(dev_config)

# Production: optimized for performance
prod_config = get_production_config()
configure_observability(prod_config)
```

## How-to: Structured Logging

### Basic Logging

Use structured logging with event keys and contextual fields:

```python
from meridian.observability.logging import get_logger

logger = get_logger()

# Simple logging
logger.info("node.start", "Node starting up", node_name="worker", version="1.0")

# Error logging with context
logger.error("node.error", "Failed to process message", 
            error="validation_failed", 
            message_id="123",
            port="input")
```

### Contextual Logging

Enrich logs with runtime context using `with_context()`:

```python
from meridian.observability.logging import get_logger, with_context

logger = get_logger()

# Add context for a block of operations
with with_context(node="worker", edge_id="input->output", trace_id="abc-123"):
    logger.info("processing.start", "Starting message processing")
    
    # All logs in this block inherit the context
    logger.debug("processing.step", "Validating message")
    logger.info("processing.complete", "Message processed successfully")
```

### Log Levels and Configuration

Configure logging behavior globally:

```python
from meridian.observability.logging import configure, LogLevel

# Configure logging programmatically
configure(
    level=LogLevel.DEBUG,
    extra={"service": "myapp", "version": "1.0"}
)

# JSON vs key=value format
configure(level="INFO")  # Uses JSON by default
```

## How-to: Metrics Collection

### Basic Metrics

Collect application and runtime metrics:

```python
from meridian.observability.metrics import get_metrics

metrics = get_metrics()

# Counters for events
messages_processed = metrics.counter("messages_processed_total")
messages_processed.inc()

# Gauges for current state
queue_depth = metrics.gauge("queue_depth")
queue_depth.set(42)

# Histograms for distributions
processing_time = metrics.histogram("processing_duration_seconds")
processing_time.observe(0.125)
```

### Performance Monitoring

Use `time_block()` for automatic timing and metrics:

```python
from meridian.observability.metrics import time_block

# Automatic timing with metrics
with time_block("node_processing_duration"):
    result = process_message(msg)
    # Timing automatically recorded when block exits
```

### Custom Metrics with Labels

Add dimensions to metrics for better analysis:

```python
metrics = get_metrics()

# Metrics with labels for filtering/grouping
errors_by_type = metrics.counter("errors_total", labels={"error_type": "validation"})
errors_by_type.inc()

# Node-specific metrics
node_metrics = metrics.gauge("node_memory_bytes", labels={"node": "worker"})
node_metrics.set(1024 * 1024)
```

## How-to: Distributed Tracing

### Basic Tracing

Create spans to track operation flow:

```python
from meridian.observability.tracing import start_span

# Create a span for an operation
with start_span("process_message", {"message_id": "123", "node": "worker"}):
    # All operations in this block are traced
    validate_message(msg)
    transform_message(msg)
    send_message(msg)
```

### Nested Spans

Create hierarchical traces:

```python
from meridian.observability.tracing import start_span

with start_span("pipeline_execution", {"pipeline": "data_processing"}):
    # Parent span
    
    with start_span("validation", {"stage": "input"}):
        validate_input(data)
    
    with start_span("transformation", {"stage": "processing"}):
        transform_data(data)
    
    with start_span("output", {"stage": "final"}):
        send_output(data)
```

### Trace Context Management

Manage trace context across operations:

```python
from meridian.observability.tracing import set_trace_id, get_trace_id

# Set trace context
set_trace_id("abc-123-def-456")

# Retrieve current trace ID
current_trace = get_trace_id()
print(f"Current trace: {current_trace}")
```

## Reference: Configuration Options

### ObservabilityConfig

Complete configuration for all observability subsystems:

```python
@dataclass
class ObservabilityConfig:
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_json: bool = True
    log_stream: TextIO | None = None
    
    # Metrics
    metrics_enabled: bool = False
    metrics_namespace: str = "meridian-runtime"
    
    # Tracing
    tracing_enabled: bool = False
    tracing_provider: str = "noop"
    tracing_sample_rate: float = 0.0
```

### Log Levels

Available logging severity levels:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARN`: Warning conditions
- `ERROR`: Error conditions

### Tracing Providers

Supported tracing backends:

- `"noop"`: Disabled tracing (default)
- `"inmemory"`: In-memory tracer for development
- `"opentelemetry"`: OpenTelemetry integration (placeholder)

## Reference: Metric Types

### Counter

Monotonically increasing values for counting events:

```python
counter = metrics.counter("events_total")
counter.inc()           # Increment by 1
counter.inc(5)          # Increment by 5
```

### Gauge

Current value measurements for state:

```python
gauge = metrics.gauge("active_connections")
gauge.set(42)           # Set current value
```

### Histogram

Distribution measurements for latency and sizes:

```python
histogram = metrics.histogram("request_duration_seconds")
histogram.observe(0.125)  # Record observation
```

## Reference: Built-in Metrics

### Node Metrics

Runtime automatically collects these metrics for each node:

- `messages_total`: Total messages processed
- `errors_total`: Total errors encountered
- `tick_duration`: Time spent in tick operations

### Edge Metrics

Per-edge metrics for monitoring data flow:

- `enqueued_total`: Messages enqueued
- `dequeued_total`: Messages dequeued
- `dropped_total`: Messages dropped due to overflow
- `queue_depth`: Current queue depth
- `blocked_time`: Time spent blocked

### Scheduler Metrics

System-level performance metrics:

- `runnable_nodes`: Number of runnable nodes
- `loop_latency`: Scheduler loop latency
- `priority_applied`: Priority scheduling decisions

## Explanation: Observability Patterns

### When to Use Each Subsystem

**Logging**: Use for operational events, errors, and debugging information

- ✅ Lifecycle events (start, stop, configuration changes)
- ✅ Error conditions with context
- ✅ Debug information for troubleshooting

**Metrics**: Use for performance monitoring and alerting

- ✅ Throughput measurements (messages/second)
- ✅ Latency distributions (processing time)
- ✅ Resource utilization (memory, queue depth)
- ✅ Business metrics (success rate, error rate)

**Tracing**: Use for request flow analysis and debugging

- ✅ Request/response flows across nodes
- ✅ Performance bottleneck identification
- ✅ Distributed debugging
- ✅ Dependency analysis

### Performance Considerations

- **Zero Cost**: All subsystems are no-op when disabled
- **Sampling**: Use tracing sample rates to control overhead
- **Buffering**: Metrics are buffered in memory for efficiency
- **Async**: Logging and metrics don't block the main processing loop

### Integration with External Systems

**Logging**: JSON format compatible with log aggregation systems

- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Cloud logging (AWS CloudWatch, GCP Logging)

**Metrics**: Prometheus-compatible format

- Prometheus for collection and alerting
- Grafana for visualization
- Cloud monitoring (AWS CloudWatch, GCP Monitoring)

**Tracing**: OpenTelemetry compatible

- Jaeger for trace visualization
- Zipkin for distributed tracing
- Cloud tracing (AWS X-Ray, GCP Trace)

### Best Practices

1. **Structured Logging**: Always use event keys and structured fields
2. **Context Propagation**: Use `with_context()` for related operations
3. **Metric Naming**: Use consistent naming conventions (snake_case)
4. **Label Cardinality**: Limit metric label values to prevent explosion
5. **Sampling**: Use appropriate tracing sample rates for production
6. **Error Handling**: Log errors with sufficient context for debugging 