from __future__ import annotations

from typing import Any

from ...observability.logging import with_context
from ..message import Message, MessageType
from ..node import Node
from ..policies import Block, PutResult
from ..runtime_plan import RuntimePlan
from .fairness import compute_blocked_count


def is_node_blocked_by_backpressure(plan: RuntimePlan, node_name: str) -> bool:
    ready_state = plan.ready_states.get(node_name)
    return ready_state is not None and len(ready_state.blocked_edges) > 0


def try_unblock_node(plan: RuntimePlan, node_name: str, blocked_nodes_gauge: Any, logger: Any) -> None:
    ready_state = plan.ready_states.get(node_name)
    if ready_state is None or len(ready_state.blocked_edges) == 0:
        return

    edges_to_unblock = set()
    for edge_id in ready_state.blocked_edges:
        edge_ref = plan.edges.get(edge_id)
        if edge_ref and not edge_ref.edge.is_full():
            edges_to_unblock.add(edge_id)
            with with_context(node=node_name, edge_id=edge_id):
                logger.debug(
                    "scheduler.edge_unblocked",
                    f"Edge {edge_id} unblocked, capacity available",
                )

    # Remove unblocked edges
    ready_state.blocked_edges -= edges_to_unblock

    # Update blocked nodes gauge
    blocked_count = compute_blocked_count(plan)
    blocked_nodes_gauge.set(blocked_count)

    if edges_to_unblock:
        logger.debug(
            "scheduler.node_unblocked",
            f"Node {node_name} unblocked on {len(edges_to_unblock)} edges",
            unblocked_edges=list(edges_to_unblock),
        )


def handle_node_emit(plan: RuntimePlan, metrics: Any, node: Node, port: str, msg: Message, logger: Any) -> None:
    """
    Backpressure-aware routing of a node emission.
    Raises RuntimeError on backpressure to signal the node to yield.
    """
    edges = plan.get_outgoing_edges(node.name, port)
    for edge in edges:
        policy = Block() if msg.type == MessageType.CONTROL else edge.default_policy
        result = edge.try_put(msg, policy)

        with with_context(
            node=node.name,
            port=port,
            edge_id=edge._edge_id(),
            message_type=msg.type.value,
        ):
            if result == PutResult.BLOCKED:
                logger.debug("scheduler.backpressure", "Message blocked, applying backpressure")
                source_node_name = node.name
                if source_node_name in plan.ready_states:
                    plan.ready_states[source_node_name].blocked_edges.add(edge._edge_id())

                backpressure_labels = {
                    "source_node": source_node_name,
                    "target_node": edge.target_node,
                    "edge_id": edge._edge_id(),
                }
                metrics.counter("scheduler_backpressure_events_total", backpressure_labels).inc(1)

                raise RuntimeError(
                    f"Backpressure: Edge {edge._edge_id()} is full (capacity: {edge.capacity})"
                )
            elif result == PutResult.DROPPED:
                logger.warn(
                    "scheduler.message_dropped",
                    "Message dropped due to capacity limits",
                    edge_capacity=edge.capacity,
                    edge_size=edge.depth(),
                )
            elif result == PutResult.REPLACED:
                logger.debug(
                    "scheduler.message_replaced",
                    "Message replaced older message",
                    edge_capacity=edge.capacity,
                    edge_size=edge.depth(),
                )
            elif result == PutResult.COALESCED:
                logger.debug(
                    "scheduler.message_coalesced",
                    "Message coalesced with existing message",
                    edge_capacity=edge.capacity,
                    edge_size=edge.depth(),
                )
            else:
                logger.debug(
                    "scheduler.message_routed",
                    f"Message routed successfully: {result.name}",
                    result=result.name,
                    edge_capacity=edge.capacity,
                    edge_size=edge.depth(),
                )
