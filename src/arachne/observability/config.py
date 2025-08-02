from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from .logging import LogLevel, configure as configure_logging
from .metrics import PrometheusConfig, PrometheusMetrics, configure_metrics
from .tracing import TracingConfig, configure_tracing


@dataclass
class ObservabilityConfig:
    """Complete observability configuration."""

    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    log_json: bool = True
    log_stream: TextIO | None = None

    # Metrics configuration
    metrics_enabled: bool = False
    metrics_namespace: str = "arachne"

    # Tracing configuration
    tracing_enabled: bool = False
    tracing_provider: str = "noop"
    tracing_sample_rate: float = 0.0


def configure_observability(config: ObservabilityConfig) -> None:
    """Configure all observability components."""

    # Configure logging
    configure_logging(
        level=config.log_level, stream=config.log_stream, extra={"json": config.log_json}
    )

    # Configure metrics
    if config.metrics_enabled:
        prometheus_config = PrometheusConfig(namespace=config.metrics_namespace)
        prometheus_metrics = PrometheusMetrics(prometheus_config)
        configure_metrics(prometheus_metrics)

    # Configure tracing
    if config.tracing_enabled:
        tracing_config = TracingConfig(
            enabled=True, provider=config.tracing_provider, sample_rate=config.tracing_sample_rate
        )
        configure_tracing(tracing_config)


def get_default_config() -> ObservabilityConfig:
    """Get default observability configuration."""
    return ObservabilityConfig()


def get_development_config() -> ObservabilityConfig:
    """Get development observability configuration with enhanced logging."""
    return ObservabilityConfig(
        log_level=LogLevel.DEBUG,
        metrics_enabled=True,
        tracing_enabled=True,
        tracing_provider="inmemory",
        tracing_sample_rate=1.0,
    )


def get_production_config() -> ObservabilityConfig:
    """Get production observability configuration."""
    return ObservabilityConfig(
        log_level=LogLevel.INFO,
        metrics_enabled=True,
        tracing_enabled=True,
        tracing_provider="opentelemetry",
        tracing_sample_rate=0.1,
    )
