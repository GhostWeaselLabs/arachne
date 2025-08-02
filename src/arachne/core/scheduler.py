from __future__ import annotations

from dataclasses import dataclass
import time
from time import monotonic, sleep

from ..observability.logging import get_logger, with_context
from ..observability.metrics import get_metrics, time_block
from ..observability.tracing import start_span
from .message import Message, MessageType
from .node import Node
from .policies import Block, PutResult
from .priority_queue import NodeProcessor, PriorityQueueConfig, PrioritySchedulingQueue
from .runtime_plan import PriorityBand, RuntimePlan
from .subgraph import Subgraph


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
            fairness_ratio=self._cfg.fairness_ratio, max_batch_per_node=self._cfg.max_batch_per_node
        )
        self._queue = PrioritySchedulingQueue(queue_config)
        self._processor = NodeProcessor(queue_config)

        # For runtime mutators before plan is built
        self._pending_priorities: dict[str, PriorityBand] = {}

        # Observability
        self._metrics = get_metrics()
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize scheduler metrics."""
        self._runnable_nodes_gauge = self._metrics.gauge("scheduler_runnable_nodes")
        self._loop_latency_histogram = self._metrics.histogram("scheduler_loop_latency_seconds")
        self._priority_applied_counter = self._metrics.counter("scheduler_priority_applied_total")

    def register(self, unit: Node | Subgraph) -> None:
        """Register a node or subgraph for execution."""
        logger = get_logger()

        if self._running:
            raise RuntimeError("Cannot register while scheduler is running")

        if isinstance(unit, Node):
            g = Subgraph.from_nodes(unit.name, [unit])
            self._graphs.append(g)
            logger.debug("scheduler.register_node", f"Registered node {unit.name}")
        else:
            self._graphs.append(unit)
            logger.debug("scheduler.register_subgraph", f"Registered subgraph {unit.name}")

    def run(self) -> None:
        """Run the scheduler until shutdown is requested."""
        logger = get_logger()

        if self._running:
            return

        self._running = True
        self._shutdown = False

        logger.info(
            "scheduler.start",
            "Scheduler starting",
            graphs_count=len(self._graphs),
            tick_interval_ms=self._cfg.tick_interval_ms,
        )

        try:
            # Build runtime plan and connect nodes
            with time_block("scheduler_build_time_seconds"):
                self._plan.build_from_graphs(self._graphs, self._pending_priorities)
                self._plan.connect_nodes_to_scheduler(self)

            # Start all nodes
            with time_block("scheduler_startup_time_seconds"):
                self._processor.start_all_nodes(self._plan)

            logger.info(
                "scheduler.ready",
                "Scheduler ready, entering main loop",
                nodes_count=len(self._plan.nodes),
            )

            # Main scheduling loop
            self._run_main_loop()

        except Exception as e:
            logger.error(
                "scheduler.error",
                f"Scheduler error: {e}",
                error_type=type(e).__name__,
                error_msg=str(e),
            )
            raise
        finally:
            # Graceful shutdown
            logger.info("scheduler.shutdown_start", "Starting graceful shutdown")

            with time_block("scheduler_shutdown_time_seconds"):
                self._processor.stop_all_nodes(self._plan)

            self._running = False
            logger.info("scheduler.shutdown_complete", "Scheduler shutdown complete")

    def _run_main_loop(self) -> None:
        """Main scheduling loop."""
        logger = get_logger()
        loop_start = monotonic()
        iteration_count = 0

        while not self._shutdown:
            iteration_start = time.perf_counter()

            with start_span("scheduler.loop_iteration", {"iteration": iteration_count}):
                # Update readiness and queue state
                self._plan.update_readiness(self._cfg.tick_interval_ms)
                self._queue.update_from_plan(self._plan)

                # Update runnable nodes gauge
                runnable_count = len(
                    [
                        state
                        for state in self._plan.ready_states.values()
                        if state.message_ready or state.tick_ready
                    ]
                )
                self._runnable_nodes_gauge.set(runnable_count)

                # Get next runnable node
                runnable = self._queue.get_next_runnable()
                if runnable is None:
                    # No work available - check timeout and idle
                    if (monotonic() - loop_start) > self._cfg.shutdown_timeout_s:
                        logger.info("scheduler.timeout", "Scheduler timeout reached, shutting down")
                        break
                    sleep(self._cfg.idle_sleep_ms / 1000.0)
                    continue

                node_name, priority = runnable
                ready_state = self._plan.ready_states[node_name]

                # Record priority application
                self._priority_applied_counter.inc(1)

                work_done = False

                # Process messages first (higher priority)
                if ready_state.message_ready:
                    with with_context(node=node_name):
                        logger.debug(
                            "scheduler.process_messages",
                            f"Processing messages for node {node_name}",
                        )
                    work_done = self._processor.process_node_messages(self._plan, node_name)

                # Process tick if no messages or if still tick-ready
                elif ready_state.tick_ready:
                    with with_context(node=node_name):
                        logger.debug(
                            "scheduler.process_tick", f"Processing tick for node {node_name}"
                        )
                    work_done = self._processor.process_node_tick(self._plan, node_name)

                if not work_done:
                    sleep(self._cfg.idle_sleep_ms / 1000.0)

            # Record loop iteration metrics
            iteration_duration = time.perf_counter() - iteration_start
            self._loop_latency_histogram.observe(iteration_duration)
            iteration_count += 1

            # Periodic logging of scheduler health
            if iteration_count % 1000 == 0:
                logger.debug(
                    "scheduler.health",
                    f"Completed {iteration_count} iterations",
                    iteration_count=iteration_count,
                    runnable_nodes=runnable_count,
                    avg_loop_latency=iteration_duration,
                )

    def shutdown(self) -> None:
        """Signal scheduler to shutdown gracefully."""
        logger = get_logger()
        logger.info("scheduler.shutdown_requested", "Shutdown requested")
        self._shutdown = True

    def set_priority(self, edge_id: str, priority: PriorityBand) -> None:
        """Set priority for an edge (runtime mutator)."""
        logger = get_logger()

        if not isinstance(priority, PriorityBand):
            raise ValueError("Priority must be a PriorityBand")

        if self._running:
            # Runtime mutation
            if edge_id in self._plan.edges:
                old_priority = self._plan.edges[edge_id].priority_band
                self._plan.edges[edge_id].priority_band = priority
                logger.info(
                    "scheduler.priority_changed",
                    f"Edge priority changed: {edge_id}",
                    edge_id=edge_id,
                    old_priority=old_priority.name,
                    new_priority=priority.name,
                )
            else:
                logger.warn(
                    "scheduler.edge_not_found",
                    f"Edge not found for priority change: {edge_id}",
                    edge_id=edge_id,
                )
        else:
            # Store for later application
            self._pending_priorities[edge_id] = priority
            logger.debug(
                "scheduler.priority_pending",
                f"Priority change queued for edge: {edge_id}",
                edge_id=edge_id,
                priority=priority.name,
            )

    def set_capacity(self, edge_id: str, capacity: int) -> None:
        """Set capacity for an edge (runtime mutator)."""
        logger = get_logger()

        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        if self._running:
            # Runtime mutation
            if edge_id in self._plan.edges:
                old_capacity = self._plan.edges[edge_id].edge.capacity
                self._plan.edges[edge_id].edge.capacity = capacity
                logger.info(
                    "scheduler.capacity_changed",
                    f"Edge capacity changed: {edge_id}",
                    edge_id=edge_id,
                    old_capacity=old_capacity,
                    new_capacity=capacity,
                )
            else:
                logger.warn(
                    "scheduler.edge_not_found",
                    f"Edge not found for capacity change: {edge_id}",
                    edge_id=edge_id,
                )
        else:
            logger.warn(
                "scheduler.capacity_not_supported", "Capacity changes not supported before runtime"
            )

    def _handle_node_emit(self, node: Node, port: str, msg: Message) -> None:
        """Handle message emission from a node (backpressure integration)."""
        logger = get_logger()

        # Find the edge for this node/port combination
        edges = self._plan.get_outgoing_edges(node.name, port)

        for edge in edges:
            # Determine policy based on message type and edge configuration
            policy = Block() if msg.type == MessageType.CONTROL else None

            # Try to put the message
            result = edge.try_put(msg, policy)

            with with_context(node=node.name, port=port, edge_id=edge._edge_id()):
                if result == PutResult.BLOCKED:
                    logger.debug("scheduler.backpressure", "Message blocked, applying backpressure")
                    # TODO: Implement cooperative yielding for backpressure
                elif result == PutResult.DROPPED:
                    logger.warn(
                        "scheduler.message_dropped", "Message dropped due to capacity limits"
                    )
                else:
                    logger.debug(
                        "scheduler.message_routed", f"Message routed successfully: {result.name}"
                    )

    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running

    def get_stats(self) -> dict[str, int | str]:
        """Get basic scheduler statistics."""
        if not self._running:
            return {"status": "stopped"}

        runnable_count = len(
            [
                state
                for state in self._plan.ready_states.values()
                if state.message_ready or state.tick_ready
            ]
        )

        return {
            "status": "running",
            "nodes_count": len(self._plan.nodes),
            "edges_count": len(self._plan.edges),
            "runnable_nodes": runnable_count,
        }
