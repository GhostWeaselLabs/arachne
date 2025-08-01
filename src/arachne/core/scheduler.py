from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic, sleep

from .message import Message, MessageType
from .node import Node
from .policies import Block, PutResult
from .priority_queue import NodeProcessor, PriorityQueueConfig, PrioritySchedulingQueue
from .runtime_plan import PriorityBand, RuntimePlan
from .subgraph import Subgraph

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SchedulerConfig:
    """Configuration for the scheduler."""
    tick_interval_ms: int = 50
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 8
    idle_sleep_ms: int = 1
    shutdown_timeout_s: float = 2.0


class Scheduler:
    """Cooperative scheduler for graph execution."""

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self._cfg = config or SchedulerConfig()
        self._graphs: list[Subgraph] = []
        self._running = False
        self._shutdown = False
        
        # Runtime components
        self._plan = RuntimePlan()
        queue_config = PriorityQueueConfig(
            fairness_ratio=self._cfg.fairness_ratio,
            max_batch_per_node=self._cfg.max_batch_per_node
        )
        self._queue = PrioritySchedulingQueue(queue_config)
        self._processor = NodeProcessor(queue_config)
        
        # For runtime mutators before plan is built
        self._pending_priorities: dict[str, PriorityBand] = {}

    def register(self, unit: Node | Subgraph) -> None:
        """Register a node or subgraph for execution."""
        if self._running:
            raise RuntimeError("Cannot register while scheduler is running")
        
        if isinstance(unit, Node):
            g = Subgraph.from_nodes(unit.name, [unit])
            self._graphs.append(g)
        else:
            self._graphs.append(unit)

    def run(self) -> None:
        """Run the scheduler until shutdown is requested."""
        if self._running:
            return
            
        self._running = True
        self._shutdown = False
        
        try:
            # Build runtime plan and connect nodes
            self._plan.build_from_graphs(self._graphs, self._pending_priorities)
            self._plan.connect_nodes_to_scheduler(self)
            
            # Start all nodes
            self._processor.start_all_nodes(self._plan)
            
            # Main scheduling loop
            self._run_main_loop()
                    
        finally:
            # Graceful shutdown
            self._processor.stop_all_nodes(self._plan)
            self._running = False

    def _run_main_loop(self) -> None:
        """Main scheduling loop."""
        loop_start = monotonic()
        
        while not self._shutdown:
            # Update readiness and queue state
            self._plan.update_readiness(self._cfg.tick_interval_ms)
            self._queue.update_from_plan(self._plan)
            
            # Get next runnable node
            runnable = self._queue.get_next_runnable()
            if runnable is None:
                # No work available - check timeout and idle
                if (monotonic() - loop_start) > self._cfg.shutdown_timeout_s:
                    break
                sleep(self._cfg.idle_sleep_ms / 1000.0)
                continue
            
            node_name, priority = runnable
            ready_state = self._plan.ready_states[node_name]
            
            work_done = False
            
            # Process messages first (higher priority)
            if ready_state.message_ready:
                work_done = self._processor.process_node_messages(self._plan, node_name)
            
            # Process tick if no messages or if still tick-ready
            elif ready_state.tick_ready:
                work_done = self._processor.process_node_tick(self._plan, node_name)
            
            if not work_done:
                sleep(self._cfg.idle_sleep_ms / 1000.0)

    def shutdown(self) -> None:
        """Signal scheduler to shutdown gracefully."""
        self._shutdown = True

    def _handle_node_emit(self, node: Node, port: str, message: Message) -> None:
        """Handle node emission with backpressure awareness."""
        node_ref = self._plan.nodes.get(node.name)
        if not node_ref or port not in node_ref.outputs:
            logger.warning(f"Node {node.name} emitted to unknown port {port}")
            return
        
        edge_ref = node_ref.outputs[port]
        edge = edge_ref.edge
        
        # Determine policy - use Block for control messages to ensure delivery
        policy = Block() if message.is_control() else None
        
        try:
            result = edge.try_put(message.payload, policy)
            
            if result == PutResult.BLOCKED:
                # Mark this edge as blocked and reschedule producer later
                ready_state = self._plan.ready_states[node.name]
                ready_state.blocked_edges.add(edge_ref.edge_id)
                logger.debug(f"Edge {edge_ref.edge_id} blocked, rescheduling producer")
                
            elif result == PutResult.DROPPED:
                logger.warning(f"Message dropped on edge {edge_ref.edge_id}")
                
        except Exception as e:
            logger.error(f"Error putting message on edge {edge_ref.edge_id}: {e}")

    def set_priority(self, edge_id: str, priority: int) -> None:
        """Set priority for an edge. Higher values = higher priority."""
        if priority < 1 or priority > 3:
            raise ValueError("Priority must be 1 (normal), 2 (high), or 3 (control)")
        
        priority_band = PriorityBand(priority)
        
        # If runtime plan is built, apply immediately
        if self._plan.edges:
            try:
                self._plan.set_edge_priority(edge_id, priority_band)
                return
            except ValueError:
                pass  # Fall through to graph search
        
        # Otherwise, find the edge in registered graphs
        for graph in self._graphs:
            for edge in graph.edges:
                computed_edge_id = f"{edge.source_node}:{edge.source_port.name}->{edge.target_node}:{edge.target_port.name}"
                if computed_edge_id == edge_id:
                    self._pending_priorities[edge_id] = priority_band
                    logger.debug(f"Scheduled priority {priority} for edge {edge_id}")
                    return
        
        raise ValueError(f"Unknown edge: {edge_id}")

    def set_capacity(self, edge_id: str, capacity: int) -> None:
        """Set capacity for an edge."""
        if capacity <= 0:
            raise ValueError("Capacity must be > 0")
        
        # If runtime plan is built, apply immediately
        if self._plan.edges:
            try:
                self._plan.set_edge_capacity(edge_id, capacity)
                return
            except ValueError:
                pass  # Fall through to graph search
        
        # Otherwise, find the edge in registered graphs
        for graph in self._graphs:
            for edge in graph.edges:
                computed_edge_id = f"{edge.source_node}:{edge.source_port.name}->{edge.target_node}:{edge.target_port.name}"
                if computed_edge_id == edge_id:
                    edge.capacity = capacity
                    logger.debug(f"Set capacity {capacity} for edge {edge_id}")
                    return
        
        raise ValueError(f"Unknown edge: {edge_id}")
