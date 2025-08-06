from __future__ import annotations

from typing import Any

from meridian.core import Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Transformer(Node):
    """Normalizes payloads and forwards."""

    def __init__(self) -> None:
        super().__init__(
            name="transformer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", dict))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", dict))],
        )

    def _handle_message(self, port: str, msg: Message[dict[str, Any]]) -> None:
        if port != "in":
            return
        payload = dict(msg.payload)
        payload.setdefault("normalized", True)
        self.emit("out", Message(type=MessageType.DATA, payload=payload))
