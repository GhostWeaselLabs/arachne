
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# # Observability Basics

# This notebook provides an introduction to the observability features in Meridian Runtime. Observability is crucial for understanding the behavior of a system, debugging issues, and monitoring performance. Meridian Runtime provides a comprehensive observability system with structured logging, metrics collection, and distributed tracing.

# ## 1. Configuring Observability

# The first step is to configure the observability system. You can do this using the `ObservabilityConfig` class and the `configure_observability` function.

# +
from meridian.observability.config import ObservabilityConfig, configure_observability

# Simple development setup
config = ObservabilityConfig(
    log_level="INFO",
    log_json=False, # Use human-readable logs for this example
    metrics_enabled=True,
    metrics_namespace="myapp",
    tracing_enabled=True,
    tracing_provider="inmemory",
    tracing_sample_rate=1.0
)

configure_observability(config)
# -

# ## 2. Structured Logging

# Meridian Runtime uses structured logging to make it easy to search and analyze logs. You can use the `get_logger` function to get a logger instance.

# +
from meridian.observability.logging import get_logger

logger = get_logger()

# Simple logging
logger.info("node.start", "Node starting up", node_name="worker", version="1.0")

# Error logging with context
logger.error("node.error", "Failed to process message", 
            error="validation_failed", 
            message_id="123",
            port="input")
# -

# ## 3. Metrics Collection

# Meridian Runtime can collect a variety of metrics to help you monitor the performance of your dataflows. You can use the `get_metrics` function to get a metrics collector instance.

# +
from meridian.observability.metrics import get_metrics

metrics = get_metrics()

# Counters for events
messages_processed = metrics.counter("messages_processed_total")
messages_processed.inc()

# Gauges for current state
queue_depth = metrics.gauge("queue_depth")
queue_depth.set(42)

# Histograms for distributions
processing_time = metrics.histogram("processing_duration_seconds")
processing_time.observe(0.125)
# -

# ## 4. Distributed Tracing

# Distributed tracing allows you to trace the flow of a request across multiple nodes in your dataflow. You can use the `start_span` function to create a new trace span.

# +
from meridian.observability.tracing import start_span

# Create a span for an operation
with start_span("process_message", {"message_id": "123", "node": "worker"}):
    # All operations in this block are traced
    print("Processing message...")
# -

# ## 5. Putting It All Together

# Let's see how to use these features in a simple graph.

# +
from meridian.core import Subgraph, Scheduler, Node, Message, MessageType
from meridian.observability.logging import get_logger, with_context
from meridian.observability.metrics import get_metrics, time_block
from meridian.observability.tracing import start_span

class InstrumentedNode(Node):
    def _handle_message(self, port, msg):
        logger = get_logger()
        metrics = get_metrics()

        with with_context(node=self.name, port=port, trace_id=msg.get_trace_id()):
            logger.info("processing.start", "Starting message processing")

            with time_block("node_processing_duration"):
                with start_span("process_message", {"port": port, "type": msg.type.value}):
                    print(f"Processing message: {msg.payload}")
                    metrics.counter("messages_processed_total").inc()
                    self.emit("out", Message(MessageType.DATA, msg.payload))

            logger.info("processing.complete", "Message processed successfully")

class Producer(Node):
    def __init__(self, n=5):
        self._n = n
        self._i = 0

    def name(self):
        return "producer"

    def on_start(self):
        self._i = 0

    def on_tick(self):
        if self._i < self._n:
            self.emit("out", Message(payload=self._i))
            self._i += 1

# Create a subgraph
sg = Subgraph.from_nodes("observability_demo", [InstrumentedNode(), Producer()])
sg.connect(("producer","out"), ("instrumentednode","in"), capacity=4)

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(sg)

# Run the scheduler
scheduler.run()
# -

# ## 6. Conclusion

# This notebook has provided a basic introduction to the observability features in Meridian Runtime. By using structured logging, metrics collection, and distributed tracing, you can gain deep insights into the behavior of your dataflows, making it easier to debug issues and monitor performance.
