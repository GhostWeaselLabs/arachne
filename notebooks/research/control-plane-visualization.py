

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

# # Control-Plane Priority Visualization

# This notebook demonstrates the effect of control-plane messages on data flow and queue states in Meridian Runtime, using interactive visualizations.

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

# ## 2. Imports and Node Definitions

# We'll import necessary modules and define the `Worker`, `Controller`, and `Producer` nodes.

# +
import time
import threading
import plotly.graph_objects as go
from collections import deque

from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec, SchedulerConfig
from meridian.core.ports import Port, PortDirection
from meridian.observability.config import configure_observability, ObservabilityConfig

# Configure observability to capture logs for visualization
configure_observability(
    ObservabilityConfig(
        log_level="INFO",
        log_json=False, # Human-readable logs for this example
        metrics_enabled=False,
        tracing_enabled=False,
    )
)

class Worker(Node):
    def __init__(self):
        super().__init__(
            "worker",
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", int)),
                Port("ctl", PortDirection.INPUT, spec=PortSpec("ctl", str)),
            ],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
        self._mode = "normal"
        self.processed_data_messages = 0
        self.processed_control_messages = 0

    def _handle_message(self, port, msg):
        if port == "ctl" and msg.type == MessageType.CONTROL:
            cmd = str(msg.payload).strip().lower()
            print(f"Worker received control message: {cmd}")
            if cmd in {"normal", "quiet"}:
                self._mode = cmd
            self.processed_control_messages += 1
            return
        if port == "in" and self._mode != "quiet":
            # Simulate some work
            time.sleep(0.01) 
            self.processed_data_messages += 1
            # print(f"Worker processing data message: {msg.payload}")
            self.emit("out", Message(MessageType.DATA, msg.payload))

class Controller(Node):
    def __init__(self, control_interval_s=1.0):
        super().__init__("controller", inputs=[], outputs=[Port("ctl", PortDirection.OUTPUT, spec=PortSpec("ctl", str))])
        self._control_interval_s = control_interval_s
        self._last_control_time = time.monotonic()

    def _handle_tick(self):
        now = time.monotonic()
        if now - self._last_control_time >= self._control_interval_s:
            print("Controller sending control message: quiet")
            self.emit("ctl", Message(MessageType.CONTROL, "quiet"))
            self._last_control_time = now

class Producer(Node):
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
            # print(f"Producer emitting data message: {self._i}")
            self.emit("out", Message(type=MessageType.DATA, payload=self._i))
            self._i += 1
# -

# ## 3. Data Collection for Visualization

# We'll create a custom scheduler that records queue depths over time.

# +
class VisualizingScheduler(Scheduler):
    def __init__(self, config: SchedulerConfig | None = None):
        super().__init__(config)
        self.queue_depth_history = {
            "producer:out->worker:in": deque(),
            "controller:ctl->worker:ctl": deque(),
        }
        self.timestamps = deque()
        self._start_time = time.monotonic()

    def _run_main_loop(self) -> None:
        # Override to collect data
        super()._run_main_loop()
        
        # After the main loop, collect final queue depths
        self._collect_queue_depths()

    def _collect_queue_depths(self):
        current_time = time.monotonic() - self._start_time
        self.timestamps.append(current_time)
        
        for edge_id, edge_ref in self._plan.edges.items():
            if edge_id in self.queue_depth_history:
                self.queue_depth_history[edge_id].append(edge_ref.edge.depth())

    def run(self) -> None:
        # Wrap the original run method to collect data periodically
        self._start_time = time.monotonic()
        super().run()

        # Ensure all history deques have the same length for plotting
        max_len = max(len(q) for q in self.queue_depth_history.values())
        for q in self.queue_depth_history.values():
            while len(q) < max_len:
                q.append(q[-1] if q else 0) # Pad with last value or 0

# -

# ## 4. Building and Running the Graph with Visualization

# We'll set up the graph and run it using our `VisualizingScheduler`.

# +
import ipywidgets as widgets
from IPython.display import display

# Create widgets for configuration
duration_slider = widgets.FloatSlider(value=5.0, min=1.0, max=20.0, step=1.0, description='Duration (s):')
producer_messages_slider = widgets.IntSlider(value=100, min=10, max=1000, step=10, description='Producer Msgs:')
control_interval_slider = widgets.FloatSlider(value=1.0, min=0.1, max=5.0, step=0.1, description='Control Interval (s):')

run_button = widgets.Button(description='Run Simulation')
output_widget = widgets.Output()

def run_simulation(b):
    with output_widget:
        output_widget.clear_output()
        print("🚀 Running Control Plane Priority Simulation...")

        # Create nodes with interactive parameters
        worker = Worker()
        controller = Controller(control_interval_s=control_interval_slider.value)
        producer = Producer(n=producer_messages_slider.value)

        # Create subgraph
        sg = Subgraph.from_nodes("control_plane_demo", [worker, controller, producer])

        # Connect data edge
        sg.connect(("producer","out"), ("worker","in"), capacity=10) # Data queue

        # Connect control edge (higher priority by default)
        sg.connect(("controller","ctl"), ("worker","ctl"), capacity=1) # Control queue

        # Create and run visualizing scheduler
        scheduler_config = SchedulerConfig(
            tick_interval_ms=1, 
            shutdown_timeout_s=duration_slider.value + 2.0 # Add buffer for shutdown
        )
        scheduler = VisualizingScheduler(scheduler_config)
        scheduler.register(sg)
        
        # Run in a separate thread to keep notebook interactive
        sim_thread = threading.Thread(target=scheduler.run)
        sim_thread.start()
        sim_thread.join() # Wait for simulation to complete

        print("Simulation complete. Generating plot...")

        # Generate plot
        fig = go.Figure()

        for edge_id, history in scheduler.queue_depth_history.items():
            fig.add_trace(go.Scatter(x=list(scheduler.timestamps), y=list(history), mode='lines', name=f'Queue Depth: {edge_id}'))

        fig.update_layout(
            title='Queue Depth Over Time',
            xaxis_title='Time (s)',
            yaxis_title='Queue Depth',
            hovermode='x unified'
        )
        fig.show()
        
        print(f"\nWorker processed data messages: {worker.processed_data_messages}")
        print(f"Worker processed control messages: {worker.processed_control_messages}")

run_button.on_click(run_simulation)

display(
    duration_slider,
    producer_messages_slider,
    control_interval_slider,
    run_button,
    output_widget
)
# -

