from __future__ import annotations

from io import StringIO
import time

from arachne.core import Message, MessageType, Node, Scheduler, SchedulerConfig, Subgraph
from arachne.observability.config import configure_observability, get_development_config
from arachne.observability.logging import get_logger
from arachne.observability.metrics import PrometheusMetrics, get_metrics
from arachne.observability.tracing import InMemoryTracer, get_tracer


class ObsTestProducer(Node):
    """Test producer node."""

    def __init__(self) -> None:
        node = Node.with_ports("ObsTestProducer", [], ["out"])
        super().__init__(node.name, node.inputs, node.outputs)
        self.tick_count = 0

    def _handle_tick(self) -> None:
        """Produce a test message."""
        self.tick_count += 1
        if self.tick_count <= 3:  # Produce 3 messages
            msg = Message(MessageType.DATA, f"test-message-{self.tick_count}")
            self.emit("out", msg)


class ObsTestConsumer(Node):
    """Test consumer node."""

    def __init__(self) -> None:
        node = Node.with_ports("ObsTestConsumer", ["in"], [])
        super().__init__(node.name, node.inputs, node.outputs)
        self.messages_received = 0

    def _handle_message(self, port: str, msg: Message) -> None:
        """Consume a test message."""
        self.messages_received += 1
        logger = get_logger()
        logger.info("consumer.message", f"Received: {msg.payload}")


def test_observability_integration() -> None:
    """Test complete observability integration."""

    # Configure observability for development
    log_stream = StringIO()
    config = get_development_config()
    config.log_stream = log_stream
    configure_observability(config)

    # Verify components are configured
    get_logger()
    metrics = get_metrics()
    tracer = get_tracer()

    assert isinstance(metrics, PrometheusMetrics)
    assert isinstance(tracer, InMemoryTracer)
    assert tracer.is_enabled()

    # Create test graph
    producer = ObsTestProducer()
    consumer = ObsTestConsumer()

    subgraph = Subgraph.from_nodes("TestGraph", [producer, consumer])
    subgraph.connect(("ObsTestProducer", "out"), ("ObsTestConsumer", "in"), capacity=10)

    # Create scheduler with short timeout
    scheduler_config = SchedulerConfig(tick_interval_ms=50, shutdown_timeout_s=1.0)
    scheduler = Scheduler(scheduler_config)
    scheduler.register(subgraph)

    # Run the scheduler
    start_time = time.time()
    scheduler.run()
    duration = time.time() - start_time

    # Verify messages were processed
    assert consumer.messages_received == 3
    assert duration < 2.0  # Should complete quickly

    # Verify logging occurred
    log_output = log_stream.getvalue()
    assert "scheduler.start" in log_output
    assert "node.start" in log_output
    assert "consumer.message" in log_output
    assert "scheduler.shutdown_complete" in log_output

    # Verify metrics were recorded
    all_counters = metrics.get_all_counters()
    all_gauges = metrics.get_all_gauges()
    all_histograms = metrics.get_all_histograms()

    # Should have node message counters
    node_message_counters = [k for k in all_counters.keys() if "node_messages_total" in k]
    assert len(node_message_counters) > 0

    # Should have edge metrics
    edge_counters = [k for k in all_counters.keys() if "edge_enqueued_total" in k]
    assert len(edge_counters) > 0

    # Should have scheduler metrics
    scheduler_gauges = [k for k in all_gauges.keys() if "scheduler_runnable_nodes" in k]
    assert len(scheduler_gauges) > 0

    # Verify tracing occurred
    spans = tracer.get_spans()
    assert len(spans) > 0

    # Should have node spans
    node_spans = [span for span in spans if span.name.startswith("node.")]
    assert len(node_spans) > 0

    # Should have scheduler spans
    scheduler_spans = [span for span in spans if span.name.startswith("scheduler.")]
    assert len(scheduler_spans) > 0

    print("✅ Observability integration test passed!")
    print(f"   - Processed {consumer.messages_received} messages")
    print(
        f"   - Recorded {len(all_counters)} counters, "
        f"{len(all_gauges)} gauges, {len(all_histograms)} histograms"
    )
    print(f"   - Created {len(spans)} spans")
    print(f"   - Generated {len(log_output.splitlines())} log lines")


if __name__ == "__main__":
    test_observability_integration()
