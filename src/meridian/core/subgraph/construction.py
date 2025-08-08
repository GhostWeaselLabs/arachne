from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import NamedTuple

from ..edge import Edge
from ..node import Node


class ValidationIssue(NamedTuple):
    level: str
    code: str
    message: str


@dataclass
class Subgraph:
    name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge[object]] = field(default_factory=list)
    exposed_inputs: dict[str, tuple[str, str]] = field(default_factory=dict)
    exposed_outputs: dict[str, tuple[str, str]] = field(default_factory=dict)
    _has_duplicate_names: bool = False

    @classmethod
    def from_nodes(cls, name: str, nodes: Iterable[Node]) -> Subgraph:
        return cls(name=name, nodes={n.name: n for n in nodes})

    def add_node(self, node: Node, name: str | None = None) -> None:
        node_name = name or node.name
        if node_name in self.nodes:
            self._has_duplicate_names = True
        self.nodes[node_name] = node

    def connect(
        self,
        src: tuple[str, str],
        dst: tuple[str, str],
        capacity: int = 1024,
        policy: object | None = None,
    ) -> str:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        s_node, s_port = src
        d_node, d_port = dst
        sn = self.nodes[s_node]
        dn = self.nodes[d_node]
        s_port_obj = next(p for p in sn.outputs if p.name == s_port)
        d_port_obj = next(p for p in dn.inputs if p.name == d_port)
        edge: Edge[object] = Edge(
            s_node,
            s_port_obj,
            d_node,
            d_port_obj,
            capacity=capacity,
            spec=d_port_obj.spec,
            default_policy=policy,  # type: ignore[arg-type]
        )
        self.edges.append(edge)
        return f"{s_node}:{s_port}->{d_node}:{d_port}"

    # Keep validation method to preserve behavior used by management/validation helpers
    def validate(self) -> list[ValidationIssue]:
        from .validation import validate

        return validate(self)

    def expose_input(self, name: str, target: tuple[str, str]) -> None:
        if name in self.exposed_inputs:
            raise ValueError("input already exposed")
        self.exposed_inputs[name] = target

    def expose_output(self, name: str, source: tuple[str, str]) -> None:
        if name in self.exposed_outputs:
            raise ValueError("output already exposed")
        self.exposed_outputs[name] = source

    def node_names(self) -> list[str]:
        return list(self.nodes.keys())

    def inputs_of(self, node_name: str) -> dict[str, Edge[object]]:
        result: dict[str, Edge[object]] = {}
        for e in self.edges:
            if e.target_node == node_name:
                result[e.target_port.name] = e
        return result
