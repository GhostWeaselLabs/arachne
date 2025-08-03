from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import logging
from time import monotonic
from typing import Any

from .edge import Edge
from .node import Node
from .subgraph import Subgraph

logger = logging.getLogger(__name__)


class PriorityBand(IntEnum):
    """Priority bands for edge scheduling."""

    CONTROL = 3
    HIGH = 2
    NORMAL = 1


@dataclass(slots=True)
class ReadyState:
    """Tracks readiness state for a node."""

    message_ready: bool = False
    tick_ready: bool = False
    blocked_edges: set[str] = field(default_factory=set)


@dataclass(slots=True)
class EdgeRef:
    """Runtime reference to an edge with scheduling metadata."""

    edge: Edge[Any]
    priority_band: PriorityBand = PriorityBand.NORMAL

    @property
    def edge_id(self) -> str:
        """Generate deterministic edge ID."""
        return (
            f"{self.edge.source_node}:{self.edge.source_port.name}->"
            f"{self.edge.target_node}:{self.edge.target_port.name}"
        )


@dataclass(slots=True)
class NodeRef:
    """Runtime reference to a node with scheduling metadata."""

    node: Node
    inputs: dict[str, EdgeRef]
    outputs: dict[str, EdgeRef]
    last_tick: float = 0.0
    error_count: int = 0


class RuntimePlan:
    """
    Execution plan built from registered subgraphs.

    Responsibilities:
      - Materialize nodes and edges from registered Subgraphs into runtime references.
      - Track per-node readiness (messages and ticks) and compute effective priorities.
      - Provide helper operations for priority/capacity mutation and node-scheduler wiring.
      - Support efficient lookups of outgoing edges for routing/emission.

    Notes:
      - Node-ready state is derived each scheduler iteration via update_readiness().
      - Priorities originate from edge metadata; node priority is computed from ready inputs.
    """

    def __init__(self) -> None:
        """Initialize empty runtime state containers."""
        self.nodes: dict[str, NodeRef] = {}
        self.edges: dict[str, EdgeRef] = {}
        self.ready_states: dict[str, ReadyState] = {}

    def clear(self) -> None:
        """Clear the runtime plan."""
        self.nodes.clear()
        self.edges.clear()
        self.ready_states.clear()

    def build_from_graphs(
        self,
        graphs: list[Subgraph],
        pending_priorities: dict[str, PriorityBand] | None = None,
    ) -> None:
        """
        Build the runtime plan from registered subgraphs.

        Parameters:
          graphs:
            Subgraphs previously registered with the scheduler.
          pending_priorities:
            Optional mapping of edge_id to PriorityBand to apply during build.

        Behavior:
          - Validates duplicate node names.
          - Constructs NodeRef and EdgeRef objects and links inputs/outputs.
          - Applies pending edge priorities before finalization.

        Raises:
          ValueError: If duplicate node names are encountered.
        """
        self.clear()
        pending_priorities = pending_priorities or {}

        # Collect all nodes and edges
        for graph in graphs:
            # If the subgraph recorded duplicate adds, surface a consistent error here
            if getattr(graph, "_has_duplicate_names", False):
                raise ValueError("Duplicate node name: subgraph recorded duplicate additions")

            # Detect duplicate node names within the same subgraph before adding
            seen_in_graph: set[str] = set()
            for key, node in graph.nodes.items():
                # Detect duplicates within the same subgraph by dict key (supports add_node duplicates)
                if key in seen_in_graph:
                    raise ValueError(f"Duplicate node name: {key}")
                seen_in_graph.add(key)

                # Detect duplicates across already-added graphs by node name
                if node.name in self.nodes:
                    raise ValueError(f"Duplicate node name: {node.name}")

                node_ref = NodeRef(node=node, inputs={}, outputs={}, last_tick=monotonic())
                self.nodes[node.name] = node_ref
                self.ready_states[node.name] = ReadyState()

            for edge in graph.edges:
                edge_ref = EdgeRef(edge=edge)
                edge_id = edge_ref.edge_id

                # Apply any pending priorities
                if edge_id in pending_priorities:
                    edge_ref.priority_band = pending_priorities[edge_id]

                self.edges[edge_id] = edge_ref

                # Link edges to nodes
                if edge.source_node in self.nodes:
                    self.nodes[edge.source_node].outputs[edge.source_port.name] = edge_ref
                if edge.target_node in self.nodes:
                    self.nodes[edge.target_node].inputs[edge.target_port.name] = edge_ref

    def update_readiness(self, tick_interval_ms: int) -> None:
        """
        Update per-node readiness for messages and ticks.

        Parameters:
          tick_interval_ms:
            Milliseconds after which a node becomes tick-ready if it has not ticked.

        Behavior:
          - message_ready: True if any input edge has depth > 0.
          - tick_ready: True if time since last_tick exceeds tick_interval_ms.
        """
        current_time = monotonic()

        for node_name, node_ref in self.nodes.items():
            ready_state = self.ready_states[node_name]

            # Check message readiness
            ready_state.message_ready = any(
                edge_ref.edge.depth() > 0 for edge_ref in node_ref.inputs.values()
            )

            # Check tick readiness
            time_since_tick = (current_time - node_ref.last_tick) * 1000.0
            ready_state.tick_ready = time_since_tick >= tick_interval_ms

    def get_node_priority(self, node_name: str) -> PriorityBand:
        """
        Compute the effective priority for a node.

        Rules:
          - If message_ready: use the highest PriorityBand among ready input edges.
          - Else if tick_ready: NORMAL priority.
          - Else: NORMAL priority.

        Returns:
          PriorityBand for scheduling the node.
        """
        node_ref = self.nodes[node_name]
        ready_state = self.ready_states[node_name]

        if ready_state.message_ready:
            # Node priority is highest priority of ready input edges
            return max(
                (
                    edge_ref.priority_band
                    for edge_ref in node_ref.inputs.values()
                    if edge_ref.edge.depth() > 0
                ),
                default=PriorityBand.NORMAL,
            )
        elif ready_state.tick_ready:
            return PriorityBand.NORMAL

        return PriorityBand.NORMAL

    def is_node_ready(self, node_name: str) -> bool:
        """Return True if the node is ready to run (messages or tick)."""
        ready_state = self.ready_states[node_name]
        return ready_state.message_ready or ready_state.tick_ready

    def set_edge_priority(self, edge_id: str, priority_band: PriorityBand) -> None:
        """
        Set the priority band for an edge in the runtime plan.

        Raises:
          ValueError: If the edge_id is unknown.
        """
        if edge_id not in self.edges:
            raise ValueError(f"Unknown edge: {edge_id}")

        self.edges[edge_id].priority_band = priority_band
        logger.debug(f"Set priority {priority_band} for edge {edge_id}")

    def set_edge_capacity(self, edge_id: str, capacity: int) -> None:
        """
        Set capacity for an edge in the runtime plan.

        Raises:
          ValueError: If the edge_id is unknown or capacity <= 0.
        """
        if edge_id not in self.edges:
            raise ValueError(f"Unknown edge: {edge_id}")

        if capacity <= 0:
            raise ValueError("Capacity must be > 0")

        self.edges[edge_id].edge.capacity = capacity
        logger.debug(f"Set capacity {capacity} for edge {edge_id}")

    def connect_nodes_to_scheduler(self, scheduler: Any) -> None:
        """Connect all nodes to the scheduler for backpressure-aware emission."""
        for node_ref in self.nodes.values():
            node_ref.node._set_scheduler(scheduler)

    def get_outgoing_edges(self, node_name: str, port_name: str) -> list[Any]:
        """
        Get outgoing edges for a specific node and port.

        Returns:
          List of Edge instances whose source matches (node_name, port_name).
        """
        edges = []
        for edge_ref in self.edges.values():
            if (
                edge_ref.edge.source_node == node_name
                and edge_ref.edge.source_port.name == port_name
            ):
                edges.append(edge_ref.edge)
        return edges
