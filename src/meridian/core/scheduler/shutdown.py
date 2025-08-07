from __future__ import annotations

from ...observability.logging import get_logger
from ...observability.metrics import time_block
from ..priority_queue import NodeProcessor
from ..runtime_plan import RuntimePlan


def graceful_shutdown(processor: NodeProcessor, plan: RuntimePlan) -> None:
    """
    Stop all nodes using the processor with timing and logging.
    """
    logger = get_logger()
    logger.info("scheduler.shutdown_start", "Starting graceful shutdown")
    with time_block("scheduler_shutdown_time_seconds"):
        processor.stop_all_nodes(plan)
    logger.info("scheduler.shutdown_complete", "Scheduler shutdown complete")
