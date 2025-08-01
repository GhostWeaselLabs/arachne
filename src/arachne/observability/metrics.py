from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


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


@dataclass(frozen=True, slots=True)
class NoopCounter:
    def inc(self, n: int = 1) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopGauge:
    def set(self, v: int | float) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopHistogram:
    def observe(self, v: int | float) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopMetrics:
    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter:
        return NoopCounter()

    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge:
        return NoopGauge()

    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram:
        return NoopHistogram()
