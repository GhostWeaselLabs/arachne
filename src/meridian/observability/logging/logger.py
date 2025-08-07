from __future__ import annotations

import json
import time
from typing import Any, TextIO

from .config import LogConfig, LogLevel
from .context import (
    LogContext,
    get_trace_id as _get_trace_id_ctx,
    get_node as _get_node_ctx,
    get_edge_id as _get_edge_ctx,
    get_port as _get_port_ctx,
    get_message_type as _get_msg_type_ctx,
    with_context,
)


class Logger:
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

    def _build_record(self, level: LogLevel, event: str, message: str, **fields: Any) -> dict[str, Any]:
        record = {"ts": time.time(), "level": level.value, "event": event, "message": message}
        if (trace_id := _get_trace_id_ctx()) is not None:
            record["trace_id"] = trace_id
        if (node := _get_node_ctx()) is not None:
            record["node"] = node
        if (edge_id := _get_edge_ctx()) is not None:
            record["edge_id"] = edge_id
        if (port := _get_port_ctx()) is not None:
            record["port"] = port
        if (mt := _get_msg_type_ctx()) is not None:
            record["message_type"] = mt
        record.update(self._config.extra_fields)
        record.update(fields)
        return record

    def _emit(self, record: dict[str, Any]) -> None:
        if self._config.json:
            line = json.dumps(record, separators=(",", ":"))
        else:
            parts = [f"{k}={v}" for k, v in record.items()]
            line = " ".join(parts)
        print(line, file=self._config.stream)

    def debug(self, event: str, message: str, **fields: Any) -> None:
        if self._should_log(LogLevel.DEBUG):
            self._emit(self._build_record(LogLevel.DEBUG, event, message, **fields))

    def info(self, event: str, message: str, **fields: Any) -> None:
        if self._should_log(LogLevel.INFO):
            self._emit(self._build_record(LogLevel.INFO, event, message, **fields))

    def warn(self, event: str, message: str, **fields: Any) -> None:
        if self._should_log(LogLevel.WARN):
            self._emit(self._build_record(LogLevel.WARN, event, message, **fields))

    def error(self, event: str, message: str, **fields: Any) -> None:
        if self._should_log(LogLevel.ERROR):
            self._emit(self._build_record(LogLevel.ERROR, event, message, **fields))


# Global logger instance and helpers
_global_config = LogConfig()
_global_logger = Logger(_global_config)


def get_logger() -> Logger:
    return _global_logger


def configure(level: str | LogLevel, stream: TextIO | None = None, extra: dict[str, Any] | None = None) -> None:
    global _global_config, _global_logger
    if isinstance(level, str):
        level = LogLevel(level.upper())
    _global_config = LogConfig(level=level, stream=stream or _global_config.stream, extra_fields=extra or {})
    _global_logger = Logger(_global_config)
