from __future__ import annotations

from arachne.core.message import Message, MessageType


class KillSwitch:
    """Publishes a shutdown signal on control-plane edge."""

    def __init__(self) -> None:
        self.triggered = False

    def on_tick(self) -> Message[str] | None:
        if self.triggered:
            return None
        self.triggered = True
        return Message(type=MessageType.CONTROL, payload="shutdown")
