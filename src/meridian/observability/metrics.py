from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
import time
from typing import Protocol


class Counter(Protocol):
    """A monotonically increasing counter metric."""

    def inc(self, n: int = 1) -> None: ...


class Gauge(Protocol):
    """A numerical gauge metric representing the latest value."""

    def set(self, v: int | float) -> None: ...


class Histogram(Protocol):
    """A histogram metric for recording observations into buckets."""

    def observe(self, v: int | float) -> None: ...


class Metrics(Protocol):
    """
    Abstract metrics provider interface.

    Implementations should create or fetch metric instruments with a stable name and optional
    label set. Returned instruments must be safe to reuse across calls with the same name/labels.
    """

    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter: ...
    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge: ...
    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram: ...


@dataclass(frozen=True, slots=True)
class NoopCounter:
    """No-op Counter implementation used when metrics are disabled."""

    def inc(self, n: int = 1) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopGauge:
    """No-op Gauge implementation used when metrics are disabled."""

    def set(self, v: int | float) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopHistogram:
    """No-op Histogram implementation used when metrics are disabled."""

    def observe(self, v: int | float) -> None:
        return None


@dataclass(frozen=True, slots=True)
class NoopMetrics:
    """No-op Metrics provider wiring all instruments to no-op implementations."""

    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter:
        return NoopCounter()

    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge:
        return NoopGauge()

    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram:
        return NoopHistogram()


# Default histogram buckets for latency measurements
DEFAULT_LATENCY_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]


@dataclass
class PrometheusConfig:
    """
    Configuration for the built-in in-memory Prometheus-like metrics adapter.

    Attributes:
      namespace:
        Prefix applied to metric names (e.g., "meridian-runtime_edge_enqueued_total").
      default_buckets:
        Default histogram buckets used when constructing histograms without explicit buckets.
    """

    namespace: str = "meridian-runtime"
    default_buckets: Sequence[float] = field(default_factory=lambda: DEFAULT_LATENCY_BUCKETS)


class PrometheusCounter:
    """Simple in-memory counter for demonstration/test usage."""

    def __init__(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        self._name = name
        self._labels = labels or {}
        self._value = 0.0

    def inc(self, n: int = 1) -> None:
        """Increment the counter by n (default: 1)."""
        self._value += n

    @property
    def value(self) -> float:
        """Current counter value."""
        return self._value


class PrometheusGauge:
    """Simple in-memory gauge for demonstration/test usage."""

    def __init__(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        self._name = name
        self._labels = labels or {}
        self._value = 0.0

    def set(self, v: int | float) -> None:
        """Set the gauge to a specific numeric value."""
        self._value = float(v)

    @property
    def value(self) -> float:
        """Current gauge value."""
        return self._value


class PrometheusHistogram:
    """Simple in-memory histogram with pre-defined buckets and cumulative counts."""

    def __init__(
        self,
        name: str,
        labels: Mapping[str, str] | None = None,
        buckets: Sequence[float] | None = None,
    ) -> None:
        self._name = name
        self._labels = labels or {}
        self._buckets = buckets or DEFAULT_LATENCY_BUCKETS
        self._bucket_counts = {bucket: 0 for bucket in self._buckets}
        self._bucket_counts[float("inf")] = 0
        self._sum = 0.0
        self._count = 0

    def observe(self, v: int | float) -> None:
        """Record an observation into the histogram and update cumulative buckets."""
        value = float(v)
        self._sum += value
        self._count += 1

        for bucket in self._buckets:
            if value <= bucket:
                self._bucket_counts[bucket] += 1
        self._bucket_counts[float("inf")] += 1

    @property
    def sum(self) -> float:
        """Sum of all observed values."""
        return self._sum

    @property
    def count(self) -> int:
        """Total number of observations."""
        return self._count

    @property
    def buckets(self) -> dict[float, int]:
        """A copy of bucket upper-bound -> cumulative count mapping (including +Inf)."""
        return self._bucket_counts.copy()


class PrometheusMetrics:
    """
    In-memory Prometheus-like metrics provider suitable for development and tests.

    Metric naming:
      - Instruments are registered under "{namespace}_{name}" where namespace is configurable.
      - Labels are encoded into a stable key "name{k=v,...}" for fast reuse.

    Note:
      - This adapter does not expose a /metrics endpoint; it is a local accumulator only.
    """

    def __init__(self, config: PrometheusConfig | None = None) -> None:
        self._config = config or PrometheusConfig()
        self._counters: dict[str, PrometheusCounter] = {}
        self._gauges: dict[str, PrometheusGauge] = {}
        self._histograms: dict[str, PrometheusHistogram] = {}

    def _metric_key(self, name: str, labels: Mapping[str, str] | None) -> str:
        """Build a stable key from a metric name and label mapping."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def counter(self, name: str, labels: Mapping[str, str] | None = None) -> Counter:
        """Create or fetch a Counter instrument with the given name and labels."""
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)

        if key not in self._counters:
            self._counters[key] = PrometheusCounter(full_name, labels)

        return self._counters[key]

    def gauge(self, name: str, labels: Mapping[str, str] | None = None) -> Gauge:
        """Create or fetch a Gauge instrument with the given name and labels."""
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)

        if key not in self._gauges:
            self._gauges[key] = PrometheusGauge(full_name, labels)

        return self._gauges[key]

    def histogram(self, name: str, labels: Mapping[str, str] | None = None) -> Histogram:
        """Create or fetch a Histogram instrument with the given name and labels."""
        full_name = f"{self._config.namespace}_{name}"
        key = self._metric_key(full_name, labels)

        if key not in self._histograms:
            self._histograms[key] = PrometheusHistogram(
                full_name,
                labels,
                self._config.default_buckets,
            )

        return self._histograms[key]

    def get_all_counters(self) -> dict[str, PrometheusCounter]:
        """Return a copy of all counters keyed by fully-qualified metric key."""
        return self._counters.copy()

    def get_all_gauges(self) -> dict[str, PrometheusGauge]:
        """Return a copy of all gauges keyed by fully-qualified metric key."""
        return self._gauges.copy()

    def get_all_histograms(self) -> dict[str, PrometheusHistogram]:
        """Return a copy of all histograms keyed by fully-qualified metric key."""
        return self._histograms.copy()


# Global metrics instance
_global_metrics: Metrics = NoopMetrics()


def get_metrics() -> Metrics:
    """Get the global metrics instance (NoopMetrics by default)."""
    return _global_metrics


def configure_metrics(metrics: Metrics) -> None:
    """
    Configure the global metrics instance.

    Parameters:
      metrics:
        A Metrics implementation (e.g., PrometheusMetrics). All future calls to
        get_metrics() will return this instance.
    """
    global _global_metrics
    _global_metrics = metrics


@contextmanager
def time_block(name: str, labels: Mapping[str, str] | None = None) -> Iterator[None]:
    """
    Context manager that records elapsed wall-clock time into a histogram.

    Parameters:
      name:
        Histogram metric name (without namespace prefix).
      labels:
        Optional label mapping to attach to the histogram.

    Usage:
      with time_block("node_tick_duration_seconds", {"node": "A"}):
          do_work()

    Notes:
      - The histogram is fetched from the global metrics instance. If metrics are disabled,
        this is a no-op via NoopMetrics.
    """
    histogram = get_metrics().histogram(name, labels)
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        histogram.observe(duration)
