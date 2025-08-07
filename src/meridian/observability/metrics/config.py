from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

DEFAULT_LATENCY_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]


@dataclass
class PrometheusConfig:
    namespace: str = "meridian-runtime"
    default_buckets: Sequence[float] = field(default_factory=lambda: DEFAULT_LATENCY_BUCKETS)
