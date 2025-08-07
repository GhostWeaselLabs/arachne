
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

# # Observability Analysis with Meridian Runtime

# This notebook demonstrates how to capture, filter, and analyze observability data (logs and metrics) from Meridian Runtime. It showcases how to gain insights into the behavior of your dataflows using structured logging and Prometheus-style metrics.

# ## 1. Setup: Add Project to Python Path

# This cell adds the project's `src` directory to the Python path. This is necessary for the notebook to find and import the `meridian` module.

# +
import sys
import os

# Add the project's 'src' directory to the Python path
# This is necessary for the notebook to find the 'meridian' module
# We assume the notebook is run from the 'notebooks/research' directory.
src_path = os.path.abspath('../../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added '{src_path}' to the Python path.")
# -

# ## 2. Imports and Configuration

# We'll import necessary modules and configure observability to capture logs and metrics.

# +
import io
import json
import time
import threading
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from IPython.display import display

from meridian.core import Node, Message, MessageType, Port, PortDirection, PortSpec, Subgraph, Scheduler, SchedulerConfig
from meridian.observability.config import ObservabilityConfig, configure_observability
from meridian.observability.logging import get_logger
from meridian.observability.metrics import PrometheusMetrics, configure_metrics, get_metrics

# Use an in-memory stream to capture logs
log_stream = io.StringIO()

# Configure observability to capture logs and metrics
configure_observability(
    ObservabilityConfig(
        log_level="DEBUG", # Capture all logs for analysis
        log_json=True,     # Emit JSON logs for easy parsing
        log_stream=log_stream,
        metrics_enabled=True,
        metrics_namespace="demo_app",
        tracing_enabled=False,
    )
)

# Ensure PrometheusMetrics is configured for metric collection
configure_metrics(PrometheusMetrics())

logger = get_logger()
metrics = get_metrics()
# -

# ## 3. Graph Definition

# We'll define a simple graph with a producer, a processing node, and a consumer to generate observability data.

# +
class DataProducer(Node):
    def __init__(self, n=100):
        super().__init__(
            name="producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
        self._n = n
        self._i = 0

    def _handle_tick(self):
        if self._i < self._n:
            self.emit("out", Message(type=MessageType.DATA, payload=self._i))
            self._i += 1

class DataProcessor(Node):
    def __init__(self):
        super().__init__(
            name="processor",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )

    def _handle_message(self, port, msg):
        # Simulate some processing time
        time.sleep(0.005)
        self.emit("out", Message(type=MessageType.DATA, payload=msg.payload * 2))

class DataConsumer(Node):
    def __init__(self):
        super().__init__(
            name="consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
        self.received_messages = []

    def _handle_message(self, port, msg):
        self.received_messages.append(msg.payload)
# -

# ## 4. Running the Simulation and Collecting Data

# We'll run the graph and collect all logs and metrics generated during its execution.

# +
class VisualizingScheduler(Scheduler):
    def __init__(self, config: SchedulerConfig | None = None):
        super().__init__(config)
        self.queue_depth_history = {}
        self.message_counts_history = {}
        self.timestamps = []
        self._start_time = time.monotonic()

    def _run_main_loop(self) -> None:
        # Call the original main loop, but also collect metrics periodically
        loop_start_time = time.monotonic()
        last_metric_collection_time = loop_start_time
        
        while not self._shutdown:
            # Collect metrics snapshot
            current_time = time.monotonic() - self._start_time
            self.timestamps.append(current_time)

            # Collect queue depths
            for edge_ref in self._plan.edges.values():
                edge_id = edge_ref.edge._edge_id()
                if edge_id not in self.queue_depth_history:
                    self.queue_depth_history[edge_id] = []
                self.queue_depth_history[edge_id].append(edge_ref.edge.depth())

            # Collect message counts (counters)
            for metric_key, counter_obj in metrics.get_all_counters().items():
                if metric_key.startswith('demo_app_node_messages_total'):
                    node_name = counter_obj._labels.get('node', 'unknown')
                    if node_name not in self.message_counts_history:
                        self.message_counts_history[node_name] = []
                    self.message_counts_history[node_name].append(counter_obj.value)

            # Run a single iteration of the scheduler's main loop logic
            super()._run_main_loop_single_iteration() # Assuming such a method exists or can be extracted

            # Sleep to control loop frequency and allow time for external events
            sleep_time = self._cfg.tick_interval_ms / 1000.0
            time.sleep(sleep_time)

        # Ensure all history lists have the same length for plotting
        max_len = max(len(q) for q in self.queue_depth_history.values())
        for q in self.queue_depth_history.values():
            while len(q) < max_len:
                q.append(q[-1] if q else 0) # Pad with last value or 0

        max_len = max(len(q) for q in self.message_counts_history.values())
        for q in self.message_counts_history.values():
            while len(q) < max_len:
                q.append(q[-1] if q else 0) # Pad with last value or 0

def run_simulation_and_collect_data(num_messages=100, capacity=10):
    # Clear previous logs
    log_stream.seek(0)
    log_stream.truncate(0)

    producer = DataProducer(n=num_messages)
    processor = DataProcessor()
    consumer = DataConsumer()

    sg = Subgraph.from_nodes("observability_demo", [producer, processor, consumer])
    sg.connect(("producer", "out"), ("processor", "in"), capacity=capacity)
    sg.connect(("processor", "out"), ("consumer", "in"), capacity=capacity)

    scheduler = VisualizingScheduler(SchedulerConfig(tick_interval_ms=1, shutdown_timeout_s=10.0))
    scheduler.register(sg)

    print("🚀 Running simulation and collecting data...")
    scheduler.run()
    print("Simulation finished.")

    # Get all collected metrics from the VisualizingScheduler
    metrics_raw = {
        "queue_depth_history": scheduler.queue_depth_history,
        "message_counts_history": scheduler.message_counts_history,
        "timestamps": scheduler.timestamps,
    }
    
    # Get all collected logs
    logs = log_stream.getvalue()
    
    return logs, metrics_raw, consumer.received_messages

logs_raw, metrics_raw, consumed_messages = run_simulation_and_collect_data(num_messages=200, capacity=5)

print(f"\nTotal consumed messages: {len(consumed_messages)}")
# -

# ## 5. Analyzing Logs

# We'll parse the raw JSON logs into a Pandas DataFrame for easier filtering and analysis.

# +
log_lines = logs_raw.strip().split('\n')
log_data = [json.loads(line) for line in log_lines if line.strip()]
logs_df = pd.DataFrame(log_data)

# Convert timestamp to datetime for better readability
logs_df['ts_datetime'] = pd.to_datetime(logs_df['ts'], unit='s')

print("Sample Log Entries:")
display(logs_df.head())

# Filter logs for specific events, e.g., message processing
message_processing_logs = logs_df[logs_df['event'] == 'processing.start']
print("\nSample Message Processing Logs:")
display(message_processing_logs.head())

# You can further filter by node, port, message_type, etc.
producer_emits = logs_df[(logs_df['node'] == 'producer') & (logs_df['event'] == 'scheduler.message_put_result')]
print("\nSample Producer Emit Results:")
display(producer_emits.head())
# -

# ## 6. Analyzing Metrics

# We'll extract relevant metrics and visualize them over time.

# +
# Extract queue depth metrics
queue_depth_metrics = []
if 'queue_depth_history' in metrics_raw and 'timestamps' in metrics_raw:
    timestamps = metrics_raw['timestamps']
    for edge_id, history in metrics_raw['queue_depth_history'].items():
        for i, value in enumerate(history):
            queue_depth_metrics.append({
                'timestamp': timestamps[i],
                'value': value,
                'edge_id': edge_id
            })

queue_depth_df = pd.DataFrame(queue_depth_metrics)
queue_depth_df['timestamp'] = pd.to_datetime(queue_depth_df['timestamp'], unit='s')

if not queue_depth_df.empty:
    fig = px.line(queue_depth_df, x='timestamp', y='value', color='edge_id', title='Queue Depth Over Time')
    fig.update_layout(yaxis_title='Queue Depth')
    fig.show()
else:
    print("No queue depth metrics to display.")

# Extract message processing rates
message_counts = []
if 'message_counts_history' in metrics_raw and 'timestamps' in metrics_raw:
    timestamps = metrics_raw['timestamps']
    for node_name, history in metrics_raw['message_counts_history'].items():
        for i, value in enumerate(history):
            message_counts.append({
                'timestamp': timestamps[i],
                'value': value,
                'node': node_name
            })

message_counts_df = pd.DataFrame(message_counts)
message_counts_df['timestamp'] = pd.to_datetime(message_counts_df['timestamp'], unit='s')

if not message_counts_df.empty:
    # Calculate rate as difference between consecutive values for each node
    message_rates_df = message_counts_df.sort_values(by=['node', 'timestamp'])
    message_rates_df['rate'] = message_rates_df.groupby('node')['value'].diff().fillna(0)
    
    fig = px.line(message_rates_df, x='timestamp', y='rate', color='node', title='Message Processing Rate')
    fig.update_layout(yaxis_title='Messages Processed per Tick')
    fig.show()
else:
    print("No message processing metrics to display.")
# -

# ## 7. Conclusion

# This notebook provides a foundation for analyzing observability data from Meridian Runtime. By combining structured logging with metrics, you can gain deep insights into your dataflow's performance and behavior.
