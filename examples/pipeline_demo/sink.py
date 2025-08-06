from __future__ import annotations

import time
from typing import Any

from meridian.core import Message, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class SlowSink(Node):
    """Simulates I/O latency to trigger backpressure."""

    def __init__(self, delay_s: float = 0.02) -> None:
        super().__init__(
            name="sink",
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", dict)),
                Port("control", PortDirection.INPUT, spec=PortSpec("control", str)),
            ],
            outputs=[],
        )
        self.delay_s = delay_s
        self.count = 0

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port == "in":
            time.sleep(self.delay_s)
            self.count += 1
        elif port == "control":
            pass
