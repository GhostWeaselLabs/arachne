"""Time utilities for Arachne runtime.

Provides monotonic and wall-clock helpers with minimal allocation overhead.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
import time


def now_ts_ms() -> int:
    """Get current epoch time in milliseconds.

    Returns:
        int: Milliseconds since Unix epoch
    """
    return int(time.time() * 1000)


def now_rfc3339() -> str:
    """Get current time as RFC3339 formatted string in UTC.

    Returns:
        str: RFC3339 timestamp (e.g., "2024-01-15T10:30:45.123456Z")
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def monotonic_ns() -> int:
    """Get monotonic time in nanoseconds.

    Returns:
        int: Monotonic nanoseconds, suitable for duration measurements
    """
    return time.monotonic_ns()


@contextmanager
def time_block(name: str | None = None) -> Generator[float, None, None]:
    """Context manager for timing code blocks.

    Args:
        name: Optional name for the timing block (not used in implementation,
              but available for caller logging/metrics)

    Yields:
        float: Start time in monotonic seconds

    Example:
        with time_block("processing") as start_time:
            # do work
            pass
        # elapsed time available via time.monotonic() - start_time

    Or to capture elapsed time:
        with time_block() as start_time:
            # do work
            pass
        elapsed = time.monotonic() - start_time
    """
    start = time.monotonic()
    try:
        yield start
    finally:
        # Context manager doesn't return elapsed time directly
        # to keep allocation minimal - caller can compute if needed
        pass


# Legacy compatibility functions
def generate_timestamp() -> float:
    """Generate a timestamp in seconds since epoch (legacy alias)."""
    return time.time()


def generate_monotonic_timestamp() -> float:
    """Generate a monotonic timestamp for duration measurements (legacy alias)."""
    return time.perf_counter()
