from __future__ import annotations

from meridian.core import Message, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Consumer(Node):
    def __init__(self) -> None:
        super().__init__(
            name="consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
        self.values: list[int] = []

    def _handle_message(self, port: str, msg: Message[int]) -> None:
        if port != "in":
            return
        self.values.append(msg.payload)
        print(msg.payload)
