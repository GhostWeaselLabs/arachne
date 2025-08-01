from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass

from .runtime_plan import PriorityBand, RuntimePlan

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PriorityQueueConfig:
    """Configuration for priority-based scheduling."""
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 8


class PrioritySchedulingQueue:
    """Priority-based scheduling queue with fairness guarantees."""
    
    def __init__(self, config: PriorityQueueConfig) -> None:
        self._config = config
        self._ready_queues: dict[PriorityBand, deque[str]] = {
            PriorityBand.CONTROL: deque(),
            PriorityBand.HIGH: deque(),
            PriorityBand.NORMAL: deque(),
        }
        self._round_robin_state: dict[PriorityBand, int] = defaultdict(int)
    
    def clear(self) -> None:
        """Clear all queues."""
        for queue in self._ready_queues.values():
            queue.clear()
        self._round_robin_state.clear()
    
    def enqueue_runnable(self, node_name: str, priority: PriorityBand) -> None:
        """Add node to appropriate priority queue if not already queued."""
        # Remove from all queues first to avoid duplicates
        for queue in self._ready_queues.values():
            if node_name in queue:
                queue.remove(node_name)
        
        # Add to appropriate priority queue
        self._ready_queues[priority].append(node_name)
    
    def get_next_runnable(self) -> tuple[str, PriorityBand] | None:
        """Get next runnable node respecting priority bands and fairness."""
        # Check bands in priority order with fairness ratios
        ratios = {
            PriorityBand.CONTROL: self._config.fairness_ratio[0],
            PriorityBand.HIGH: self._config.fairness_ratio[1], 
            PriorityBand.NORMAL: self._config.fairness_ratio[2],
        }
        
        # Simple fairness: cycle through bands based on their ratios
        total_ratio = sum(ratios.values())
        current_tick = sum(len(q) for q in self._ready_queues.values())
        
        for band in [PriorityBand.CONTROL, PriorityBand.HIGH, PriorityBand.NORMAL]:
            queue = self._ready_queues[band]
            if not queue:
                continue
                
            # Check if this band should run based on fairness ratio
            band_ratio = ratios[band] / total_ratio if total_ratio > 0 else 0
            if current_tick % total_ratio < band_ratio * total_ratio:
                return queue.popleft(), band
            
            # Always service control plane if available
            if band == PriorityBand.CONTROL and queue:
                return queue.popleft(), band
        
        # Fallback: service any available node
        for band, queue in self._ready_queues.items():
            if queue:
                return queue.popleft(), band
        
        return None
    
    def update_from_plan(self, plan: RuntimePlan) -> None:
        """Update queues based on runtime plan readiness."""
        for node_name in plan.nodes:
            if plan.is_node_ready(node_name):
                priority = plan.get_node_priority(node_name)
                self.enqueue_runnable(node_name, priority)
    
    def has_runnable_nodes(self) -> bool:
        """Check if any nodes are ready to run."""
        return any(queue for queue in self._ready_queues.values())
    
    def get_queue_depths(self) -> dict[PriorityBand, int]:
        """Get current queue depths for observability."""
        return {band: len(queue) for band, queue in self._ready_queues.items()}


class NodeProcessor:
    """Handles node execution with error handling and work batching."""
    
    def __init__(self, config: PriorityQueueConfig) -> None:
        self._config = config
    
    def process_node_messages(self, plan: RuntimePlan, node_name: str) -> bool:
        """Process available messages for a node. Returns True if work was done."""
        from .message import Message, MessageType
        
        node_ref = plan.nodes[node_name]
        node = node_ref.node
        work_done = False
        messages_processed = 0
        
        # Process up to max_batch_per_node messages
        for port_name, edge_ref in node_ref.inputs.items():
            if messages_processed >= self._config.max_batch_per_node:
                break
                
            edge = edge_ref.edge
            msg_payload = edge.try_get()
            
            if msg_payload is not None:
                try:
                    # Wrap payload in Message - infer type based on edge priority
                    msg_type = MessageType.CONTROL if edge_ref.priority_band == PriorityBand.CONTROL else MessageType.DATA
                    message = Message(msg_type, msg_payload)
                    
                    node.on_message(port_name, message)
                    work_done = True
                    messages_processed += 1
                    
                except Exception as e:
                    node_ref.error_count += 1
                    logger.error(f"Error in {node.name}.on_message({port_name}): {e}")
                    # Continue processing other messages
        
        return work_done
    
    def process_node_tick(self, plan: RuntimePlan, node_name: str) -> bool:
        """Process tick for a node. Returns True if work was done."""
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
        """Start all nodes with error handling."""
        for node_name, node_ref in plan.nodes.items():
            try:
                node_ref.node.on_start()
                logger.debug(f"Started node {node_name}")
            except Exception as e:
                logger.error(f"Error starting node {node_name}: {e}")
                node_ref.error_count += 1
    
    def stop_all_nodes(self, plan: RuntimePlan) -> None:
        """Stop all nodes in reverse order with error handling."""
        node_names = list(plan.nodes.keys())
        for node_name in reversed(node_names):
            try:
                plan.nodes[node_name].node.on_stop()
                logger.debug(f"Stopped node {node_name}")
            except Exception as e:
                logger.error(f"Error stopping node {node_name}: {e}") 