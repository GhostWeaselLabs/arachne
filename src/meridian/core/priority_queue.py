from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import logging

from .runtime_plan import PriorityBand, RuntimePlan

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PriorityQueueConfig:
    """
    Configuration for priority-based scheduling.

    Parameters:
      fairness_ratio:
        Relative weights for priority bands when selecting runnable nodes.
        Tuple order corresponds to (control, high, normal). Larger values
        increase the share of scheduling opportunities for that band.
      max_batch_per_node:
        Upper bound on how many items a single node may process during one
        scheduling slice. Keeps the loop fair by preventing monopolization.

    Notes:
      - Choose a higher control ratio for responsive control-plane behavior.
      - Reduce max_batch_per_node to favor latency over throughput.
    """

    fairness_ratio: tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 8


class PrioritySchedulingQueue:
    """
    Priority-based scheduling queue with fairness guarantees.

    Responsibilities:
      - Track runnable nodes per PriorityBand (CONTROL, HIGH, NORMAL).
      - Enforce a simple fairness model across bands using configurable ratios.
      - Provide the next runnable node to the scheduler’s main loop.

    Fairness Model (high-level):
      - Each band is assigned a weight via fairness_ratio.
      - The queue prefers CONTROL, then HIGH, then NORMAL respecting weights.
      - When multiple nodes are runnable within a band, the band queue is
        serviced in a FIFO manner to approximate round-robin.

    Notes:
      - This is a cooperative, in-memory mechanism; it assumes relatively
        short work units per node to maintain fairness.
    """

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
        """
        Get next runnable node respecting priority bands and fairness.

        Returns:
          A tuple of (node_name, PriorityBand) or None if no nodes are runnable.

        Behavior:
          - Compute relative ratios per band and attempt to service bands
            proportionally.
          - CONTROL band is preferentially serviced if present.
          - Falls back to any available band if ratio-based selection yields none.

        Note:
          - This fairness is intentionally simple; it aims for approximate
            proportional servicing over time, not strict quotas per timeslice.
        """
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
    """
    Handles node execution with error handling and work batching.

    Responsibilities:
      - Start/stop nodes with error isolation.
      - Process messages for nodes up to max_batch_per_node per slice.
      - Dispatch ticks and update last_tick timestamps.
      - Log and count errors without crashing the scheduler.

    Semantics:
      - Messages are processed with precedence over ticks (scheduler controls
        the order of calls).
      - Message type is derived from the input edge’s priority band:
        CONTROL edges produce MessageType.CONTROL; otherwise MessageType.DATA.
      - Exceptions in node hooks increment error counters and are logged;
        the processor continues with other work to avoid starvation.
    """

    def __init__(self, config: PriorityQueueConfig) -> None:
        self._config = config

    def process_node_messages(self, plan: RuntimePlan, node_name: str) -> bool:
        """
        Process available messages for a node.

        Returns:
          True if at least one message was processed; False otherwise.

        Behavior:
          - Pulls messages from input edges, up to max_batch_per_node.
          - Wraps dequeued payloads into Message envelopes with inferred type.
          - Calls node.on_message(port_name, message) for each processed item.
          - Catches and logs exceptions per-message to continue processing.
        """
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
                    # If producer already enqueued a Message, pass it through unchanged.
                    if isinstance(msg_payload, Message):
                        message = msg_payload
                    else:
                        # Wrap raw payload in Message - infer type based on edge priority
                        msg_type = (
                            MessageType.CONTROL
                            if edge_ref.priority_band == PriorityBand.CONTROL
                            else MessageType.DATA
                        )
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
        """
        Process tick for a node.

        Returns:
          True if a tick was processed successfully; False if an error occurred.

        Behavior:
          - Invokes node.on_tick() and updates the node’s last_tick timestamp.
          - Logs exceptions and increments error counters, but does not abort
            the outer scheduling loop.
        """
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
        """
        Start all nodes with error handling.

        Behavior:
          - Iterates through nodes and invokes on_start().
          - Logs failures per node and increments error counters.
        """
        for node_name, node_ref in plan.nodes.items():
            try:
                node_ref.node.on_start()
                logger.debug(f"Started node {node_name}")
            except Exception as e:
                logger.error(f"Error starting node {node_name}: {e}")
                node_ref.error_count += 1

    def stop_all_nodes(self, plan: RuntimePlan) -> None:
        """
        Stop all nodes in reverse order with error handling.

        Behavior:
          - Invokes on_stop() from last to first to respect potential dependencies.
          - Logs failures per node; continues stopping the rest.
        """
        node_names = list(plan.nodes.keys())
        for node_name in reversed(node_names):
            try:
                plan.nodes[node_name].node.on_stop()
                logger.debug(f"Stopped node {node_name}")
            except Exception as e:
                logger.error(f"Error stopping node {node_name}: {e}")
