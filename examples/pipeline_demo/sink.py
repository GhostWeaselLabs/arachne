from __future__ import annotations

import time
from typing import Any

from arachne.core.message import Message


class SlowSink:
    """Simulates I/O latency to trigger backpressure."""

    def __init__(self, delay_s: float = 0.02) -> None:
        self.delay_s = delay_s
        self.count = 0

    def on_message(self, port: str, msg: Message[dict[str, Any]]) -> None:
        if port != "in":
            return
        time.sleep(self.delay_s)
        self.count += 1
