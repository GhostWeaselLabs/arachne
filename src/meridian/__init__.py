from __future__ import annotations

import sys as _sys

from .core import (
    Edge,
    Message,
    MessageType,
    Node,
    Port,
    PortDirection,
    Scheduler,
    SchedulerConfig,
    Subgraph,
)

__all__ = [
    "__version__",
    "core",
    "observability",
    "utils",
    # Convenience re-exports
    "Message",
    "MessageType",
    "Node",
    "Subgraph",
    "Edge",
    "Port",
    "PortDirection",
    "Scheduler",
    "SchedulerConfig",
]

__version__ = "0.0.0"

_PKG_NAME = "meridian"
_MIN_PY = (3, 11)

if _sys.version_info < _MIN_PY:
    raise RuntimeError(
        f"{_PKG_NAME} requires Python {'.'.join(map(str, _MIN_PY))}+; "
        f"detected {_sys.version.split()[0]}"
    )
