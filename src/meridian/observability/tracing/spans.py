from __future__ import annotations

from typing import Any


class Span:
    """Represents a tracing span with a name, trace_id, and span_id."""

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
        if not self._finished:
            self.attributes[key] = value

    def finish(self) -> None:
        self._finished = True

    def is_finished(self) -> bool:
        return self._finished


class NoopSpan(Span):
    """No-op span implementation that ignores all operations."""

    def __init__(self, name: str) -> None:
        super().__init__(name, "", "")

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D401
        return None

    def finish(self) -> None:  # noqa: D401
        return None


class OpenTelemetrySpan(Span):
    """Span implementation that wraps an OpenTelemetry span."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        otel_span: Any,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, trace_id, span_id, attributes)
        self._otel_span = otel_span

    def set_attribute(self, key: str, value: Any) -> None:
        if not self._finished:
            self.attributes[key] = value
            try:
                self._otel_span.set_attribute(key, str(value))
            except Exception:
                pass

    def finish(self) -> None:
        if not self._finished:
            self._finished = True
            try:
                self._otel_span.end()
            except Exception:
                pass
