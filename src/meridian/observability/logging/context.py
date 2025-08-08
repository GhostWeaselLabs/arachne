from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_node_context: ContextVar[str | None] = ContextVar("node_context", default=None)
_edge_context: ContextVar[str | None] = ContextVar("edge_context", default=None)
_port_context: ContextVar[str | None] = ContextVar("port_context", default=None)
_message_type_context: ContextVar[str | None] = ContextVar("message_type_context", default=None)


def set_trace_id(trace_id: str) -> None:
    _trace_id.set(trace_id)


def get_trace_id() -> str | None:
    return _trace_id.get()


# Internal getters used by logger to enrich records
def get_node() -> str | None:
    return _node_context.get()


def get_edge_id() -> str | None:
    return _edge_context.get()


def get_port() -> str | None:
    return _port_context.get()


def get_message_type() -> str | None:
    return _message_type_context.get()


class LogContext:
    def __init__(self, **fields: Any) -> None:
        self._fields = fields
        self._tokens: dict[str, Any] = {}

    def __enter__(self) -> LogContext:
        if "trace_id" in self._fields:
            self._tokens["trace_id"] = _trace_id.set(self._fields["trace_id"])
        if "node" in self._fields:
            self._tokens["node"] = _node_context.set(self._fields["node"])
        if "edge_id" in self._fields:
            self._tokens["edge_id"] = _edge_context.set(self._fields["edge_id"])
        if "port" in self._fields:
            self._tokens["port"] = _port_context.set(self._fields["port"])
        if "message_type" in self._fields:
            self._tokens["message_type"] = _message_type_context.set(self._fields["message_type"])
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        for var_name, token in self._tokens.items():
            if var_name == "trace_id":
                _trace_id.reset(token)
            elif var_name == "node":
                _node_context.reset(token)
            elif var_name == "edge_id":
                _edge_context.reset(token)
            elif var_name == "port":
                _port_context.reset(token)
            elif var_name == "message_type":
                _message_type_context.reset(token)


def with_context(**fields: Any) -> LogContext:
    return LogContext(**fields)
