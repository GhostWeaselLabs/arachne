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
    """
    Configuration for the cooperative scheduler.

    Parameters:
      tick_interval_ms:
        Milliseconds used by the runtime to determine when to consider a node
        tick-ready. The plan updates tick readiness using this interval.
      fairness_ratio:
        Relative weights applied to priority bands when selecting runnable nodes.
        Tuple order corresponds to (control, high, normal).
      max_batch_per_node:
        Maximum number of items processed per scheduling slice for a node. Keeps
        individual nodes from monopolizing the loop.
      idle_sleep_ms:
        Milliseconds to sleep when no work is available. Reduces CPU churn while idle.
      shutdown_timeout_s:
        Maximum allowed wall-clock seconds with no runnable work before the scheduler
        exits the main loop and begins graceful shutdown.

    Notes:
      - These values tune responsiveness, fairness, and CPU usage. For latency-sensitive
        workloads, consider reducing idle_sleep_ms and ensuring batch sizes are small.
    """

    tick_interval_ms: int = 50
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 8
    idle_sleep_ms: int = 1
    shutdown_timeout_s: float = 2.0


class Scheduler:
    """
    Cooperative scheduler for graph execution.

    Responsibilities:
      - Build a runtime plan from registered nodes/subgraphs.
      - Drive node lifecycle: start → handle messages/ticks → stop.
      - Enforce fairness via a priority scheduling queue.
      - Apply backpressure and routing policies on emissions.
      - Surface observability via logs, metrics, and traces.

    Lifecycle:
      1) register(Node|Subgraph) for all units
      2) run() to start, which builds the plan and starts all nodes
      3) main loop processes messages first, then ticks, until shutdown
      4) shutdown() to request graceful termination, or automatic timeout

    Error handling:
      - Exceptions within node handlers are logged and re-raised to the scheduler;
        the processor applies the runtime’s policy. The scheduler logs and continues
        shutdown on fatal errors.

    Threading and performance:
      - Designed for cooperative execution. Avoid blocking calls inside node handlers.
      - Keep per-iteration work bounded (max_batch_per_node) to maintain fairness.

    """

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        """
        Initialize the scheduler with optional configuration.

        Parameters:
          config:
            SchedulerConfig to use. If None, defaults are applied.

        Side effects:
          - Initializes the priority queue and node processor.
          - Prepares observability instruments (metrics).

        """
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
        """Initialize scheduler metrics used to monitor loop health and load."""
        self._runnable_nodes_gauge = self._metrics.gauge("scheduler_runnable_nodes")
        self._loop_latency_histogram = self._metrics.histogram("scheduler_loop_latency_seconds")
        self._priority_applied_counter = self._metrics.counter("scheduler_priority_applied_total")

    def register(self, unit: Node | Subgraph) -> None:
        """
        Register a node or subgraph for execution.

        Parameters:
          unit:
            A Node or Subgraph to be managed by this scheduler.

        Raises:
          RuntimeError:
            If called while the scheduler is already running.

        Notes:
          - Nodes are wrapped in a single-node Subgraph internally for uniform handling.
          - Registration is only allowed prior to run(); use runtime mutators for live changes.
        """
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
        """
        Run the scheduler until shutdown is requested or timeout elapses.

        Behavior:
          - Builds the runtime plan and connects nodes to the scheduler.
          - Starts all nodes, then enters the main scheduling loop.
          - On exit or error, performs a graceful shutdown of all nodes.

        Notes:
          - Re-entrant calls are ignored if already running.
          - Use shutdown() to request termination from another thread/task.
        """
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
        """
        Main scheduling loop.

        Responsibilities:
          - Updates plan readiness (messages and ticks).
          - Feeds the priority queue with runnable nodes according to fairness settings.
          - Processes messages with precedence over ticks.
          - Records loop latency and runnable node count.
          - Applies idle sleep when no work is available to reduce CPU usage.

        Termination:
          - Exits when shutdown is requested or when shutdown timeout elapses without work.
        """
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
        """
        Signal scheduler to shutdown gracefully.

        Side effects:
          - Sets an internal flag checked by the main loop to begin termination.
          - Logs a shutdown request event.

        Notes:
          - The main loop will complete in-flight work and stop nodes before exiting.
        """
        logger = get_logger()
        logger.info("scheduler.shutdown_requested", "Shutdown requested")
        self._shutdown = True

    def set_priority(self, edge_id: str, priority: PriorityBand) -> None:
        """
        Set the priority band for a specific edge at runtime or pre-runtime.

        Parameters:
          edge_id:
            Identifier of the edge whose priority should change.
          priority:
            PriorityBand to apply.

        Behavior:
          - If the scheduler is running and the edge exists, applies the change immediately.
          - If the scheduler is not running, queues the change to be applied during plan build.

        Raises:
          ValueError:
            If the provided priority is not a PriorityBand instance.
        """
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
        """
        Set the queue capacity for a specific edge at runtime.

        Parameters:
          edge_id:
            Identifier of the edge whose capacity should change.
          capacity:
            Positive integer representing the maximum queue size.

        Behavior:
          - If the scheduler is running and the edge exists, applies the change immediately.
          - Capacity changes are not supported prior to runtime.

        Raises:
          ValueError:
            If capacity is not a positive integer.
        """
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
        """
        Handle message emission from a node with backpressure-aware routing.

        Parameters:
          node:
            The emitting Node.
          port:
            Name of the output port used for emission.
          msg:
            The Message being emitted.

        Behavior:
          - Looks up outgoing edges from the given node/port.
          - Applies a stricter policy (Block) for CONTROL messages by default.
          - Invokes edge.try_put(msg, policy) and logs the result.
          - Future: may yield cooperatively on BLOCKED to implement backpressure.

        Notes:
          - This is invoked by Node.emit() when a scheduler is attached.
        """
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
        """Return True if the scheduler main loop is active."""
        return self._running

    def get_stats(self) -> dict[str, int | str]:
        """
        Get basic scheduler statistics.

        Returns:
          A dictionary containing:
            - status: "running" or "stopped"
            - nodes_count: number of nodes in the plan (when running)
            - edges_count: number of edges in the plan (when running)
            - runnable_nodes: count of nodes currently runnable (when running)
        """
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
