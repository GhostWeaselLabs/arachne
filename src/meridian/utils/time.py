"""Time utilities for the Arachne runtime.

Provides monotonic and wall-clock helpers with minimal allocation overhead and
clear, copy-paste-friendly examples.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
import time


def now_ts_ms() -> int:
    """Return the current Unix epoch time in milliseconds.

    Returns:
        int: Milliseconds since the Unix epoch.

    Example:
        ts_ms = now_ts_ms()
        # e.g., 1735728000123
    """
    return int(time.time() * 1000)


def now_rfc3339() -> str:
    """Return the current UTC time as an RFC3339-formatted string.

    Returns:
        str: RFC3339 timestamp (e.g., "2024-01-15T10:30:45.123456Z").

    Example:
        ts = now_rfc3339()
        # e.g., "2024-01-15T10:30:45.123456Z"
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def monotonic_ns() -> int:
    """Return a monotonic clock reading in nanoseconds.

    Returns:
        int: Monotonic nanoseconds, suitable for duration measurements.

    Example:
        start_ns = monotonic_ns()
        # ... do work ...
        elapsed_ns = monotonic_ns() - start_ns
    """
    return time.monotonic_ns()


@contextmanager
def time_block(name: str | None = None) -> Generator[float, None, None]:
    """Context manager for timing code blocks using a monotonic clock.

    Parameters:
        name: Optional descriptive name for the timing block (for logs/metrics only).

    Yields:
        float: The start time in monotonic seconds.

    Examples:
        Basic usage:
            with time_block("processing") as start_time:
                # do work
                pass
            # Compute elapsed time:
            # elapsed = time.monotonic() - start_time

        Without a name:
            with time_block() as start_time:
                # do work
                pass
            elapsed = time.monotonic() - start_time

    Notes:
        - The context does not directly return the elapsed time to avoid extra allocations.
          Callers can compute elapsed = time.monotonic() - start_time if needed.
    """
    start = time.monotonic()
    try:
        yield start
    finally:
        # Keep allocation minimal; callers compute elapsed as needed.
        pass


# Legacy compatibility functions
def generate_timestamp() -> float:
    """Generate a wall-clock timestamp in seconds since the Unix epoch (legacy alias)."""
    return time.time()


def generate_monotonic_timestamp() -> float:
    """Generate a monotonic timestamp in seconds for duration measurements (legacy alias)."""
    return time.perf_counter()
