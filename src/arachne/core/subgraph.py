from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .edge import Edge
from .node import Node


@dataclass(slots=True)
class Subgraph:
    name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge[object]] = field(default_factory=list)
    exposed_inputs: dict[str, tuple[str, str]] = field(default_factory=dict)
    exposed_outputs: dict[str, tuple[str, str]] = field(default_factory=dict)

    @classmethod
    def from_nodes(cls, name: str, nodes: Iterable[Node]) -> Subgraph:
        return cls(name=name, nodes={n.name: n for n in nodes})

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node

    def connect(self, src: tuple[str, str], dst: tuple[str, str], capacity: int = 1024) -> None:
        s_node, s_port = src
        d_node, d_port = dst
        sn = self.nodes[s_node]
        dn = self.nodes[d_node]
        s_port_obj = next(p for p in sn.outputs if p.name == s_port)
        d_port_obj = next(p for p in dn.inputs if p.name == d_port)
        self.edges.append(
            Edge(
                s_node,
                s_port_obj,
                d_node,
                d_port_obj,
                capacity=capacity,
                spec=d_port_obj.spec,
            )
        )

    def expose_input(self, name: str, target: tuple[str, str]) -> None:
        if name in self.exposed_inputs:
            raise ValueError("input already exposed")
        self.exposed_inputs[name] = target

    def expose_output(self, name: str, source: tuple[str, str]) -> None:
        if name in self.exposed_outputs:
            raise ValueError("output already exposed")
        self.exposed_outputs[name] = source

    def validate(self) -> list[str]:
        issues: list[str] = []
        if len(self.nodes) != len(set(self.nodes.keys())):
            issues.append("duplicate node names")
        for e in self.edges:
            if e.source_node not in self.nodes or e.target_node not in self.nodes:
                issues.append("edge references unknown node")
        for _, (n, p) in self.exposed_inputs.items():
            if n not in self.nodes or all(port.name != p for port in self.nodes[n].inputs):
                issues.append("exposed input references unknown target")
        for _, (n, p) in self.exposed_outputs.items():
            if n not in self.nodes or all(port.name != p for port in self.nodes[n].outputs):
                issues.append("exposed output references unknown source")
        return issues

    def node_names(self) -> list[str]:
        return list(self.nodes.keys())
