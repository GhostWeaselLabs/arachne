from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
import json
import sys
import time
from typing import Any, TextIO


class LogLevel(str, Enum):
    """Logging severity levels for the structured logger."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


# Context variables for enriching logs
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_node_context: ContextVar[str | None] = ContextVar("node_context", default=None)
_edge_context: ContextVar[str | None] = ContextVar("edge_context", default=None)
_port_context: ContextVar[str | None] = ContextVar("port_context", default=None)


@dataclass
class LogConfig:
    """
    Configuration for the global structured logger.

    Attributes:
      level:
        Minimum LogLevel to emit (messages below this level are suppressed).
      json:
        When True, log records are emitted as compact JSON. Otherwise, a simple
        key=value format is used.
      stream:
        Output stream for log lines (defaults to sys.stderr).
      extra_fields:
        Static fields merged into every record (e.g., service, version).
    """

    level: LogLevel = LogLevel.INFO
    json: bool = True
    stream: TextIO = field(default_factory=lambda: sys.stderr)
    extra_fields: dict[str, Any] = field(default_factory=dict)


class Logger:
    """
    Minimal structured logger with contextual fields support.

    Behavior:
      - Emits records as JSON or key=value lines to the configured stream.
      - Enriches records with contextual fields (trace_id, node, edge_id, port)
        when set via with_context().
      - Suppresses messages below the configured minimum level.
    """

    def __init__(self, config: LogConfig) -> None:
        self._config = config
        self._level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARN: 2,
            LogLevel.ERROR: 3,
        }

    def _should_log(self, level: LogLevel) -> bool:
        return self._level_order[level] >= self._level_order[self._config.level]

    def _build_record(
        self, level: LogLevel, event: str, message: str, **fields: Any
    ) -> dict[str, Any]:
        record = {
            "ts": time.time(),
            "level": level.value,
            "event": event,
            "message": message,
        }

        # Add context from contextvars
        if trace_id := _trace_id.get():
            record["trace_id"] = trace_id
        if node := _node_context.get():
            record["node"] = node
        if edge := _edge_context.get():
            record["edge_id"] = edge
        if port := _port_context.get():
            record["port"] = port

        # Add extra fields from config
        record.update(self._config.extra_fields)

        # Add fields from call
        record.update(fields)

        return record

    def _emit(self, record: dict[str, Any]) -> None:
        """Write a single record to the configured stream."""
        if self._config.json:
            line = json.dumps(record, separators=(",", ":"))
        else:
            # Simple key=value format for non-JSON mode
            parts = [f"{k}={v}" for k, v in record.items()]
            line = " ".join(parts)

        print(line, file=self._config.stream)

    def debug(self, event: str, message: str, **fields: Any) -> None:
        """Emit a DEBUG log with an event key and message."""
        if self._should_log(LogLevel.DEBUG):
            record = self._build_record(LogLevel.DEBUG, event, message, **fields)
            self._emit(record)

    def info(self, event: str, message: str, **fields: Any) -> None:
        """Emit an INFO log with an event key and message."""
        if self._should_log(LogLevel.INFO):
            record = self._build_record(LogLevel.INFO, event, message, **fields)
            self._emit(record)

    def warn(self, event: str, message: str, **fields: Any) -> None:
        """Emit a WARN log with an event key and message."""
        if self._should_log(LogLevel.WARN):
            record = self._build_record(LogLevel.WARN, event, message, **fields)
            self._emit(record)

    def error(self, event: str, message: str, **fields: Any) -> None:
        """Emit an ERROR log with an event key and message."""
        if self._should_log(LogLevel.ERROR):
            record = self._build_record(LogLevel.ERROR, event, message, **fields)
            self._emit(record)


# Global logger instance
_global_config = LogConfig()
_global_logger = Logger(_global_config)


def get_logger() -> Logger:
    """Get the global logger instance."""
    return _global_logger


def configure(
    level: str | LogLevel,
    stream: TextIO | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Configure the global logger.

    Parameters:
      level:
        LogLevel or level name string ("DEBUG", "INFO", "WARN", "ERROR").
      stream:
        Optional stream to write logs to (defaults to current configured stream).
      extra:
        Optional static fields to include in every record.

    Notes:
      - Does not change JSON vs key=value mode; set via LogConfig.json at construction time.
    """
    global _global_config, _global_logger

    if isinstance(level, str):
        level = LogLevel(level.upper())

    _global_config = LogConfig(
        level=level,
        stream=stream or _global_config.stream,
        extra_fields=extra or {},
    )
    _global_logger = Logger(_global_config)


class LogContext:
    """Context manager for enriching logs with additional fields.

    Usage:
      with with_context(trace_id="...", node="A", edge_id="A:o->B:i", port="o"):
          logger.info("event", "message")

    Fields:
      - trace_id: string trace identifier
      - node: node name
      - edge_id: stable edge identifier
      - port: port name
    """

    def __init__(self, **fields: Any) -> None:
        self._fields = fields
        self._tokens: dict[str, Any] = {}

    def __enter__(self) -> LogContext:
        # Set context variables
        if "trace_id" in self._fields:
            self._tokens["trace_id"] = _trace_id.set(self._fields["trace_id"])
        if "node" in self._fields:
            self._tokens["node"] = _node_context.set(self._fields["node"])
        if "edge_id" in self._fields:
            self._tokens["edge_id"] = _edge_context.set(self._fields["edge_id"])
        if "port" in self._fields:
            self._tokens["port"] = _port_context.set(self._fields["port"])
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Reset context variables
        for var_name, token in self._tokens.items():
            if var_name == "trace_id":
                _trace_id.reset(token)
            elif var_name == "node":
                _node_context.reset(token)
            elif var_name == "edge_id":
                _edge_context.reset(token)
            elif var_name == "port":
                _port_context.reset(token)


def with_context(**fields: Any) -> LogContext:
    """Create a context manager that enriches subsequent logs."""
    return LogContext(**fields)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current logging context."""
    _trace_id.set(trace_id)


def get_trace_id() -> str | None:
    """Get the current trace ID from the logging context."""
    return _trace_id.get()
