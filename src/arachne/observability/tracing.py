from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
import uuid

# Context variables for tracing
_current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)
_current_span_id: ContextVar[str | None] = ContextVar("current_span_id", default=None)


@dataclass
class TracingConfig:
    enabled: bool = False
    provider: str = "noop"  # "opentelemetry" | "noop"
    sample_rate: float = 0.0


class Span:
    """Represents a tracing span."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.attributes = attributes or {}
        self._finished = False

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        if not self._finished:
            self.attributes[key] = value

    def finish(self) -> None:
        """Mark the span as finished."""
        self._finished = True

    def is_finished(self) -> bool:
        """Check if the span is finished."""
        return self._finished


class NoopSpan(Span):
    """No-op span implementation."""

    def __init__(self, name: str) -> None:
        super().__init__(name, "", "")

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def finish(self) -> None:
        pass


class Tracer:
    """Base tracer interface."""

    def __init__(self, config: TracingConfig) -> None:
        self._config = config

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        """Start a new span."""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._config.enabled


class NoopTracer(Tracer):
    """No-op tracer implementation."""

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        return NoopSpan(name)


class InMemoryTracer(Tracer):
    """In-memory tracer for testing and development."""

    def __init__(self, config: TracingConfig) -> None:
        super().__init__(config)
        self.spans: list[Span] = []

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        if not self._config.enabled:
            return NoopSpan(name)

        # Get or generate trace ID
        trace_id = _current_trace_id.get() or self._generate_trace_id()
        span_id = self._generate_span_id()

        span = Span(name, trace_id, span_id, attributes)
        self.spans.append(span)
        return span

    def _generate_trace_id(self) -> str:
        """Generate a new trace ID."""
        return str(uuid.uuid4())

    def _generate_span_id(self) -> str:
        """Generate a new span ID."""
        return str(uuid.uuid4())

    def get_spans(self) -> list[Span]:
        """Get all recorded spans."""
        return self.spans.copy()

    def clear_spans(self) -> None:
        """Clear all recorded spans."""
        self.spans.clear()


# Global tracer instance
_global_tracer: Tracer = NoopTracer(TracingConfig())


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    return _global_tracer


def configure_tracing(config: TracingConfig) -> None:
    """Configure the global tracer."""
    global _global_tracer

    if config.provider == "inmemory":
        _global_tracer = InMemoryTracer(config)
    else:
        _global_tracer = NoopTracer(config)


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]:
    """Context manager that creates and manages a span."""
    tracer = get_tracer()
    span = tracer.start_span(name, attributes)

    # Set span context
    old_trace_id = _current_trace_id.get()
    old_span_id = _current_span_id.get()

    trace_token = _current_trace_id.set(span.trace_id) if span.trace_id else None
    span_token = _current_span_id.set(span.span_id) if span.span_id else None

    try:
        yield span
    finally:
        span.finish()

        # Restore context
        if trace_token:
            _current_trace_id.set(old_trace_id)
        if span_token:
            _current_span_id.set(old_span_id)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context."""
    _current_trace_id.set(trace_id)


def get_trace_id() -> str | None:
    """Get the current trace ID."""
    return _current_trace_id.get()


def get_span_id() -> str | None:
    """Get the current span ID."""
    return _current_span_id.get()


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    return str(uuid.uuid4())


def is_tracing_enabled() -> bool:
    """Check if tracing is currently enabled."""
    return get_tracer().is_enabled()
