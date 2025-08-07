from __future__ import annotations

from typing import Mapping, Protocol


class Counter(Protocol):
    def inc(self, n: int = 1) -> None: ...


class Gauge(Protocol):
    def set(self, v: int | float) -> None: ...


class Histogram(Protocol):
    def observe(self, v: int | float) -> None: ...


class Metrics(Protocol):
    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter: ...
    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge: ...
    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram: ...
