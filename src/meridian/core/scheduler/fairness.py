from __future__ import annotations

from ..runtime_plan import RuntimePlan


def compute_runnable_count(plan: RuntimePlan) -> int:
    return len(
        [state for state in plan.ready_states.values() if state.message_ready or state.tick_ready]
    )


def compute_blocked_count(plan: RuntimePlan) -> int:
    return len([state for state in plan.ready_states.values() if len(state.blocked_edges) > 0])


def update_scheduler_gauges(plan: RuntimePlan, runnable_gauge, blocked_gauge) -> tuple[int, int]:
    """
    Compute runnable/blocked counts and update gauges.

    Returns the pair (runnable_count, blocked_count).
    """
    runnable_count = compute_runnable_count(plan)
    blocked_count = compute_blocked_count(plan)
    runnable_gauge.set(runnable_count)
    blocked_gauge.set(blocked_count)
    return runnable_count, blocked_count
