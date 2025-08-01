from __future__ import annotations

import uuid


def new_trace_id() -> str:
    """Generate a new trace ID.
    
    Returns a UUID4 hex string without dashes for compactness.
    Note: Not cryptographically secure; not for security tokens.
    
    Returns:
        str: Trace ID suitable for correlation across system boundaries
    """
    return uuid.uuid4().hex


def new_id(prefix: str | None = None) -> str:
    """Generate a new ID with optional prefix.
    
    Args:
        prefix: Optional prefix to prepend to the ID
        
    Returns:
        str: ID in format "{prefix}_{uuid4hex}" if prefix given, otherwise just uuid4hex
        
    Note: Not cryptographically secure; not for security tokens.
    """
    id_part = uuid.uuid4().hex
    if prefix:
        return f"{prefix}_{id_part}"
    return id_part


# Legacy aliases for backward compatibility
def generate_trace_id() -> str:
    """Generate a new trace ID (legacy alias)."""
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """Generate a new correlation ID (legacy alias)."""
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """Generate a new span ID (legacy alias)."""
    return str(uuid.uuid4()) 