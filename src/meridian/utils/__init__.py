# Arachne Utils Subpackage
# M1 scope: provide stable import points and lightweight helpers/placeholders.
# Real implementations will arrive in later milestones (IDs, time helpers, validation, etc.).

from __future__ import annotations

__all__ = [
    "new_trace_id",
    "utc_now_iso",
    "require",
]

from datetime import UTC, datetime
import os
import secrets
import time


def new_trace_id(entropy_bytes: int = 16) -> str:
    """
    Generate a URL-safe, random trace identifier.

    Parameters
    ----------
    entropy_bytes:
        Number of random bytes to encode. Defaults to 16 (128 bits).

    Returns
    -------
    str
        A lowercase hex string suitable for correlation IDs and logs.

    Notes
    -----
    - Uses cryptographic randomness (secrets.token_hex).
    - Keep IDs opaque and avoid embedding sensitive data.
    """
    if entropy_bytes <= 0:
        entropy_bytes = 16
    return secrets.token_hex(entropy_bytes)


def utc_now_iso(precise: bool = True) -> str:
    """
    Get current UTC timestamp in ISO 8601 format.

    Parameters
    ----------
    precise:
        When True, include microseconds. When False, second resolution.

    Returns
    -------
    str
        e.g., "2025-01-01T12:34:56.789012Z" or "2025-01-01T12:34:56Z"
    """
    now = datetime.now(UTC)
    if precise:
        # Use timespec='microseconds' in Python 3.11+
        return now.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return now.isoformat(timespec="seconds").replace("+00:00", "Z")


def require(condition: bool, message: str = "Precondition failed") -> None:
    """
    Lightweight assertion helper for runtime preconditions.

    Parameters
    ----------
    condition:
        Boolean expression that must be True.
    message:
        Error message raised when the condition is False.

    Raises
    ------
    ValueError
        If the condition is False.

    Notes
    -----
    Prefer explicit validation with meaningful error messages over bare `assert`,
    which can be stripped with optimization flags. This helper provides a consistent
    failure type (ValueError) for invalid arguments and state checks.
    """
    if not condition:
        raise ValueError(message)


# Environment and time helpers (minimal, safe defaults)


def env_flag(name: str, default: bool = False) -> bool:
    """
    Interpret an environment variable as a boolean flag.

    Truthy (case-insensitive): "1", "true", "yes", "on"
    Falsy  (case-insensitive): "0", "false", "no", "off"
    Otherwise, returns default.

    Parameters
    ----------
    name:
        Environment variable name.
    default:
        Fallback when the variable is unset or not recognized.

    Returns
    -------
    bool
    """
    val = os.getenv(name)
    if val is None:
        return default
    lowered = val.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def monotonic_ns() -> int:
    """
    Return a strictly-monotonic clock reading in nanoseconds.

    Useful for measuring durations without being affected by system clock changes.
    """
    return time.monotonic_ns()
