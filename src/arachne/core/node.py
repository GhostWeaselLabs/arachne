from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .message import Message
from .ports import Port, PortDirection


@dataclass(slots=True)
class Node:
    name: str
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)

    @classmethod
    def with_ports(cls, name: str, input_names: Iterable[str], output_names: Iterable[str]) -> "Node":
        ins = [Port(n, PortDirection.INPUT) for n in input_names]
        outs = [Port(n, PortDirection.OUTPUT) for n in output_names]
        return cls(name=name, inputs=ins, outputs=outs)

    def port_map(self) -> Dict[str, Port]:
        m: Dict[str, Port] = {p.name: p for p in self.inputs + self.outputs}
        return m

    def handle(self, message: Message) -> Message:
        return message
