from __future__ import annotations

import time
from time import monotonic, sleep

from ...observability.logging import get_logger, with_context
from ...observability.metrics import get_metrics, time_block
from ...observability.tracing import start_span
from ..message import Message, MessageType
from ..node import Node
from ..priority_queue import NodeProcessor, PriorityQueueConfig, PrioritySchedulingQueue
from ..runtime_plan import PriorityBand, RuntimePlan
from ..subgraph import Subgraph
from .config import SchedulerConfig
from .execution import (
    is_node_blocked_by_backpressure,
    try_unblock_node,
    handle_node_emit,
)


class Scheduler:
    """
    Cooperative scheduler for graph execution.
    """

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

        # Pending runtime mutations
        self._pending_priorities: dict[str, PriorityBand] = {}

        # Observability
        self._metrics = get_metrics()
        self._init_metrics()

    def _init_metrics(self) -> None:
        self._runnable_nodes_gauge = self._metrics.gauge("scheduler_runnable_nodes")
        self._loop_latency_histogram = self._metrics.histogram("scheduler_loop_latency_seconds")
        self._priority_applied_counter = self._metrics.counter("scheduler_priority_applied_total")
        self._blocked_nodes_gauge = self._metrics.gauge("scheduler_blocked_nodes")

    def register(self, unit: Node | Subgraph) -> None:
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
            with time_block("scheduler_build_time_seconds"):
                self._plan.build_from_graphs(self._graphs, self._pending_priorities)
                self._plan.connect_nodes_to_scheduler(self)

            with time_block("scheduler_startup_time_seconds"):
                self._processor.start_all_nodes(self._plan)

            logger.info(
                "scheduler.ready",
                "Scheduler ready, entering main loop",
                nodes_count=len(self._plan.nodes),
            )

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
            from .shutdown import graceful_shutdown

            graceful_shutdown(self._processor, self._plan)
            self._running = False

    def _run_main_loop(self) -> None:
        logger = get_logger()
        loop_start = monotonic()
        iteration_count = 0

        while not self._shutdown:
            iteration_start = time.perf_counter()
            with start_span("scheduler.loop_iteration", {"iteration": iteration_count}):
                self._plan.update_readiness(self._cfg.tick_interval_ms)
                self._queue.update_from_plan(self._plan)

                from .fairness import update_scheduler_gauges

                runnable_count, blocked_count = update_scheduler_gauges(
                    self._plan, self._runnable_nodes_gauge, self._blocked_nodes_gauge
                )

                runnable = self._queue.get_next_runnable()
                if runnable is None:
                    if (monotonic() - loop_start) > self._cfg.shutdown_timeout_s:
                        logger.info("scheduler.timeout", "Scheduler timeout reached, shutting down")
                        break
                    sleep(self._cfg.idle_sleep_ms / 1000.0)
                    continue

                node_name, priority = runnable
                ready_state = self._plan.ready_states[node_name]

                if is_node_blocked_by_backpressure(self._plan, node_name):
                    try_unblock_node(self._plan, node_name, self._blocked_nodes_gauge, logger)
                    if is_node_blocked_by_backpressure(self._plan, node_name):
                        logger.debug(
                            "scheduler.node_blocked",
                            f"Node {node_name} blocked by backpressure, yielding",
                            blocked_edges=list(ready_state.blocked_edges),
                        )
                        sleep(self._cfg.idle_sleep_ms / 1000.0)
                        continue

                self._priority_applied_counter.inc(1)
                work_done = False

                if ready_state.message_ready:
                    with with_context(node=node_name):
                        logger.debug(
                            "scheduler.process_messages",
                            f"Processing messages for node {node_name}",
                        )
                    work_done = self._processor.process_node_messages(self._plan, node_name)
                elif ready_state.tick_ready:
                    with with_context(node=node_name):
                        logger.debug(
                            "scheduler.process_tick", f"Processing tick for node {node_name}"
                        )
                    work_done = self._processor.process_node_tick(self._plan, node_name)

                if not work_done:
                    sleep(self._cfg.idle_sleep_ms / 1000.0)

            iteration_duration = time.perf_counter() - iteration_start
            self._loop_latency_histogram.observe(iteration_duration)
            iteration_count += 1

            if iteration_count % 1000 == 0:
                logger.debug(
                    "scheduler.health",
                    f"Completed {iteration_count} iterations",
                    iteration_count=iteration_count,
                    runnable_nodes=runnable_count,
                    avg_loop_latency=iteration_duration,
                )

    def shutdown(self) -> None:
        logger = get_logger()
        logger.info("scheduler.shutdown_requested", "Shutdown requested")
        self._shutdown = True

    def set_priority(self, edge_id: str, priority: PriorityBand) -> None:
        logger = get_logger()
        if not isinstance(priority, PriorityBand):
            raise ValueError("Priority must be a PriorityBand")
        if self._running:
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
            self._pending_priorities[edge_id] = priority
            logger.debug(
                "scheduler.priority_pending",
                f"Priority change queued for edge: {edge_id}",
                edge_id=edge_id,
                priority=priority.name,
            )

    def set_capacity(self, edge_id: str, capacity: int) -> None:
        logger = get_logger()
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        if self._running:
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
        logger = get_logger()
        handle_node_emit(self._plan, self._metrics, node, port, msg, logger)

    def is_running(self) -> bool:
        return self._running

    def get_stats(self) -> dict[str, int | str]:
        if not self._running:
            return {"status": "stopped"}
        runnable_count = len(
            [
                state
                for state in self._plan.ready_states.values()
                if state.message_ready or state.tick_ready
            ]
        )
        blocked_count = len(
            [
                state
                for state in self._plan.ready_states.values()
                if len(state.blocked_edges) > 0
            ]
        )
        return {
            "status": "running",
            "nodes_count": len(self._plan.nodes),
            "edges_count": len(self._plan.edges),
            "runnable_nodes": runnable_count,
            "blocked_nodes": blocked_count,
        }

    def _is_node_blocked_by_backpressure(self, node_name: str) -> bool:
        return is_node_blocked_by_backpressure(self._plan, node_name)

    def _try_unblock_node(self, node_name: str) -> None:
        logger = get_logger()
        try_unblock_node(self._plan, node_name, self._blocked_nodes_gauge, logger)
