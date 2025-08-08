from __future__ import annotations

from collections import defaultdict, deque

from ..runtime_plan import PriorityBand, RuntimePlan
from .config import PriorityQueueConfig


class PrioritySchedulingQueue:
    def __init__(self, config: PriorityQueueConfig) -> None:
        self._config = config
        self._ready_queues: dict[PriorityBand, deque[str]] = {
            PriorityBand.CONTROL: deque(),
            PriorityBand.HIGH: deque(),
            PriorityBand.NORMAL: deque(),
        }
        self._round_robin_state: dict[PriorityBand, int] = defaultdict(int)

    def clear(self) -> None:
        for queue in self._ready_queues.values():
            queue.clear()
        self._round_robin_state.clear()

    def enqueue_runnable(self, node_name: str, priority: PriorityBand) -> None:
        for queue in self._ready_queues.values():
            if node_name in queue:
                queue.remove(node_name)
        self._ready_queues[priority].append(node_name)

    def get_next_runnable(self) -> tuple[str, PriorityBand] | None:
        ratios = {
            PriorityBand.CONTROL: self._config.fairness_ratio[0],
            PriorityBand.HIGH: self._config.fairness_ratio[1],
            PriorityBand.NORMAL: self._config.fairness_ratio[2],
        }
        total_ratio = sum(ratios.values())
        current_tick = sum(len(q) for q in self._ready_queues.values())
        for band in [PriorityBand.CONTROL, PriorityBand.HIGH, PriorityBand.NORMAL]:
            queue = self._ready_queues[band]
            if not queue:
                continue
            band_ratio = ratios[band] / total_ratio if total_ratio > 0 else 0
            if current_tick % total_ratio < band_ratio * total_ratio:
                return queue.popleft(), band
            if band == PriorityBand.CONTROL and queue:
                return queue.popleft(), band
        for band, queue in self._ready_queues.items():
            if queue:
                return queue.popleft(), band
        return None

    def update_from_plan(self, plan: RuntimePlan) -> None:
        for node_name in plan.nodes:
            if plan.is_node_ready(node_name):
                priority = plan.get_node_priority(node_name)
                self.enqueue_runnable(node_name, priority)

    def has_runnable_nodes(self) -> bool:
        return any(queue for queue in self._ready_queues.values())

    def get_queue_depths(self) -> dict[PriorityBand, int]:
        return {band: len(queue) for band, queue in self._ready_queues.items()}
