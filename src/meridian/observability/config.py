from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from .logging import LogLevel, configure as configure_logging
from .metrics import PrometheusConfig, PrometheusMetrics, configure_metrics
from .tracing import TracingConfig, configure_tracing


@dataclass
class ObservabilityConfig:
    """
    Complete observability configuration for logging, metrics, and tracing.

    Attributes:
      log_level:
        Minimum log level to emit (DEBUG, INFO, WARN, ERROR).
      log_json:
        Emit logs as compact JSON when True; otherwise use key=value format.
      log_stream:
        Optional IO stream to write logs to (defaults to stderr if None).

      metrics_enabled:
        Enable metrics collection when True; a Prometheus-like in-memory provider
        is configured by default.
      metrics_namespace:
        Namespace/prefix applied to metric names (e.g., "meridian-runtime_edge_enqueued_total").

      tracing_enabled:
        Enable tracing when True.
      tracing_provider:
        Provider identifier ("noop", "inmemory", or future "opentelemetry").
      tracing_sample_rate:
        Fraction (0.0–1.0) indicating sampling rate; provider-specific behavior.
    """

    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    log_json: bool = True
    log_stream: TextIO | None = None

    # Metrics configuration
    metrics_enabled: bool = False
    metrics_namespace: str = "meridian-runtime"

    # Tracing configuration
    tracing_enabled: bool = False
    tracing_provider: str = "noop"
    tracing_sample_rate: float = 0.0


def configure_observability(config: ObservabilityConfig) -> None:
    """
    Configure logging, metrics, and tracing from a single configuration object.

    Parameters:
      config:
        ObservabilityConfig containing settings for each subsystem.

    Behavior:
      - Logging: sets global logger level/stream and toggles JSON vs key=value mode.
      - Metrics: when enabled, installs a Prometheus-like in-memory provider
        with the configured namespace.
      - Tracing: when enabled, configures the global tracer according to provider and
        sample rate (e.g., "inmemory" for development, "noop" otherwise).
    """
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
    """
    Get the default observability configuration.

    Returns:
      ObservabilityConfig with INFO logs, metrics and tracing disabled.
    """
    return ObservabilityConfig()


def get_development_config() -> ObservabilityConfig:
    """
    Get a development-oriented observability configuration.

    Returns:
      ObservabilityConfig with:
        - DEBUG log level
        - Metrics enabled
        - In-memory tracing enabled at 100% sample rate
    """
    return ObservabilityConfig(
        log_level=LogLevel.DEBUG,
        metrics_enabled=True,
        tracing_enabled=True,
        tracing_provider="inmemory",
        tracing_sample_rate=1.0,
    )


def get_production_config() -> ObservabilityConfig:
    """
    Get a production-oriented observability configuration.

    Returns:
      ObservabilityConfig with:
        - INFO log level
        - Metrics enabled
        - Tracing enabled (provider "opentelemetry" placeholder) at 10% sample rate
    """
    return ObservabilityConfig(
        log_level=LogLevel.INFO,
        metrics_enabled=True,
        tracing_enabled=True,
        tracing_provider="opentelemetry",
        tracing_sample_rate=0.1,
    )
