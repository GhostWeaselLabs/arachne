from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping

from .message import Message, MessageType
from .ports import Port, PortDirection, PortSpec


@dataclass(slots=True)
class Node:
    name: str
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)

    @classmethod
    def with_ports(
        cls, name: str, input_names: Iterable[str], output_names: Iterable[str]
    ) -> "Node":
        ins = [Port(n, PortDirection.INPUT, spec=PortSpec(n)) for n in input_names]
        outs = [Port(n, PortDirection.OUTPUT, spec=PortSpec(n)) for n in output_names]
        return cls(name=name, inputs=ins, outputs=outs)

    def port_map(self) -> Dict[str, Port]:
        m: Dict[str, Port] = {p.name: p for p in self.inputs + self.outputs}
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
        return msg
