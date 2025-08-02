from __future__ import annotations

from typing import Any

from arachne.core.message import Message, MessageType
from arachne.core.node import Node
from arachne.core.ports import Port, PortDirection, PortSpec


class Transformer(Node):
    """Normalizes payloads and forwards."""

    def __init__(self) -> None:
        super().__init__(name="transformer")
        self.inputs = [Port(name="in", direction=PortDirection.INPUT, spec=PortSpec("in", dict))]
        self.outputs = [Port(name="out", direction=PortDirection.OUTPUT, spec=PortSpec("out", dict))]

    def _handle_message(self, port: str, msg: Message[dict[str, Any]]) -> None:
        if port != "in":
            return
        payload = dict(msg.payload)
        payload.setdefault("normalized", True)
        self.emit("out", Message(type=MessageType.DATA, payload=payload))
