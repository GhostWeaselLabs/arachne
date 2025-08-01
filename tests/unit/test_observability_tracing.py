from __future__ import annotations

import pytest

from src.arachne.observability.tracing import (
    InMemoryTracer,
    NoopTracer,
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


class TestTracingConfig:
    def test_default_config(self) -> None:
        """Test default tracing configuration."""
        config = TracingConfig()

        assert config.enabled is False
        assert config.provider == "noop"
        assert config.sample_rate == 0.0

    def test_custom_config(self) -> None:
        """Test custom tracing configuration."""
        config = TracingConfig(enabled=True, provider="opentelemetry", sample_rate=0.1)

        assert config.enabled is True
        assert config.provider == "opentelemetry"
        assert config.sample_rate == 0.1


class TestNoopTracer:
    def test_noop_tracer_disabled(self) -> None:
        """Test no-op tracer when disabled."""
        config = TracingConfig(enabled=False)
        tracer = NoopTracer(config)

        assert tracer.is_enabled() is False

        span = tracer.start_span("test.operation")
        assert span.name == "test.operation"
        assert span.trace_id == ""
        assert span.span_id == ""

    def test_noop_span_operations(self) -> None:
        """Test no-op span operations."""
        config = TracingConfig(enabled=False)
        tracer = NoopTracer(config)

        span = tracer.start_span("test.operation", {"key": "value"})

        # Should not raise exceptions
        span.set_attribute("test", "value")
        span.finish()

        assert span.is_finished() is False  # NoopSpan always returns False


class TestInMemoryTracer:
    def test_inmemory_tracer_disabled(self) -> None:
        """Test in-memory tracer when disabled."""
        config = TracingConfig(enabled=False)
        tracer = InMemoryTracer(config)

        assert tracer.is_enabled() is False

        span = tracer.start_span("test.operation")
        assert span.name == "test.operation"
        assert span.trace_id == ""
        assert span.span_id == ""

        # Should not record spans when disabled
        assert len(tracer.get_spans()) == 0

    def test_inmemory_tracer_enabled(self) -> None:
        """Test in-memory tracer when enabled."""
        config = TracingConfig(enabled=True)
        tracer = InMemoryTracer(config)

        assert tracer.is_enabled() is True

        span = tracer.start_span("test.operation", {"key": "value"})

        assert span.name == "test.operation"
        assert span.trace_id != ""
        assert span.span_id != ""
        assert span.attributes == {"key": "value"}

        # Should record the span
        spans = tracer.get_spans()
        assert len(spans) == 1
        assert spans[0] is span

    def test_span_lifecycle(self) -> None:
        """Test span lifecycle operations."""
        config = TracingConfig(enabled=True)
        tracer = InMemoryTracer(config)

        span = tracer.start_span("test.operation")

        assert span.is_finished() is False

        span.set_attribute("duration", 0.123)
        assert span.attributes["duration"] == 0.123

        span.finish()
        assert span.is_finished() is True

        # Setting attributes after finish should be ignored
        span.set_attribute("after_finish", "ignored")
        assert "after_finish" not in span.attributes

    def test_clear_spans(self) -> None:
        """Test clearing recorded spans."""
        config = TracingConfig(enabled=True)
        tracer = InMemoryTracer(config)

        tracer.start_span("span1")
        tracer.start_span("span2")

        assert len(tracer.get_spans()) == 2

        tracer.clear_spans()
        assert len(tracer.get_spans()) == 0


class TestGlobalTracing:
    def test_default_noop_tracer(self) -> None:
        """Test default global tracer is no-op."""
        # Reset to default
        configure_tracing(TracingConfig())

        tracer = get_tracer()
        assert isinstance(tracer, NoopTracer)
        assert not tracer.is_enabled()

    def test_configure_inmemory_tracer(self) -> None:
        """Test configuring in-memory tracer."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        tracer = get_tracer()
        assert isinstance(tracer, InMemoryTracer)
        assert tracer.is_enabled()

    def test_is_tracing_enabled(self) -> None:
        """Test global tracing enabled check."""
        # Disabled by default
        configure_tracing(TracingConfig(enabled=False))
        assert not is_tracing_enabled()

        # Enable tracing
        configure_tracing(TracingConfig(enabled=True, provider="inmemory"))
        assert is_tracing_enabled()


class TestStartSpanContextManager:
    def test_start_span_context_manager(self) -> None:
        """Test start_span context manager."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        tracer = get_tracer()
        assert isinstance(tracer, InMemoryTracer)

        with start_span("test.operation", {"key": "value"}) as span:
            assert span.name == "test.operation"
            assert span.attributes == {"key": "value"}
            assert not span.is_finished()

        # Span should be finished after context exit
        assert span.is_finished()

        # Should be recorded
        spans = tracer.get_spans()
        assert len(spans) == 1
        assert spans[0] is span

    def test_start_span_with_exception(self) -> None:
        """Test start_span context manager with exception."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        tracer = get_tracer()
        assert isinstance(tracer, InMemoryTracer)

        with pytest.raises(ValueError):
            with start_span("error.operation") as span:
                raise ValueError("Test error")

        # Span should still be finished
        assert span.is_finished()

        # Should still be recorded
        spans = tracer.get_spans()
        assert len(spans) == 1

    def test_start_span_noop(self) -> None:
        """Test start_span with no-op tracer."""
        configure_tracing(TracingConfig(enabled=False))

        with start_span("test.operation") as span:
            assert span.name == "test.operation"
            assert span.trace_id == ""
            assert span.span_id == ""


class TestTraceIdHelpers:
    def test_set_get_trace_id(self) -> None:
        """Test trace ID context helpers."""
        test_trace_id = "test-trace-123"

        set_trace_id(test_trace_id)
        assert get_trace_id() == test_trace_id

    def test_get_span_id(self) -> None:
        """Test span ID context helper."""
        # Initially should be None
        assert get_span_id() is None

        # After starting a span, should have span ID
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        with start_span("test.operation") as span:
            # Context should be set during span
            current_span_id = get_span_id()
            assert current_span_id == span.span_id

    def test_generate_trace_id(self) -> None:
        """Test trace ID generation."""
        trace_id1 = generate_trace_id()
        trace_id2 = generate_trace_id()

        assert trace_id1 != trace_id2
        assert len(trace_id1) > 0
        assert len(trace_id2) > 0

    def test_trace_context_propagation(self) -> None:
        """Test trace context propagation."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        # Set initial trace ID
        set_trace_id("parent-trace-123")

        with start_span("parent.operation") as parent_span:
            # Should use the set trace ID
            assert parent_span.trace_id == "parent-trace-123"
            assert get_trace_id() == "parent-trace-123"

            with start_span("child.operation") as child_span:
                # Child should inherit parent's trace ID
                assert child_span.trace_id == "parent-trace-123"
                assert get_trace_id() == "parent-trace-123"


class TestTracingIntegration:
    def test_nested_spans(self) -> None:
        """Test nested span creation."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        tracer = get_tracer()
        assert isinstance(tracer, InMemoryTracer)

        with start_span("outer.operation"):
            with start_span("inner.operation"):
                pass

        spans = tracer.get_spans()
        assert len(spans) == 2

        # Both spans should have the same trace ID
        assert spans[0].trace_id == spans[1].trace_id

        # But different span IDs
        assert spans[0].span_id != spans[1].span_id

    def test_span_attributes(self) -> None:
        """Test span attribute setting."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        with start_span("test.operation", {"initial": "value"}) as span:
            span.set_attribute("runtime", "added")
            span.set_attribute("count", 42)

        assert span.attributes["initial"] == "value"
        assert span.attributes["runtime"] == "added"
        assert span.attributes["count"] == 42

    def test_multiple_independent_traces(self) -> None:
        """Test multiple independent traces."""
        config = TracingConfig(enabled=True, provider="inmemory")
        configure_tracing(config)

        tracer = get_tracer()
        assert isinstance(tracer, InMemoryTracer)

        # First trace
        set_trace_id("trace-1")
        with start_span("operation.1"):
            pass

        # Second trace
        set_trace_id("trace-2")
        with start_span("operation.2"):
            pass

        spans = tracer.get_spans()
        assert len(spans) == 2

        # Should have different trace IDs
        trace_ids = {span.trace_id for span in spans}
        assert len(trace_ids) == 2
        assert "trace-1" in trace_ids
        assert "trace-2" in trace_ids


if __name__ == "__main__":
    pytest.main([__file__])
