# Arachne Core Subpackage
# Minimal initializer for the core runtime namespace.
# M1 scope: provide stable import points and placeholders; real
# implementations arrive in later milestones.

from __future__ import annotations

__all__ = [
    "Node",
    "Message",
    "Subgraph",
    "Scheduler",
]

# Re-export placeholders from the top-level package for convenience.
# These placeholders are defined in `arachne.__init__` during M1 to keep imports working.
try:
    from .. import Message, Node, Scheduler, Subgraph
except Exception as _exc:  # pragma: no cover
    # In case the package layout changes or partial installs occur, provide ultra-minimal fallbacks.
    class Message:  # type: ignore[no-redef]
        __slots__ = ("payload", "headers")

        def __init__(self, payload: object | None = None, headers: dict[str, object] | None = None):
            self.payload = payload
            self.headers = headers or {}

    class Node:  # type: ignore[no-redef]
        def name(self) -> str:
            return self.__class__.__name__.lower()

        def inputs(self) -> dict[str, object]:
            return {}

        def outputs(self) -> dict[str, object]:
            return {}

        def on_start(self) -> None: ...
        def on_message(self, port: str, msg: Message) -> None: ...
        def on_tick(self) -> None: ...
        def on_stop(self) -> None: ...
        def emit(self, port: str, msg: Message) -> None: ...

    class Subgraph:  # type: ignore[no-redef]
        def add_node(self, node: Node) -> None: ...
        def connect(
            self,
            src: tuple[str, str],
            dst: tuple[str, str],
            capacity: int = 1,
        ) -> None: ...

    class Scheduler:  # type: ignore[no-redef]
        def register(self, subgraph: Subgraph) -> None: ...
        def run(self) -> None: ...
