from __future__ import annotations

import uuid


def new_trace_id() -> str:
    """
    Generate a new trace ID suitable for correlation across boundaries.

    Returns:
        str: UUID4 hex string without dashes (not cryptographically secure).

    Notes:
        - Intended for tracing/diagnostics, not for security tokens.
    """
    return uuid.uuid4().hex


def new_id(prefix: str | None = None) -> str:
    """
    Generate a new identifier with an optional prefix.

    Parameters:
        prefix: Optional string to prepend to the UUID4 hex component.

    Returns:
        str: "{prefix}_{uuid4hex}" when prefix is provided; otherwise "uuid4hex".

    Notes:
        - Not cryptographically secure; do not use for authentication or secrets.
    """
    id_part = uuid.uuid4().hex
    if prefix:
        return f"{prefix}_{id_part}"
    return id_part


# Legacy aliases for backward compatibility
def generate_trace_id() -> str:
    """
    Generate a new trace ID (legacy alias).

    Returns:
        str: UUID4 string with dashes (legacy format).
    """
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID (legacy alias).

    Returns:
        str: UUID4 string with dashes (legacy format).
    """
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """
    Generate a new span ID (legacy alias).

    Returns:
        str: UUID4 string with dashes (legacy format).
    """
    return str(uuid.uuid4())
