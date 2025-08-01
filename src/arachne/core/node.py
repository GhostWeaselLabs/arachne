from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..observability.metrics import Metrics, NoopMetrics
from .message import Message, MessageType
from .ports import Port, PortDirection, PortSpec

if TYPE_CHECKING:
    from .scheduler import Scheduler


@dataclass(slots=True)
class Node:
    name: str
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    _metrics: Metrics = field(default_factory=NoopMetrics, init=False, repr=False)
    _scheduler: Scheduler | None = field(default=None, init=False, repr=False)

    @classmethod
    def with_ports(cls, name: str, input_names: Iterable[str], output_names: Iterable[str]) -> Node:
        ins = [Port(n, PortDirection.INPUT, spec=PortSpec(n)) for n in input_names]
        outs = [Port(n, PortDirection.OUTPUT, spec=PortSpec(n)) for n in output_names]
        return cls(name=name, inputs=ins, outputs=outs)

    def port_map(self) -> dict[str, Port]:
        m: dict[str, Port] = {p.name: p for p in self.inputs + self.outputs}
        return m

    def on_start(self) -> None:
        return None

    def on_message(self, port: str, msg: Message) -> None:
        return None

    def on_tick(self) -> None:
        return None

    def on_stop(self) -> None:
        return None

    def emit(self, port: str, msg: Message) -> Message:
        if msg.type not in (MessageType.DATA, MessageType.CONTROL, MessageType.ERROR):
            raise ValueError("invalid message type")
        if port not in {p.name for p in self.outputs}:
            raise KeyError(f"unknown output port: {port}")
        
        self._metrics.counter("messages_processed_total", {"node": self.name}).inc(1)
        
        # If connected to scheduler, use backpressure-aware emission
        if self._scheduler is not None:
            self._scheduler._handle_node_emit(self, port, msg)
        
        return msg

    def _set_scheduler(self, scheduler: Scheduler) -> None:
        """Internal method used by scheduler to register itself."""
        self._scheduler = scheduler
