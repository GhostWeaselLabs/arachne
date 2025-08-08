from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PriorityQueueConfig:
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)
    max_batch_per_node: int = 8
