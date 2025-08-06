"""
Producer Node

Emits a bounded sequence of integers on tick intervals.
Demonstrates tick-based message generation and emit() usage.
"""

from __future__ import annotations

from meridian.core import Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection
from meridian.observability.logging import get_logger, with_context


class ProducerNode(Node):
    """Produces integer messages on tick intervals."""

    def __init__(self, name: str, max_count: int = 10, start_value: int = 0):
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("output", PortDirection.OUTPUT, spec=PortSpec("output", int))],
        )
        self.max_count = max_count
        self.current_value = start_value
        self.count_emitted = 0
        self._logger = get_logger()

    def on_start(self) -> None:
        super().on_start()
        with with_context(node=self.name):
            self._logger.info(
                "producer.start",
                (
                    f"Producer starting: will emit {self.max_count} "
                    f"values from {self.current_value}"
                ),
                max_count=self.max_count,
                start_value=self.current_value,
            )

    def _handle_tick(self) -> None:
        if self.count_emitted >= self.max_count:
            with with_context(node=self.name):
                self._logger.debug(
                    "producer.limit_reached",
                    f"Reached emission limit ({self.max_count}), skipping tick",
                )
            return

        msg = Message(
            type=MessageType.DATA,
            payload=self.current_value,
            metadata={"sequence": self.count_emitted},
        )
        self.emit("output", msg)

        with with_context(node=self.name):
            self._logger.info(
                "producer.emitted",
                f"Emitted value: {self.current_value}",
                value=self.current_value,
                sequence=self.count_emitted,
            )

        self.current_value += 1
        self.count_emitted += 1

    def on_stop(self) -> None:
        super().on_stop()
        with with_context(node=self.name):
            self._logger.info(
                "producer.stop",
                f"Producer stopping: emitted {self.count_emitted} values",
                total_emitted=self.count_emitted,
            )
