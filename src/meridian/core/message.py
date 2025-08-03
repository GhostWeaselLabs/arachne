from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.ids import generate_trace_id


class MessageType(str, Enum):
    """
    Public message classification used by the runtime and Scheduler.

    DATA:
      User or system payloads intended for normal processing.

    CONTROL:
      Out-of-band control signals (e.g., start/stop/flush/watermarks) that may
      be routed differently by policies.

    ERROR:
      Error-carrying messages surfaced by nodes or adapters. Error payloads
      must avoid including sensitive contents; prefer metadata and redacted
      context.

    Notes:
      - Routing/backpressure policies may treat CONTROL and ERROR differently
        from DATA.
      - Emission and handling of ERROR should be explicit in application code.
    """

    DATA = "DATA"
    CONTROL = "CONTROL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Message:
    """
    Immutable envelope carrying a payload, optional metadata, and transport headers.

    Semantics
      - type: MessageType classification (DATA, CONTROL, ERROR) that can influence routing,
        backpressure policy, and metrics.
      - payload: Application-defined value (structured or primitive). Avoid including secrets.
      - metadata: Optional structured, typed context for application use; not interpreted by
        the runtime.
      - headers: Transport-level, runtime-interpreted keys (e.g., trace_id, timestamp).
        These are mutated only during construction in __post_init__ to ensure required keys.

    Headers
      - trace_id (str): Stable identifier for distributed tracing. Auto-generated if missing.
      - timestamp (float): Seconds since epoch when the message was created. Auto-populated
        if missing.

    Safety and Privacy
      - Prefer redaction of sensitive data before placing values into payload/metadata/headers.
      - ERROR messages should avoid embedding raw payload contents; attach redacted context.

    Usage
      - Use helpers is_data(), is_control(), is_error() for quick checks.
      - Use with_headers(...) to derive a new message with additional/overridden headers.

    """

    type: MessageType
    payload: Any
    metadata: Mapping[str, Any] | None = None
    headers: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Normalize headers to include required keys.

        Side effects:
          - Ensures "trace_id" is present, generating one if absent.
          - Ensures "timestamp" is present, set to current time if absent.

        Notes:
          - This method mutates the frozen dataclass via object.__setattr__ only to
            finalize auto-populated headers at construction time.
        """
        # Ensure trace_id is present in headers only when the key is absent.
        # If the key is present with a value of None, preserve that explicit intent.
        if "trace_id" not in self.headers:
            # We need to work around frozen dataclass limitation
            object.__setattr__(self, "headers", {**self.headers, "trace_id": generate_trace_id()})

        # Ensure timestamp is present only when the key is absent.
        # If the key is present with a value of None, preserve that explicit intent
        # so get_timestamp() can coerce it to 0.0 in tests.
        if "timestamp" not in self.headers:
            import time

            object.__setattr__(self, "headers", {**self.headers, "timestamp": time.time()})

    def is_control(self) -> bool:
        """Return True if this message is a CONTROL message."""
        return self.type == MessageType.CONTROL

    def is_error(self) -> bool:
        """Return True if this message is an ERROR message."""
        return self.type == MessageType.ERROR

    def is_data(self) -> bool:
        """Return True if this message is a DATA message."""
        return self.type == MessageType.DATA

    def get_trace_id(self) -> str:
        """
        Get the trace ID from headers.

        Returns:
          Non-empty string if present; otherwise an empty string.
        """
        value = self.headers.get("trace_id", "")
        return str(value) if value is not None else ""

    def get_timestamp(self) -> float:
        """
        Get the creation timestamp from headers.

        Returns:
          Float seconds since epoch when the message was created, or 0.0 if invalid.
        """
        value = self.headers.get("timestamp", 0.0)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def with_headers(self, **new_headers: Any) -> Message:
        """
        Derive a new Message with additional or overridden header values.
        Existing headers are preserved unless overridden by new_headers.

        Parameters:
          **new_headers: Header key/value pairs to merge into current headers.

        Returns:
          A new Message instance with updated headers.
        """
        updated_headers = {**self.headers, **new_headers}
        return Message(
            type=self.type, payload=self.payload, metadata=self.metadata, headers=updated_headers
        )
