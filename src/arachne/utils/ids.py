from __future__ import annotations

import uuid
import time


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """Generate a new span ID."""
    return str(uuid.uuid4())


def generate_timestamp() -> float:
    """Generate a timestamp in seconds since epoch."""
    return time.time()


def generate_monotonic_timestamp() -> float:
    """Generate a monotonic timestamp for duration measurements."""
    return time.perf_counter() 