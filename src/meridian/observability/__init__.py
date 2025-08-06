# Arachne Observability Subpackage
# M1 scope: provide stable import points and lightweight placeholders so
# imports resolve.
# Real implementations (structured logging, metrics interface, optional
# tracing) will arrive in later milestones.

from __future__ import annotations

__all__ = [
    "get_logger",
    "Logger",
    "Metrics",
    "Tracer",
]


# Placeholder logger interface (minimal façade).
class Logger:  # pragma: no cover - placeholder to satisfy imports
    """
    Minimal structured logger façade.

    Later milestones will provide:
    - Stable key conventions (e.g., event, node, edge, trace_id, error)
    - JSON formatting and integration hooks for exporters
    - Redaction policies for sensitive fields
    """

    def __init__(self, name: str = "meridian-runtime"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def _emit(self, level: str, event: str, **fields: object) -> None:
        # Placeholder no-op. Real implementation will route to Python logging
        # or a structured sink.
        _ = (level, event, fields)

    def info(self, event: str, **fields: object) -> None:
        self._emit("INFO", event, **fields)

    def warning(self, event: str, **fields: object) -> None:
        self._emit("WARNING", event, **fields)

    def error(self, event: str, **fields: object) -> None:
        self._emit("ERROR", event, **fields)

    def debug(self, event: str, **fields: object) -> None:
        self._emit("DEBUG", event, **fields)


def get_logger(name: str = "meridian-runtime") -> Logger:  # pragma: no cover
    """
    Factory for a structured logger. In later milestones:
    - Bind contextual fields (e.g., node, subgraph, scheduler)
    - Support child loggers and correlation IDs
    """
    return Logger(name=name)


# Placeholder metrics interface.
class Metrics:  # pragma: no cover - placeholder to satisfy imports
    """
    Minimal metrics façade.

    Later milestones will provide:
    - Counter, Gauge, Histogram helpers
    - Stable naming and label conventions (node, edge, scheduler)
    - Export adapters (e.g., Prometheus) behind optional extras
    """

    def counter(
        self,
        name: str,
        description: str = "",
        labels: dict[str, str] | None = None,
    ) -> None:
        _ = (name, description, labels)

    def gauge(
        self,
        name: str,
        description: str = "",
        labels: dict[str, str] | None = None,
    ) -> None:
        _ = (name, description, labels)

    def histogram(
        self,
        name: str,
        description: str = "",
        labels: dict[str, str] | None = None,
    ) -> None:
        _ = (name, description, labels)


# Placeholder tracer interface.
class Tracer:  # pragma: no cover - placeholder to satisfy imports
    """
    Minimal tracing façade.

    Later milestones will provide:
    - Optional OpenTelemetry span creation
    - Lightweight context propagation without sensitive data by default
    """

    def start_span(self, name: str, **attrs: object) -> Span:
        _ = (name, attrs)
        return Span(name=name, attributes=dict(attrs))


class Span:  # pragma: no cover - placeholder to satisfy imports
    def __init__(self, name: str, attributes: dict[str, object] | None = None):
        self.name = name
        self.attributes = attributes or {}

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value

    def end(self) -> None:
        # Placeholder no-op. Real implementation will end/export a span.
        return None
