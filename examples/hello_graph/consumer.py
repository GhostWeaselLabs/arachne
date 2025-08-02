from __future__ import annotations

from arachne.core.message import Message


class Consumer:
    """
    Prints or records incoming integer payloads.

    Ports:
      in:int
    """

    def __init__(self) -> None:
        self.values: list[int] = []

    def on_message(self, port: str, msg: Message[int]) -> None:
        if port != "in":
            return
        self.values.append(msg.payload)
        print(msg.payload)
