from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import NamedTuple

from .edge import Edge
from .node import Node


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

    @classmethod
    def from_nodes(cls, name: str, nodes: Iterable[Node]) -> Subgraph:
        return cls(name=name, nodes={n.name: n for n in nodes})

    def add_node(self, node: Node, name: str | None = None) -> None:
        node_name = name or node.name
        self.nodes[node_name] = node

    def connect(self, src: tuple[str, str], dst: tuple[str, str], capacity: int = 1024) -> str:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        s_node, s_port = src
        d_node, d_port = dst
        sn = self.nodes[s_node]
        dn = self.nodes[d_node]
        s_port_obj = next(p for p in sn.outputs if p.name == s_port)
        d_port_obj = next(p for p in dn.inputs if p.name == d_port)
        edge: Edge[object] = Edge(
            s_node, s_port_obj, d_node, d_port_obj, capacity=capacity, spec=d_port_obj.spec
        )
        self.edges.append(edge)
        return f"{s_node}:{s_port}->{d_node}:{d_port}"

    def expose_input(self, name: str, target: tuple[str, str]) -> None:
        if name in self.exposed_inputs:
            raise ValueError("input already exposed")
        self.exposed_inputs[name] = target

    def expose_output(self, name: str, source: tuple[str, str]) -> None:
        if name in self.exposed_outputs:
            raise ValueError("output already exposed")
        self.exposed_outputs[name] = source

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if len(self.nodes) != len(set(self.nodes.keys())):
            issues.append(ValidationIssue("error", "DUP_NODE", "duplicate node names"))
        seen_edge_ids: set[str] = set()
        for e in self.edges:
            if e.source_node not in self.nodes or e.target_node not in self.nodes:
                issues.append(
                    ValidationIssue("error", "UNKNOWN_NODE", "edge references unknown node")
                )
                continue
            src = self.nodes[e.source_node]
            dst = self.nodes[e.target_node]
            if all(p.name != e.source_port.name for p in src.outputs):
                issues.append(
                    ValidationIssue("error", "NO_SRC_PORT", "src node missing output port")
                )
            if all(p.name != e.target_port.name for p in dst.inputs):
                issues.append(
                    ValidationIssue("error", "NO_DST_PORT", "dst node missing input port")
                )
            if e.capacity <= 0:
                issues.append(ValidationIssue("error", "BAD_CAP", "edge capacity must be > 0"))
            if e.spec is not None and e.target_port.spec is not None:
                if e.target_port.spec.schema is not None:
                    sch = e.target_port.spec.schema
                    _ = sch
            edge_id = f"{e.source_node}:{e.source_port.name}->{e.target_node}:{e.target_port.name}"
            if edge_id in seen_edge_ids:
                issues.append(ValidationIssue("error", "DUP_EDGE", "duplicate edge identifier"))
            seen_edge_ids.add(edge_id)
        if len(self.exposed_inputs) != len(set(self.exposed_inputs.keys())):
            issues.append(
                ValidationIssue("error", "DUP_EXPOSE_IN", "duplicate exposed input names")
            )
        if len(self.exposed_outputs) != len(set(self.exposed_outputs.keys())):
            issues.append(
                ValidationIssue("error", "DUP_EXPOSE_OUT", "duplicate exposed output names")
            )
        for _, (n, p) in self.exposed_inputs.items():
            if n not in self.nodes or all(port.name != p for port in self.nodes[n].inputs):
                issues.append(
                    ValidationIssue(
                        "error",
                        "BAD_EXPOSE_IN",
                        "exposed input references unknown target",
                    )
                )
        for _, (n, p) in self.exposed_outputs.items():
            if n not in self.nodes or all(port.name != p for port in self.nodes[n].outputs):
                issues.append(
                    ValidationIssue(
                        "error",
                        "BAD_EXPOSE_OUT",
                        "exposed output references unknown source",
                    )
                )
        return issues

    def node_names(self) -> list[str]:
        return list(self.nodes.keys())

    def inputs_of(self, node_name: str) -> dict[str, Edge[object]]:
        result: dict[str, Edge[object]] = {}
        for e in self.edges:
            if e.target_node == node_name:
                result[e.target_port.name] = e
        return result
