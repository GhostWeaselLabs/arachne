from __future__ import annotations

from typing import Any
import uuid

from .config import TracingConfig
from .spans import Span, NoopSpan, OpenTelemetrySpan


class Tracer:
    """
    Base tracer interface.
    """

    def __init__(self, config: TracingConfig) -> None:
        self._config = config

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return self._config.enabled


class NoopTracer(Tracer):
    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        return NoopSpan(name)


class InMemoryTracer(Tracer):
    def __init__(self, config: TracingConfig) -> None:
        super().__init__(config)
        self.spans: list[Span] = []

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        if not self._config.enabled:
            return NoopSpan(name)
        trace_id = get_trace_id() or generate_trace_id()
        span_id = generate_span_id()
        span = Span(name, trace_id, span_id, attributes)
        self.spans.append(span)
        return span

    def get_spans(self) -> list[Span]:
        return self.spans.copy()

    def clear_spans(self) -> None:
        self.spans.clear()


class OpenTelemetryTracer(Tracer):
    def __init__(self, config: TracingConfig) -> None:
        super().__init__(config)
        self._otel_tracer = None
        self._initialize_otel()

    def _initialize_otel(self) -> None:
        if not self._config.enabled:
            return
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBasedSampler

            sampler = TraceIdRatioBasedSampler(self._config.sample_rate)
            if not isinstance(trace.get_tracer_provider(), TracerProvider):
                trace.set_tracer_provider(TracerProvider(sampler=sampler))
            self._otel_tracer = trace.get_tracer("meridian-runtime")
        except Exception:
            self._otel_tracer = None

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        if not self._config.enabled or self._otel_tracer is None:
            return NoopSpan(name)
        try:
            otel_span = self._otel_tracer.start_span(name)
            if attributes:
                for k, v in attributes.items():
                    try:
                        otel_span.set_attribute(k, str(v))
                    except Exception:
                        pass
            ctx = otel_span.get_span_context()
            trace_id = format(ctx.trace_id, '032x')
            span_id = format(ctx.span_id, '016x')
            return OpenTelemetrySpan(name, trace_id, span_id, otel_span, attributes)
        except Exception:
            return NoopSpan(name)


# Global tracer
_global_tracer: Tracer = NoopTracer(TracingConfig())


def get_tracer() -> Tracer:
    return _global_tracer


def configure_tracing(config: TracingConfig) -> None:
    global _global_tracer
    if config.provider == "inmemory":
        _global_tracer = InMemoryTracer(config)
    elif config.provider == "opentelemetry":
        _global_tracer = OpenTelemetryTracer(config)
    else:
        _global_tracer = NoopTracer(config)


def is_tracing_enabled() -> bool:
    return get_tracer().is_enabled()


# Context helpers (implemented here to avoid circular deps)
from contextlib import contextmanager
from typing import Iterator
from contextvars import ContextVar

_current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)
_current_span_id: ContextVar[str | None] = ContextVar("current_span_id", default=None)


def set_trace_id(trace_id: str) -> None:
    _current_trace_id.set(trace_id)


def get_trace_id() -> str | None:
    return _current_trace_id.get()


def get_span_id() -> str | None:
    return _current_span_id.get()


def generate_trace_id() -> str:
    return str(uuid.uuid4())


def generate_span_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]:
    tracer = get_tracer()
    span = tracer.start_span(name, attributes)

    old_trace_id = _current_trace_id.get()
    old_span_id = _current_span_id.get()

    trace_token = _current_trace_id.set(span.trace_id) if span.trace_id else None
    span_token = _current_span_id.set(span.span_id) if span.span_id else None

    try:
        yield span
    finally:
        span.finish()
        if trace_token is not None:
            _current_trace_id.set(old_trace_id)
        if span_token is not None:
            _current_span_id.set(old_span_id)
