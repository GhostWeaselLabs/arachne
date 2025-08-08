from __future__ import annotations

import json
from io import StringIO

import pytest

from meridian.observability.logging import (
    LogConfig,
    Logger,
    LogLevel,
    configure,
    get_logger,
    get_trace_id,
    set_trace_id,
    with_context,
)


class TestLogger:
    def test_logger_basic_functionality(self) -> None:
        """Test basic logger functionality."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        logger.info("test.event", "Test message")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["level"] == "INFO"
        assert record["event"] == "test.event"
        assert record["message"] == "Test message"
        assert "ts" in record

    def test_log_levels(self) -> None:
        """Test log level filtering."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.WARN, stream=stream)
        logger = Logger(config)

        logger.debug("debug.event", "Debug message")
        logger.info("info.event", "Info message")
        logger.warn("warn.event", "Warn message")
        logger.error("error.event", "Error message")

        lines = stream.getvalue().strip().split("\n")
        # Only warn and error should be logged
        assert len(lines) == 2

        warn_record = json.loads(lines[0])
        error_record = json.loads(lines[1])

        assert warn_record["level"] == "WARN"
        assert error_record["level"] == "ERROR"

    def test_context_enrichment(self) -> None:
        """Test context variable enrichment."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        set_trace_id("test-trace-123")

        logger.info("test.event", "Test message")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["trace_id"] == "test-trace-123"

    def test_with_context_manager(self) -> None:
        """Test context manager for enriching logs."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        with with_context(node="test-node", edge_id="test-edge"):
            logger.info("test.event", "Test message")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["node"] == "test-node"
        assert record["edge_id"] == "test-edge"

    def test_extra_fields(self) -> None:
        """Test additional fields in log records."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        logger.info("test.event", "Test message", custom_field="custom_value", count=42)

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["custom_field"] == "custom_value"
        assert record["count"] == 42

    def test_non_json_format(self) -> None:
        """Test non-JSON log format."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream, json=False)
        logger = Logger(config)

        logger.info("test.event", "Test message")

        output = stream.getvalue().strip()
        assert "level=INFO" in output
        assert "event=test.event" in output
        assert "message=Test message" in output

    def test_config_extra_fields(self) -> None:
        """Test extra fields from config."""
        stream = StringIO()
        config = LogConfig(
            level=LogLevel.DEBUG,
            stream=stream,
            extra_fields={"service": "meridian-runtime", "version": "1.0.0"},
        )
        logger = Logger(config)

        logger.info("test.event", "Test message")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["service"] == "meridian-runtime"
        assert record["version"] == "1.0.0"


class TestGlobalLogger:
    def test_get_logger(self) -> None:
        """Test getting the global logger."""
        logger = get_logger()
        assert isinstance(logger, Logger)

    def test_configure_global_logger(self) -> None:
        """Test configuring the global logger."""
        stream = StringIO()
        configure(LogLevel.ERROR, stream=stream)

        logger = get_logger()
        logger.debug("debug.event", "Debug message")
        logger.error("error.event", "Error message")

        output = stream.getvalue().strip()
        lines = output.split("\n") if output else []

        # Only error should be logged
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["level"] == "ERROR"

    def test_configure_with_string_level(self) -> None:
        """Test configuring with string log level."""
        stream = StringIO()
        configure("WARN", stream=stream)

        logger = get_logger()
        logger.info("info.event", "Info message")
        logger.warn("warn.event", "Warn message")

        output = stream.getvalue().strip()
        lines = output.split("\n") if output else []

        # Only warn should be logged
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["level"] == "WARN"


class TestTraceIdHelpers:
    def test_set_get_trace_id(self) -> None:
        """Test trace ID helpers."""
        test_trace_id = "test-trace-456"

        set_trace_id(test_trace_id)
        assert get_trace_id() == test_trace_id

    def test_trace_id_isolation(self) -> None:
        """Test trace ID context isolation."""
        # This test would need proper asyncio context to fully test isolation
        # For now, just test basic functionality
        set_trace_id("trace-1")
        assert get_trace_id() == "trace-1"

        set_trace_id("trace-2")
        assert get_trace_id() == "trace-2"


class TestContextManager:
    def test_context_manager_nesting(self) -> None:
        """Test nested context managers."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        with with_context(node="outer-node"):
            with with_context(port="inner-port"):
                logger.info("test.event", "Nested context")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert record["node"] == "outer-node"
        assert record["port"] == "inner-port"

    def test_context_manager_cleanup(self) -> None:
        """Test context manager properly cleans up."""
        stream = StringIO()
        config = LogConfig(level=LogLevel.DEBUG, stream=stream)
        logger = Logger(config)

        with with_context(node="test-node"):
            pass

        # Log after context should not have node field
        logger.info("test.event", "After context")

        output = stream.getvalue().strip()
        record = json.loads(output)

        assert "node" not in record or record.get("node") is None


if __name__ == "__main__":
    pytest.main([__file__])
