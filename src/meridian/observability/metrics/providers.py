from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Dict

from .config import PrometheusConfig, DEFAULT_LATENCY_BUCKETS
from .instruments import Counter, Gauge, Histogram, Metrics


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


class NoopMetrics:
    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter:
        return NoopCounter()

    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge:
        return NoopGauge()

    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram:
        return NoopHistogram()


class PrometheusCounter:
    def __init__(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        self._name = name
        self._labels = labels or {}
        self._value = 0.0

    def inc(self, n: int = 1) -> None:
        self._value += n

    @property
    def value(self) -> float:
        return self._value


class PrometheusGauge:
    def __init__(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        self._name = name
        self._labels = labels or {}
        self._value = 0.0

    def set(self, v: int | float) -> None:
        self._value = float(v)

    @property
    def value(self) -> float:
        return self._value


class PrometheusHistogram:
    def __init__(
        self,
        name: str,
        labels: Mapping[str, str] | None = None,
        buckets: list[float] | None = None,
    ) -> None:
        self._name = name
        self._labels = labels or {}
        self._buckets = buckets or list(DEFAULT_LATENCY_BUCKETS)
        self._bucket_counts: Dict[float, int] = {bucket: 0 for bucket in self._buckets}
        self._bucket_counts[float("inf")] = 0
        self._sum = 0.0
        self._count = 0

    def observe(self, v: int | float) -> None:
        value = float(v)
        self._sum += value
        self._count += 1
        for bucket in self._buckets:
            if value <= bucket:
                self._bucket_counts[bucket] += 1
        self._bucket_counts[float("inf")] += 1

    @property
    def sum(self) -> float:
        return self._sum

    @property
    def count(self) -> int:
        return self._count

    @property
    def buckets(self) -> dict[float, int]:
        return self._bucket_counts.copy()


class PrometheusMetrics:
    def __init__(self, config: PrometheusConfig | None = None) -> None:
        self._config = config or PrometheusConfig()
        self._counters: dict[str, PrometheusCounter] = {}
        self._gauges: dict[str, PrometheusGauge] = {}
        self._histograms: dict[str, PrometheusHistogram] = {}

    def _metric_key(self, name: str, labels: Mapping[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter:
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)
        if key not in self._counters:
            self._counters[key] = PrometheusCounter(full_name, labels)
        return self._counters[key]

    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge:
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)
        if key not in self._gauges:
            self._gauges[key] = PrometheusGauge(full_name, labels)
        return self._gauges[key]

    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram:
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)
        if key not in self._histograms:
            self._histograms[key] = PrometheusHistogram(full_name, labels, list(self._config.default_buckets))
        return self._histograms[key]

    def get_all_counters(self) -> dict[str, PrometheusCounter]:
        return self._counters.copy()

    def get_all_gauges(self) -> dict[str, PrometheusGauge]:
        return self._gauges.copy()

    def get_all_histograms(self) -> dict[str, PrometheusHistogram]:
        return self._histograms.copy()


# Global metrics instance
_global_metrics: Metrics = NoopMetrics()


def get_metrics() -> Metrics:
    return _global_metrics


def configure_metrics(metrics: Metrics) -> None:
    global _global_metrics
    _global_metrics = metrics
