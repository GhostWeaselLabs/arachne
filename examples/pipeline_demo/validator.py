from __future__ import annotations

from typing import Any

from meridian.core import Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Validator(Node):
    """Drops invalid inputs, emits valid items only."""

    def __init__(self) -> None:
        super().__init__(
            name="validator",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", dict))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", dict))],
        )
        self.seen: int = 0
        self.valid: int = 0

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port != "in":
            return
        self.seen += 1
        payload = msg.payload
        if isinstance(payload, dict) and "id" in payload:
            self.valid += 1
            self.emit("out", Message(type=MessageType.DATA, payload=payload))
