from __future__ import annotations

from typing import Any

from arachne.core.message import Message, MessageType


class Validator:
    """Drops invalid inputs, emits valid items only."""

    def __init__(self) -> None:
        self.seen: int = 0
        self.valid: int = 0

    def on_message(self, port: str, msg: Message[Any]) -> Message[Any] | None:
        if port != "in":
            return None
        self.seen += 1
        payload = msg.payload
        if isinstance(payload, dict) and "id" in payload:
            self.valid += 1
            return Message(type=MessageType.DATA, payload=payload)
        return None
