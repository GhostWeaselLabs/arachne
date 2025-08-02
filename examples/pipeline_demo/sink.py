from __future__ import annotations

import time
from typing import Any

from arachne.core.message import Message
from arachne.core.node import Node
from arachne.core.ports import Port, PortDirection, PortSpec


class SlowSink(Node):
    """Simulates I/O latency to trigger backpressure."""

    def __init__(self, delay_s: float = 0.02) -> None:
        super().__init__(name="sink")
        self.delay_s = delay_s
        self.count = 0
        self.inputs = [
            Port(name="in", direction=PortDirection.INPUT, spec=PortSpec("in", dict)),
            Port(name="control", direction=PortDirection.INPUT, spec=PortSpec("control", str)),
        ]

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port == "in":
            time.sleep(self.delay_s)
            self.count += 1
        elif port == "control":
            pass
