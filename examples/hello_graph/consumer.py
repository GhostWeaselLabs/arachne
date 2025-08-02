from __future__ import annotations

from arachne.core.message import Message
from arachne.core.ports import Port, PortDirection, PortSpec
from arachne.core.node import Node


class Consumer(Node):
    def __init__(self) -> None:
        super().__init__(name="consumer")
        self.values: list[int] = []
        # define single input port "in"
        self.inputs = [Port(name="in", direction=PortDirection.INPUT, spec=PortSpec("in", int))]

    def _handle_message(self, port: str, msg: Message[int]) -> None:
        if port != "in":
            return
        self.values.append(msg.payload)
        print(msg.payload)
