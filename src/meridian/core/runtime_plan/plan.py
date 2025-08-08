from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import logging
from time import monotonic
from typing import Any

from ..edge import Edge
from ..node import Node
from ..subgraph import Subgraph

logger = logging.getLogger(__name__)


class PriorityBand(IntEnum):
    CONTROL = 3
    HIGH = 2
    NORMAL = 1


@dataclass(slots=True)
class ReadyState:
    message_ready: bool = False
    tick_ready: bool = False
    blocked_edges: set[str] = field(default_factory=set)


@dataclass(slots=True)
class EdgeRef:
    edge: Edge[Any]
    priority_band: PriorityBand = PriorityBand.NORMAL

    @property
    def edge_id(self) -> str:
        return f"{self.edge.source_node}:{self.edge.source_port.name}->{self.edge.target_node}:{self.edge.target_port.name}"


@dataclass(slots=True)
class NodeRef:
    node: Node
    inputs: dict[str, EdgeRef]
    outputs: dict[str, EdgeRef]
    last_tick: float = 0.0
    error_count: int = 0


class RuntimePlan:
    def __init__(self) -> None:
        self.nodes: dict[str, NodeRef] = {}
        self.edges: dict[str, EdgeRef] = {}
        self.ready_states: dict[str, ReadyState] = {}

    def clear(self) -> None:
        self.nodes.clear()
        self.edges.clear()
        self.ready_states.clear()

    def build_from_graphs(
        self,
        graphs: list[Subgraph],
        pending_priorities: dict[str, PriorityBand] | None = None,
    ) -> None:
        self.clear()
        pending_priorities = pending_priorities or {}
        for graph in graphs:
            if getattr(graph, "_has_duplicate_names", False):
                raise ValueError("Duplicate node name: subgraph recorded duplicate additions")
            seen_in_graph: set[str] = set()
            for key, node in graph.nodes.items():
                if key in seen_in_graph:
                    raise ValueError(f"Duplicate node name: {key}")
                seen_in_graph.add(key)
                if node.name in self.nodes:
                    raise ValueError(f"Duplicate node name: {node.name}")
                node_ref = NodeRef(node=node, inputs={}, outputs={}, last_tick=monotonic())
                self.nodes[node.name] = node_ref
                self.ready_states[node.name] = ReadyState()
            for edge in graph.edges:
                edge_ref = EdgeRef(edge=edge)
                edge_id = edge_ref.edge_id
                if edge_id in pending_priorities:
                    edge_ref.priority_band = pending_priorities[edge_id]
                self.edges[edge_id] = edge_ref
                if edge.source_node in self.nodes:
                    self.nodes[edge.source_node].outputs[edge.source_port.name] = edge_ref
                if edge.target_node in self.nodes:
                    self.nodes[edge.target_node].inputs[edge.target_port.name] = edge_ref

    def update_readiness(self, tick_interval_ms: int) -> None:
        current_time = monotonic()
        for node_name, node_ref in self.nodes.items():
            ready_state = self.ready_states[node_name]
            ready_state.message_ready = any(edge_ref.edge.depth() > 0 for edge_ref in node_ref.inputs.values())
            time_since_tick = (current_time - node_ref.last_tick) * 1000.0
            ready_state.tick_ready = time_since_tick >= tick_interval_ms

    def get_node_priority(self, node_name: str) -> PriorityBand:
        node_ref = self.nodes[node_name]
        ready_state = self.ready_states[node_name]
        if ready_state.message_ready:
            return max(
                (edge_ref.priority_band for edge_ref in node_ref.inputs.values() if edge_ref.edge.depth() > 0),
                default=PriorityBand.NORMAL,
            )
        elif ready_state.tick_ready:
            return PriorityBand.NORMAL
        return PriorityBand.NORMAL

    def is_node_ready(self, node_name: str) -> bool:
        ready_state = self.ready_states[node_name]
        return ready_state.message_ready or ready_state.tick_ready

    def set_edge_priority(self, edge_id: str, priority_band: PriorityBand) -> None:
        if edge_id not in self.edges:
            raise ValueError(f"Unknown edge: {edge_id}")
        self.edges[edge_id].priority_band = priority_band
        logger.debug(f"Set priority {priority_band} for edge {edge_id}")

    def set_edge_capacity(self, edge_id: str, capacity: int) -> None:
        if edge_id not in self.edges:
            raise ValueError(f"Unknown edge: {edge_id}")
        if capacity <= 0:
            raise ValueError("Capacity must be > 0")
        self.edges[edge_id].edge.capacity = capacity
        logger.debug(f"Set capacity {capacity} for edge {edge_id}")

    def connect_nodes_to_scheduler(self, scheduler: Any) -> None:
        for node_ref in self.nodes.values():
            node_ref.node._set_scheduler(scheduler)

    def get_outgoing_edges(self, node_name: str, port_name: str) -> list[Any]:
        edges = []
        for edge_ref in self.edges.values():
            if edge_ref.edge.source_node == node_name and edge_ref.edge.source_port.name == port_name:
                edges.append(edge_ref.edge)
        return edges
