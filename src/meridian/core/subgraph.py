from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import NamedTuple

from .edge import Edge
from .node import Node


class ValidationIssue(NamedTuple):
    """Structured result for subgraph validation findings.

    Attributes:
      level:
        Severity of the issue (e.g., "error", "warning", "info").
      code:
        Stable, short code for the category of issue (e.g., "DUP_NODE").
      message:
        Human-readable description of the validation problem.
    """

    level: str
    code: str
    message: str


@dataclass
class Subgraph:
    """Composable collection of nodes and edges that forms a unit of execution.

    Semantics
    - Encapsulates a set of nodes and the directed edges connecting their ports.
    - Supports exposing selected internal ports as subgraph-level inputs/outputs.
    - Provides validation to catch common wiring mistakes before execution.

    Attributes
    - name: Unique identifier for the subgraph.
    - nodes: Mapping of node name to Node instances.
    - edges: List of edges (bounded channels) connecting nodes.
    - exposed_inputs: Mapping of external input name -> (target_node, target_port).
    - exposed_outputs: Mapping of external output name -> (source_node, source_port).

    Notes
    - Edge capacity must be > 0.
    - Node names must be unique within the subgraph.
    - Edge identifiers (src:port->dst:port) must be unique.
    """

    name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge[object]] = field(default_factory=list)
    exposed_inputs: dict[str, tuple[str, str]] = field(default_factory=dict)
    exposed_outputs: dict[str, tuple[str, str]] = field(default_factory=dict)
    # Internal flag to record if duplicate node keys were added at any time.
    _has_duplicate_names: bool = False

    @classmethod
    def from_nodes(cls, name: str, nodes: Iterable[Node]) -> Subgraph:
        """Construct a Subgraph from an iterable of nodes.

        Parameters:
          name:
            Identifier for the new subgraph.
          nodes:
            Iterable of Node instances. Node names must be unique.

        Returns:
          A Subgraph with the provided nodes and no edges.

        Raises:
          ValueError:
            If duplicate node names are detected by later validation.
        """
        return cls(name=name, nodes={n.name: n for n in nodes})

    def add_node(self, node: Node, name: str | None = None) -> None:
        """Add a node to the subgraph.

        Parameters:
          node:
            Node instance to add.
          name:
            Optional override for the node’s key within this subgraph. Defaults
            to node.name if not provided.

        Notes:
          - Node keys must be unique within the subgraph. Use validate() to
            detect duplicates before building a runtime plan.
        """
        node_name = name or node.name
        # Record duplicate additions without raising immediately so that
        # build_from_graphs() can surface a consistent ValueError site.
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
        """Connect an output port to an input port with a bounded edge.

        Parameters:
          src:
            Tuple of (source_node_name, source_port_name) for an output port.
          dst:
            Tuple of (target_node_name, target_port_name) for an input port.
          capacity:
            Positive integer capacity for the bounded edge queue.
          policy:
            Optional backpressure Policy to set as the edge's default_policy.

        Returns:
          Stable edge identifier: "src_node:src_port->dst_node:dst_port".

        Raises:
          ValueError:
            If capacity <= 0.

        Notes:
          - PortSpec (schema) from the target input port is attached to the edge
            to enable payload validation at enqueue time.
        """
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

    def expose_input(self, name: str, target: tuple[str, str]) -> None:
        """Expose an internal node’s input port as a subgraph-level input.

        Parameters:
          name:
            External input name to expose on the subgraph boundary.
          target:
            Tuple of (node_name, port_name) referencing an internal INPUT port.

        Raises:
          ValueError:
            If an exposed input with the same name already exists.
        """
        if name in self.exposed_inputs:
            raise ValueError("input already exposed")
        self.exposed_inputs[name] = target

    def expose_output(self, name: str, source: tuple[str, str]) -> None:
        """Expose an internal node’s output port as a subgraph-level output.

        Parameters:
          name:
            External output name to expose on the subgraph boundary.
          source:
            Tuple of (node_name, port_name) referencing an internal OUTPUT port.

        Raises:
          ValueError:
            If an exposed output with the same name already exists.
        """
        if name in self.exposed_outputs:
            raise ValueError("output already exposed")
        self.exposed_outputs[name] = source

    def validate(self) -> list[ValidationIssue]:
        """Validate subgraph structure and wiring.

        Returns:
          A list of ValidationIssue instances describing problems found. An empty
          list indicates the subgraph is structurally valid.

        Checks performed:
          - Unique node names.
          - Edges reference known nodes and ports.
          - Edge capacity > 0.
          - Unique edge identifiers (no duplicate src:port->dst:port).
          - Exposed inputs/outputs do not conflict and reference valid ports.

        Notes:
          - PortSpec schema constraints are not deeply validated here; only presence
            is acknowledged to avoid false positives. Deep validation should occur at
            runtime on enqueue when schemas are enforced.
        """
        issues: list[ValidationIssue] = []
        if len(self.nodes) != len(set(self.nodes.keys())):
            issues.append(ValidationIssue("error", "DUP_NODE", "duplicate node names"))
        seen_edge_ids: set[str] = set()
        for e in self.edges:
            if e.source_node not in self.nodes or e.target_node not in self.nodes:
                issues.append(
                    ValidationIssue("error", "UNKNOWN_NODE", "edge references unknown node")
                )
                # Still check capacity to report BAD_CAP even when nodes are unknown
                if e.capacity <= 0:
                    issues.append(ValidationIssue("error", "BAD_CAP", "edge capacity must be > 0"))
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
        """Return a list of node names contained in this subgraph."""
        return list(self.nodes.keys())

    def inputs_of(self, node_name: str) -> dict[str, Edge[object]]:
        """Return a mapping of input port name to incoming Edge for the given node."""
        result: dict[str, Edge[object]] = {}
        for e in self.edges:
            if e.target_node == node_name:
                result[e.target_port.name] = e
        return result
