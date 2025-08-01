from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from .edge import Edge
from .node import Node
from .ports import PortDirection


@dataclass(slots=True)
class Subgraph:
    name: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    @classmethod
    def from_nodes(cls, name: str, nodes: Iterable[Node]) -> "Subgraph":
        return cls(name=name, nodes={n.name: n for n in nodes})

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node

    def connect(self, src: Tuple[str, str], dst: Tuple[str, str], capacity: int = 1024) -> None:
        s_node, s_port = src
        d_node, d_port = dst
        sn = self.nodes[s_node]
        dn = self.nodes[d_node]
        s_port_obj = next(p for p in sn.outputs if p.name == s_port)
        d_port_obj = next(p for p in dn.inputs if p.name == d_port)
        self.edges.append(Edge(s_node, s_port_obj, d_node, d_port_obj, capacity=capacity, spec=d_port_obj.spec))

    def node_names(self) -> List[str]:
        return list(self.nodes.keys())
