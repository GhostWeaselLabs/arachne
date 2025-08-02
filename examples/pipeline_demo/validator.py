from __future__ import annotations

from typing import Any

from arachne.core.message import Message, MessageType
from arachne.core.node import Node
from arachne.core.ports import Port, PortDirection, PortSpec


class Validator(Node):
    """Drops invalid inputs, emits valid items only."""

    def __init__(self) -> None:
        super().__init__(name="validator")
        self.seen: int = 0
        self.valid: int = 0
        self.inputs = [Port(name="in", direction=PortDirection.INPUT, spec=PortSpec("in", dict))]
        self.outputs = [
            Port(name="out", direction=PortDirection.OUTPUT, spec=PortSpec("out", dict))
        ]

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port != "in":
            return
        self.seen += 1
        payload = msg.payload
        if isinstance(payload, dict) and "id" in payload:
            self.valid += 1
            self.emit("out", Message(type=MessageType.DATA, payload=payload))
