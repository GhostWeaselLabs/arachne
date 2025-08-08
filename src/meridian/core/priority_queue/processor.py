from __future__ import annotations

import logging

from ..runtime_plan import PriorityBand, RuntimePlan
from .config import PriorityQueueConfig

logger = logging.getLogger(__name__)


class NodeProcessor:
    def __init__(self, config: PriorityQueueConfig) -> None:
        self._config = config

    def process_node_messages(self, plan: RuntimePlan, node_name: str) -> bool:
        from ..message import Message, MessageType

        node_ref = plan.nodes[node_name]
        node = node_ref.node
        work_done = False
        messages_processed = 0

        for port_name, edge_ref in node_ref.inputs.items():
            if messages_processed >= self._config.max_batch_per_node:
                break
            edge = edge_ref.edge
            msg_payload = edge.try_get()
            if msg_payload is not None:
                try:
                    if isinstance(msg_payload, Message):
                        message = msg_payload
                    else:
                        msg_type = (
                            MessageType.CONTROL if edge_ref.priority_band == PriorityBand.CONTROL else MessageType.DATA
                        )
                        message = Message(msg_type, msg_payload)
                    node.on_message(port_name, message)
                    work_done = True
                    messages_processed += 1
                except Exception as e:
                    node_ref.error_count += 1
                    logger.error(f"Error in {node.name}.on_message({port_name}): {e}")
        return work_done

    def process_node_tick(self, plan: RuntimePlan, node_name: str) -> bool:
        from time import monotonic

        node_ref = plan.nodes[node_name]
        node = node_ref.node
        try:
            node.on_tick()
            node_ref.last_tick = monotonic()
            return True
        except Exception as e:
            node_ref.error_count += 1
            logger.error(f"Error in {node.name}.on_tick(): {e}")
            return False

    def start_all_nodes(self, plan: RuntimePlan) -> None:
        for node_name, node_ref in plan.nodes.items():
            try:
                node_ref.node.on_start()
                logger.debug(f"Started node {node_name}")
            except Exception as e:
                logger.error(f"Error starting node {node_name}: {e}")
                node_ref.error_count += 1

    def stop_all_nodes(self, plan: RuntimePlan) -> None:
        node_names = list(plan.nodes.keys())
        for node_name in reversed(node_names):
            try:
                plan.nodes[node_name].node.on_stop()
                logger.debug(f"Stopped node {node_name}")
            except Exception as e:
                logger.error(f"Error stopping node {node_name}: {e}")
