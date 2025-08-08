from __future__ import annotations

from typing import Any, Callable

from .base import ErrorPolicy, FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class DataConsumer(FunctionNode):
    """Consumes individual data messages using a user-provided handler."""

    def __init__(
        self,
        name: str,
        handler: Callable[[Any], None],
        input_port: str = "input",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], None)
        super().__init__(name, inputs=ins, outputs=outs or [], config=config)
        self._user_function = handler
        self._in = input_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            self._safe_call_user_function(msg.payload, original_message=msg)
        elif msg.type in (MessageType.CONTROL, MessageType.ERROR):
            # Default behavior: no-op (forwarding is up to graph wiring)
            pass


class BatchConsumer(FunctionNode):
    """Accumulates messages into batches before processing."""

    def __init__(
        self,
        name: str,
        batch_handler: Callable[[list[Any]], None],
        batch_size: int = 10,
        input_port: str = "input",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], None)
        super().__init__(name, inputs=ins, outputs=outs or [], config=config)
        self._user_function = batch_handler
        self._in = input_port
        self._batch_size = max(1, int(batch_size))
        self._batch: list[Any] = []

    def _flush(self) -> None:
        if self._batch:
            self._safe_call_user_function(list(self._batch))
            self._batch.clear()

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            self._batch.append(msg.payload)
            if len(self._batch) >= self._batch_size:
                self._flush()
        elif msg.type == MessageType.CONTROL:
            # Flush any pending work on control completion
            self._flush()
        elif msg.type == MessageType.ERROR:
            # Default: log via policy and continue
            self._safe_call_user_function(None)  # invoke for side effects; handler should tolerate None
