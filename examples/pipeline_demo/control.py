from __future__ import annotations

from arachne.core.message import Message, MessageType
from arachne.core.node import Node
from arachne.core.ports import Port, PortDirection, PortSpec


class KillSwitch(Node):
    """Publishes a shutdown signal on control-plane edge."""

    def __init__(self) -> None:
        super().__init__(name="control")
        self.triggered = False
        self.outputs = [Port(name="out", direction=PortDirection.OUTPUT, spec=PortSpec("out", str))]

    def _handle_tick(self) -> None:
        if self.triggered:
            return
        self.triggered = True
        self.emit("out", Message(type=MessageType.CONTROL, payload="shutdown"))
