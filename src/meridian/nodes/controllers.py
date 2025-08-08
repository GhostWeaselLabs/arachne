from __future__ import annotations

from typing import Any, Callable

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class Router(FunctionNode):
    """Routes messages to different output ports based on routing logic."""

    def __init__(
        self,
        name: str,
        routing_fn: Callable[[Any], str],
        output_ports: list[str],
        input_port: str = "input",
        default_port: str | None = None,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], output_ports)
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._route = routing_fn
        self._in = input_port
        self._outputs = set(output_ports)
        self._default = default_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            try:
                dest = self._route(msg.payload)
            except Exception:
                # On routing error, drop or send to default if configured
                dest = self._default
            if dest in self._outputs:
                self.emit(dest, msg)
            elif self._default is not None and self._default in self._outputs:
                self.emit(self._default, msg)
            else:
                # No valid destination; drop silently
                return
        else:
            # Forward CONTROL/ERROR to all outputs for propagation
            for p in self._outputs:
                self.emit(p, msg)


class Merger(FunctionNode):
    """Merges messages from multiple input ports into a single output.

    Note: The scheduler's fairness determines interleaving across inputs.
    """

    def __init__(
        self,
        name: str,
        input_ports: list[str],
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(input_ports, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._inputs = set(input_ports)
        self._out = output_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port not in self._inputs:
            return
        # Re-emit to single output; preserve ordering within each input by not buffering
        self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        # No periodic work required
        return


class Splitter(FunctionNode):
    """Duplicates messages to multiple output ports with optional per-port filtering."""

    def __init__(
        self,
        name: str,
        output_ports: list[str],
        input_port: str = "input",
        port_filters: dict[str, Callable[[Any], bool]] | None = None,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], output_ports)
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._outputs = list(output_ports)
        self._filters = port_filters or {}

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            for p in self._outputs:
                pred = self._filters.get(p)
                if pred is None or _safe_predicate(pred, msg.payload):
                    self.emit(p, msg)
        else:
            # Broadcast control/error to all
            for p in self._outputs:
                self.emit(p, msg)


def _safe_predicate(pred: Callable[[Any], bool], value: Any) -> bool:
    try:
        return bool(pred(value))
    except Exception:
        return False
