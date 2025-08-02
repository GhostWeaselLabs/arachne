from __future__ import annotations

import time

import pytest

from meridian.observability.metrics import (
    NoopMetrics,
    PrometheusConfig,
    PrometheusMetrics,
    configure_metrics,
    get_metrics,
    time_block,
)


class TestNoopMetrics:
    def test_noop_counter(self) -> None:
        """Test no-op counter implementation."""
        metrics = NoopMetrics()
        counter = metrics.counter("test_counter", {"label": "value"})

        # Should not raise any exceptions
        counter.inc()
        counter.inc(5)

    def test_noop_gauge(self) -> None:
        """Test no-op gauge implementation."""
        metrics = NoopMetrics()
        gauge = metrics.gauge("test_gauge", {"label": "value"})

        # Should not raise any exceptions
        gauge.set(42)
        gauge.set(3.14)

    def test_noop_histogram(self) -> None:
        """Test no-op histogram implementation."""
        metrics = NoopMetrics()
        histogram = metrics.histogram("test_histogram", {"label": "value"})

        # Should not raise any exceptions
        histogram.observe(1.0)
        histogram.observe(0.001)


class TestPrometheusMetrics:
    def test_prometheus_counter(self) -> None:
        """Test Prometheus counter implementation."""
        config = PrometheusConfig(namespace="test")
        metrics = PrometheusMetrics(config)

        counter = metrics.counter("requests_total", {"method": "GET"})

        # Initial value should be 0
        assert counter.value == 0.0

        # Increment and check value
        counter.inc()
        assert counter.value == 1.0

        counter.inc(5)
        assert counter.value == 6.0

    def test_prometheus_gauge(self) -> None:
        """Test Prometheus gauge implementation."""
        config = PrometheusConfig(namespace="test")
        metrics = PrometheusMetrics(config)

        gauge = metrics.gauge("temperature", {"location": "server_room"})

        # Initial value should be 0
        assert gauge.value == 0.0

        # Set value and check
        gauge.set(23.5)
        assert gauge.value == 23.5

        gauge.set(100)
        assert gauge.value == 100.0

    def test_prometheus_histogram(self) -> None:
        """Test Prometheus histogram implementation."""
        config = PrometheusConfig(namespace="test", default_buckets=[0.1, 0.5, 1.0, 5.0])
        metrics = PrometheusMetrics(config)

        histogram = metrics.histogram("request_duration", {"endpoint": "/api"})

        # Initial values
        assert histogram.count == 0
        assert histogram.sum == 0.0

        # Observe some values
        histogram.observe(0.05)  # Should go in 0.1 bucket
        histogram.observe(0.3)  # Should go in 0.5 bucket
        histogram.observe(2.0)  # Should go in 5.0 bucket

        assert histogram.count == 3
        assert histogram.sum == 2.35

        buckets = histogram.buckets
        assert buckets[0.1] == 1  # 0.05 <= 0.1
        assert buckets[0.5] == 2  # 0.05, 0.3 <= 0.5
        assert buckets[1.0] == 2  # 0.05, 0.3 <= 1.0
        assert buckets[5.0] == 3  # all values <= 5.0
        assert buckets[float("inf")] == 3  # all values

    def test_metric_naming_with_namespace(self) -> None:
        """Test metric naming with namespace."""
        config = PrometheusConfig(namespace="arachne")
        metrics = PrometheusMetrics(config)

        metrics.counter("messages_total", {"node": "test"})

        # The counter should be created with the namespaced name
        all_counters = metrics.get_all_counters()
        assert len(all_counters) == 1

        # Check that the key includes the namespace
        key = list(all_counters.keys())[0]
        assert "arachne_messages_total" in key

    def test_metric_key_generation(self) -> None:
        """Test metric key generation with labels."""
        config = PrometheusConfig(namespace="test")
        metrics = PrometheusMetrics(config)

        # Create metrics with different label combinations
        counter1 = metrics.counter("requests", {"method": "GET", "status": "200"})
        metrics.counter("requests", {"method": "POST", "status": "201"})
        counter3 = metrics.counter(
            "requests", {"method": "GET", "status": "200"}
        )  # Same as counter1

        # counter1 and counter3 should be the same instance
        assert counter1 is counter3

        # Should have 2 different counters
        all_counters = metrics.get_all_counters()
        assert len(all_counters) == 2

    def test_metrics_without_labels(self) -> None:
        """Test metrics without labels."""
        config = PrometheusConfig(namespace="test")
        metrics = PrometheusMetrics(config)

        counter = metrics.counter("simple_counter")
        gauge = metrics.gauge("simple_gauge")
        histogram = metrics.histogram("simple_histogram")

        # Should work without labels
        counter.inc()
        gauge.set(42)
        histogram.observe(1.0)

        assert counter.value == 1.0
        assert gauge.value == 42.0
        assert histogram.count == 1


class TestGlobalMetrics:
    def test_default_noop_metrics(self) -> None:
        """Test that default global metrics is no-op."""
        # Reset to default
        configure_metrics(NoopMetrics())

        metrics = get_metrics()
        assert isinstance(metrics, NoopMetrics)

    def test_configure_prometheus_metrics(self) -> None:
        """Test configuring Prometheus metrics globally."""
        prometheus_metrics = PrometheusMetrics()
        configure_metrics(prometheus_metrics)

        metrics = get_metrics()
        assert metrics is prometheus_metrics

    def test_global_metrics_usage(self) -> None:
        """Test using global metrics."""
        prometheus_metrics = PrometheusMetrics()
        configure_metrics(prometheus_metrics)

        metrics = get_metrics()
        counter = metrics.counter("global_test", {"type": "unit_test"})
        counter.inc()

        # Verify it was recorded
        all_counters = prometheus_metrics.get_all_counters()
        assert len(all_counters) == 1


class TestTimeBlock:
    def test_time_block_context_manager(self) -> None:
        """Test time_block context manager."""
        prometheus_metrics = PrometheusMetrics()
        configure_metrics(prometheus_metrics)

        with time_block("operation_duration", {"operation": "test"}):
            time.sleep(0.01)  # Sleep for 10ms

        # Check that the histogram was updated
        all_histograms = prometheus_metrics.get_all_histograms()
        assert len(all_histograms) == 1

        histogram = list(all_histograms.values())[0]
        assert histogram.count == 1
        assert histogram.sum > 0.005  # Should be at least 5ms
        assert histogram.sum < 0.1  # Should be less than 100ms

    def test_time_block_with_exception(self) -> None:
        """Test time_block still records time when exception occurs."""
        prometheus_metrics = PrometheusMetrics()
        configure_metrics(prometheus_metrics)

        with pytest.raises(ValueError):
            with time_block("error_operation", {"type": "error"}):
                time.sleep(0.01)
                raise ValueError("Test error")

        # Check that the histogram was still updated
        all_histograms = prometheus_metrics.get_all_histograms()
        assert len(all_histograms) == 1

        histogram = list(all_histograms.values())[0]
        assert histogram.count == 1

    def test_time_block_without_labels(self) -> None:
        """Test time_block without labels."""
        prometheus_metrics = PrometheusMetrics()
        configure_metrics(prometheus_metrics)

        with time_block("simple_operation"):
            time.sleep(0.01)

        all_histograms = prometheus_metrics.get_all_histograms()
        assert len(all_histograms) == 1


class TestPrometheusConfig:
    def test_default_config(self) -> None:
        """Test default Prometheus configuration."""
        config = PrometheusConfig()

        assert config.namespace == "arachne"
        assert len(config.default_buckets) > 0
        assert 0.001 in config.default_buckets
        assert 5.0 in config.default_buckets

    def test_custom_config(self) -> None:
        """Test custom Prometheus configuration."""
        custom_buckets = [0.01, 0.1, 1.0, 10.0]
        config = PrometheusConfig(namespace="custom", default_buckets=custom_buckets)

        assert config.namespace == "custom"
        assert config.default_buckets == custom_buckets

        metrics = PrometheusMetrics(config)
        histogram = metrics.histogram("test_histogram")

        # Should use custom buckets
        histogram.observe(0.5)
        buckets = histogram.buckets
        assert 0.01 in buckets
        assert 0.1 in buckets
        assert 1.0 in buckets
        assert 10.0 in buckets


if __name__ == "__main__":
    pytest.main([__file__])
