from __future__ import annotations

from typing import Any, Callable, Iterable

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class MapTransformer(FunctionNode):
    """Applies a transformation function to each message payload (1:1)."""

    def __init__(
        self,
        name: str,
        transform_fn: Callable[[Any], Any],
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._user_function = transform_fn
        self._in = input_port
        self._out = output_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            result = self._safe_call_user_function(msg.payload, original_message=msg)
            if result is not None:
                self.emit(self._out, Message(MessageType.DATA, result))
        elif msg.type == MessageType.ERROR:
            # Forward errors unchanged
            self.emit(self._out, msg)
        elif msg.type == MessageType.CONTROL:
            self.emit(self._out, msg)


class FilterTransformer(FunctionNode):
    """Filters messages based on a predicate function."""

    def __init__(
        self,
        name: str,
        predicate: Callable[[Any], bool],
        input_port: str = "input",
        output_port: str = "output",
        pass_through_control: bool = True,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._predicate = predicate
        self._in = input_port
        self._out = output_port
        self._pass_ctrl = pass_through_control

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            try:
                if self._predicate(msg.payload):
                    self.emit(self._out, msg)
            except Exception as e:
                # Route error via base policy
                self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
                raise
        elif msg.type == MessageType.ERROR:
            # Forward errors unchanged
            self.emit(self._out, msg)
        elif msg.type == MessageType.CONTROL and self._pass_ctrl:
            self.emit(self._out, msg)


class FlatMapTransformer(FunctionNode):
    """Transforms each input payload into zero or more outputs (1:N)."""

    def __init__(
        self,
        name: str,
        transform_fn: Callable[[Any], Iterable[Any]],
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._user_function = transform_fn
        self._in = input_port
        self._out = output_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            outputs = self._safe_call_user_function(msg.payload, original_message=msg)
            if outputs is None:
                return
            for item in outputs:
                self.emit(self._out, Message(MessageType.DATA, item))
        elif msg.type == MessageType.ERROR:
            self.emit(self._out, msg)
        elif msg.type == MessageType.CONTROL:
            self.emit(self._out, msg)
