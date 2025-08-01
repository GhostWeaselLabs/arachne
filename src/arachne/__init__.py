# Arachne package initializer
# This package provides a minimal, reusable graph runtime for Python.
# Milestone M1: package skeletons and placeholder modules so imports
# resolve in tests/examples.
# Python >= 3.11
from __future__ import annotations

import sys as _sys

__all__ = [
    "__version__",
    # Subpackages
    "core",
    "observability",
    "utils",
]

# Public version for tooling/tests; updated by release automation in later milestones.
__version__ = "0.0.0"

# Lightweight runtime metadata (kept internal for now)
_PKG_NAME = "arachne"
_MIN_PY = (3, 11)

# Optional: runtime guard for supported Python versions.
if _sys.version_info < _MIN_PY:
    raise RuntimeError(
        f"{_PKG_NAME} requires Python {'.'.join(map(str, _MIN_PY))}+; "
        f"detected {_sys.version.split()[0]}"
    )

# Placeholder re-exports (for convenience imports in examples/tests).
# These symbols will be defined for real in later milestones.
# We intentionally avoid importing non-existent modules to keep M1 green.
# Instead, we provide minimal placeholder classes and types that document intent.


class Message:  # pragma: no cover - placeholder to satisfy imports
    """
    Placeholder Message type.

    In later milestones this will carry:
    - payload: Any
    - headers: dict[str, Any] with trace_id, timestamp, content_type, etc.
    """

    __slots__ = ("payload", "headers")

    def __init__(self, payload: object | None = None, headers: dict[str, object] | None = None):
        self.payload = payload
        self.headers = headers or {}


class Node:  # pragma: no cover - placeholder to satisfy imports
    """
    Placeholder Node base class.

    In later milestones this will define async-friendly lifecycle hooks:
    - on_start, on_message, on_tick, on_stop
    And typed port specifications via inputs()/outputs().
    """

    def name(self) -> str:  # noqa: D401
        """Return node name."""
        return self.__class__.__name__.lower()

    def inputs(self) -> dict[str, object]:
        return {}

    def outputs(self) -> dict[str, object]:
        return {}

    # Lifecycle placeholders; concrete behavior will be added later.
    def on_start(self) -> None:  # noqa: D401
        """Called when the node starts."""
        return None

    def on_message(self, port: str, msg: Message) -> None:  # noqa: D401
        """Called when a message arrives on an input port."""
        return None

    def on_tick(self) -> None:  # noqa: D401
        """Called periodically by the scheduler for housekeeping."""
        return None

    def on_stop(self) -> None:  # noqa: D401
        """Called when the node stops for cleanup."""
        return None

    # Minimal emit to satisfy examples; later provided by runtime wiring.
    def emit(self, port: str, msg: Message) -> None:  # noqa: D401
        """Emit a message on an output port (no-op placeholder)."""
        _ = (port, msg)
        return None


class Subgraph:  # pragma: no cover - placeholder to satisfy imports
    """
    Placeholder Subgraph for composition.

    Later will support add_node(), connect(), expose ports, and validation.
    """

    def add_node(self, node: Node) -> None:
        _ = node

    def connect(self, src: tuple[str, str], dst: tuple[str, str], capacity: int = 1) -> None:
        _ = (src, dst, capacity)


class Scheduler:  # pragma: no cover - placeholder to satisfy imports
    """
    Placeholder Scheduler.

    Later will implement fairness, bounded edges/backpressure, and lifecycle control.
    """

    def register(self, subgraph: Subgraph) -> None:
        _ = subgraph

    def run(self) -> None:
        # No-op placeholder to satisfy example invocations.
        return None


# Namespaces are created by directory structure in M1; we expose them
# for linters/docs.
# from . import core as core       # Will be importable once modules land
# from . import observability as observability
# from . import utils as utils
