"""
Producer Node

Emits a bounded sequence of integers on tick intervals.
Demonstrates tick-based message generation and emit() usage.
"""
from __future__ import annotations

from arachne.core.message import Message, MessageType
from arachne.core.node import Node
from arachne.observability.logging import get_logger, with_context


class ProducerNode(Node):
    """Produces integer messages on tick intervals."""
    
    def __init__(self, name: str, max_count: int = 10, start_value: int = 0):
        """Initialize producer with bounded count and starting value."""
        super().__init__(name=name)
        self.max_count = max_count
        self.current_value = start_value
        self.count_emitted = 0
        self._logger = get_logger()
    
    def on_start(self) -> None:
        """Log producer startup."""
        super().on_start()
        with with_context(node=self.name):
            self._logger.info(
                "producer.start",
                f"Producer starting: will emit {self.max_count} values from {self.current_value}",
                max_count=self.max_count,
                start_value=self.current_value
            )
    
    def _handle_tick(self) -> None:
        """Emit next integer value if under limit."""
        if self.count_emitted >= self.max_count:
            with with_context(node=self.name):
                self._logger.debug(
                    "producer.limit_reached",
                    f"Reached emission limit ({self.max_count}), skipping tick"
                )
            return
        
        # Create data message with current value
        msg = Message(
            type=MessageType.DATA,
            payload=self.current_value,
            metadata={"sequence": self.count_emitted}
        )
        
        # Emit through "output" port
        self.emit("output", msg)
        
        with with_context(node=self.name):
            self._logger.info(
                "producer.emitted",
                f"Emitted value: {self.current_value}",
                value=self.current_value,
                sequence=self.count_emitted
            )
        
        # Update state
        self.current_value += 1
        self.count_emitted += 1
    
    def on_stop(self) -> None:
        """Log producer shutdown stats."""
        super().on_stop()
        with with_context(node=self.name):
            self._logger.info(
                "producer.stop",
                f"Producer stopping: emitted {self.count_emitted} values",
                total_emitted=self.count_emitted
            )
