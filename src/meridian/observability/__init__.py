from __future__ import annotations

# Stable import points for observability subpackages
from .logging import LogConfig, Logger, LogLevel, configure, get_logger, with_context
from .metrics import (
    DEFAULT_LATENCY_BUCKETS,
    Counter,
    Gauge,
    Histogram,
    Metrics,
    NoopMetrics,
    PrometheusConfig,
    PrometheusMetrics,
    configure_metrics,
    get_metrics,
    time_block,
)
from .tracing import (
    InMemoryTracer,
    NoopTracer,
    OpenTelemetrySpan,
    Span,
    TracingConfig,
    configure_tracing,
    generate_trace_id,
    get_span_id,
    get_trace_id,
    get_tracer,
    is_tracing_enabled,
    set_trace_id,
    start_span,
)

__all__ = [
    # logging
    "LogConfig",
    "LogLevel",
    "Logger",
    "configure",
    "get_logger",
    "with_context",
    # metrics
    "PrometheusConfig",
    "PrometheusMetrics",
    "NoopMetrics",
    "DEFAULT_LATENCY_BUCKETS",
    "Counter",
    "Gauge",
    "Histogram",
    "Metrics",
    "get_metrics",
    "configure_metrics",
    "time_block",
    # tracing
    "TracingConfig",
    "InMemoryTracer",
    "NoopTracer",
    "Span",
    "OpenTelemetrySpan",
    "get_tracer",
    "configure_tracing",
    "is_tracing_enabled",
    "start_span",
    "set_trace_id",
    "get_trace_id",
    "get_span_id",
    "generate_trace_id",
]
