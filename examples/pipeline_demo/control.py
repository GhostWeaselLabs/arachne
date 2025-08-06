from __future__ import annotations

from meridian.core import Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class KillSwitch(Node):
    """Publishes a shutdown signal on control-plane edge."""

    def __init__(self) -> None:
        super().__init__(
            name="control",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
        )
        self.triggered = False

    def _handle_tick(self) -> None:
        if self.triggered:
            return
        self.triggered = True
        self.emit("out", Message(type=MessageType.CONTROL, payload="shutdown"))
