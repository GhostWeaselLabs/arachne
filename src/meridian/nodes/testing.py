from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import time
from typing import Any, DefaultDict

from ..core.message import Message, MessageType
from ..core.node import Node


class _FakeScheduler:
    """Minimal scheduler stub to capture node emissions during tests.

    Only implements the internal hook used by Node.emit().
    """

    def __init__(self) -> None:
        self._emitted: DefaultDict[tuple[str, str], list[Message]] = defaultdict(list)

    def _handle_node_emit(self, node: Node, port: str, msg: Message) -> None:  # noqa: D401 - internal hook
        self._emitted[(node.name, port)].append(msg)


@dataclass(slots=True)
class NodeTestHarness:
    """Testing utility for built-in nodes.

    Provides simple helpers to inject messages, trigger ticks, and retrieve
    emitted messages without running the full scheduler/graph.
    """

    node: Node
    _scheduler: _FakeScheduler = field(default_factory=_FakeScheduler, init=False)

    def __post_init__(self) -> None:
        # Wire the node to the fake scheduler to capture emits
        self.node._set_scheduler(self._scheduler)  # type: ignore[attr-defined]

    def send_message(self, port: str, payload: Any, *, metadata: dict[str, Any] | None = None, headers: dict[str, Any] | None = None) -> None:
        """Send a DATA message to the node via on_message()."""
        msg = Message(MessageType.DATA, payload, metadata=metadata, headers=headers or {})
        self.node.on_message(port, msg)

    def send_control(self, port: str, payload: Any | None = None) -> None:
        """Send a CONTROL message to the node via on_message()."""
        msg = Message(MessageType.CONTROL, payload)
        self.node.on_message(port, msg)

    def send_error(self, port: str, error_payload: Any) -> None:
        """Send an ERROR message to the node via on_message()."""
        msg = Message(MessageType.ERROR, error_payload)
        self.node.on_message(port, msg)

    def get_emitted_messages(self, port: str) -> list[Message]:
        """Retrieve messages emitted by node on the given output port."""
        return list(self._scheduler._emitted.get((self.node.name, port), []))

    def trigger_tick(self) -> None:
        """Manually trigger node tick for testing."""
        self.node.on_tick()
        # Allow background worker loops (if any) to make progress between ticks
        time.sleep(0.001)
