from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator, Mapping

from .providers import get_metrics


@contextmanager
def time_block(name: str, labels: Mapping[str, str] | None = None) -> Iterator[None]:
    histogram = get_metrics().histogram(name, labels)
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        histogram.observe(duration)
