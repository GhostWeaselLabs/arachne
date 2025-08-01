from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.ids import generate_trace_id


class MessageType(str, Enum):
    DATA = "DATA"
    CONTROL = "CONTROL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Message:
    type: MessageType
    payload: Any
    metadata: Mapping[str, Any] | None = None
    headers: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure trace_id is present in headers
        if not self.headers.get("trace_id"):
            # We need to work around frozen dataclass limitation
            object.__setattr__(self, "headers", {**self.headers, "trace_id": generate_trace_id()})
        
        # Ensure timestamp is present
        if not self.headers.get("timestamp"):
            import time
            object.__setattr__(self, "headers", {**self.headers, "timestamp": time.time()})

    def is_control(self) -> bool:
        return self.type == MessageType.CONTROL

    def is_error(self) -> bool:
        return self.type == MessageType.ERROR

    def is_data(self) -> bool:
        return self.type == MessageType.DATA

    def get_trace_id(self) -> str:
        """Get the trace ID from headers."""
        return self.headers.get("trace_id", "")

    def get_timestamp(self) -> float:
        """Get the timestamp from headers."""
        return self.headers.get("timestamp", 0.0)

    def with_headers(self, **new_headers: Any) -> Message:
        """Create a new message with additional headers."""
        updated_headers = {**self.headers, **new_headers}
        return Message(
            type=self.type,
            payload=self.payload,
            metadata=self.metadata,
            headers=updated_headers
        )
