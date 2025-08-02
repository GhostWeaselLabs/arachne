from __future__ import annotations

from typing import Any

from arachne.core.message import Message, MessageType


class Transformer:
    """Normalizes payloads and forwards."""

    def on_message(self, port: str, msg: Message[dict[str, Any]]) -> Message[dict[str, Any]]:
        if port != "in":
            return msg
        payload = dict(msg.payload)
        payload.setdefault("normalized", True)
        return Message(type=MessageType.DATA, payload=payload)
