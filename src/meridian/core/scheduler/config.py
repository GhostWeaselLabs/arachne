from __future__ import annotations

from dataclasses import dataclass


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
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)
    max_batch_per_node: int = 8
    idle_sleep_ms: int = 1
    shutdown_timeout_s: float = 2.0
