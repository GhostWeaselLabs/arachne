from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .edge import Edge
from .node import Node


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

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def node_names(self) -> List[str]:
        return list(self.nodes.keys())
