
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

# # Streaming Coalesce Demo (Interactive)

# This notebook demonstrates the `Coalesce` backpressure policy in Meridian Runtime. The `Coalesce` policy is useful for merging multiple messages into a single aggregate message when the downstream consumer is slower than the producer, thus reducing pressure on the system.

# ## 1. Setup: Add Project to Python Path

# This cell adds the project's `src` directory to the Python path. This is necessary for the notebook to find and import the `meridian` module.

# +
import sys
import os

# Add the project's 'src' directory to the Python path
# This is necessary for the notebook to find the 'meridian' module
# We assume the notebook is run from the 'notebooks/examples' directory.
src_path = os.path.abspath('../../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added '{src_path}' to the Python path.")
# -

# ## 2. Domain Model

# We define `SensorReading` to represent individual data points and `WindowAgg` to represent aggregated data. The `merge_window` function is crucial for the `Coalesce` policy, as it defines how two `WindowAgg` objects are combined.

# +
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Any

@dataclass(frozen=True, slots=True)
class SensorReading:
    ts: float
    value: float

@dataclass(frozen=True, slots=True)
class WindowAgg:
    count: int
    sum: float
    min_v: float
    max_v: float

    @property
    def avg(self) -> float:
        return 0.0 if self.count == 0 else self.sum / self.count

def merge_window(a: WindowAgg, b: WindowAgg) -> WindowAgg:
    """
    Pure, deterministic merge function for rolling window aggregates.

    The Edge configured with Coalesce(fn=merge_window) will call this when capacity is hit,
    replacing the last queued item with a merged one to reduce pressure.
    """
    return WindowAgg(
        count=a.count + b.count,
        sum=a.sum + b.sum,
        min_v=min(a.min_v, b.min_v),
        max_v=max(a.max_v, b.max_v),
    )
# -

# ## 3. Pipeline Nodes

# Here are the definitions for the nodes that make up our streaming coalesce pipeline:

# *   **SensorNode**: Emits `SensorReading` at a configurable rate.
# *   **WindowAggNode**: Converts `SensorReading` to per-item `WindowAgg`.
# *   **SinkNode**: Prints aggregate snapshots and periodic summaries.

# +
from meridian.core import (
    Message,
    MessageType,
    Node,
    Port,
    PortDirection,
    PortSpec,
    Scheduler,
    SchedulerConfig,
    Subgraph,
)
from meridian.core.policies import Coalesce, Policy
from meridian.observability.config import ObservabilityConfig, configure_observability
from meridian.observability.logging import get_logger, with_context


class SensorNode(Node):
    """
    Emits SensorReading at a configurable rate. Uses ticks as the pacing mechanism.
    """

    def __init__(self, name: str = "sensor", rate_hz: float = 200.0) -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", SensorReading))],
        )
        self._last_emit = 0.0
        self._period = 1.0 / max(1e-6, rate_hz)
        self._rng = random.Random(1234)

    def _handle_tick(self) -> None:
        now = time.monotonic()
        if now - self._last_emit >= self._period:
            self._last_emit = now
            reading = SensorReading(ts=time.time(), value=0.5 + self._rng.random())
            self.emit("out", Message(MessageType.DATA, reading))


class WindowAggNode(Node):
    """
    Converts SensorReading to per-item WindowAgg (count=1), downstream coalescing merges bursts.

    Demonstrates:
      - Deterministic coalescing function
      - Low per-item overhead (one tuple allocation)
    """

    def __init__(self, name: str = "agg") -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", SensorReading))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", WindowAgg))],
        )

    def _handle_message(self, port: str, msg: Message) -> None:
        # Strictly validate payload type to prevent AttributeError
        payload = msg.payload
        if not isinstance(payload, SensorReading):
            logger = get_logger()
            with with_context(node=self.name, port=port):
                logger.warn(
                    "agg.invalid_payload",
                    f"Ignoring non-SensorReading payload type={type(payload).__name__}",
                )
            return

        reading: SensorReading = payload
        agg = WindowAgg(count=1, sum=reading.value, min_v=reading.value, max_v=reading.value)
        self.emit("out", Message(MessageType.DATA, agg))


class SinkNode(Node):
    """
    Prints aggregate snapshots and periodic summaries. Keeps a small ring buffer.
    """

    def __init__(self, name: str = "sink", keep: int = 10, verbose: bool = True) -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", WindowAgg))],
            outputs=[],
        )
        self._keep = keep
        self._verbose = verbose
        self._buf: List[WindowAgg] = []
        self._last_summary = 0.0

    def _handle_message(self, port: str, msg: Message) -> None:
        agg: WindowAgg = msg.payload
        self._buf.append(agg)
        if len(self._buf) > self._keep:
            self._buf.pop(0)

        if self._verbose:
            logger = get_logger()
            with with_context(node=self.name):
                logger.info(
                    "sink.item",
                    f"count={agg.count} avg={agg.avg:.4f} min={agg.min_v:.4f} max={agg.max_v:.4f}",
                )

    def _handle_tick(self) -> None:
        now = time.monotonic()
        if now - self._last_summary >= 1.0:
            self._last_summary = now
            if not self._buf:
                return
            # Summarize last window
            total = WindowAgg(count=0, sum=0.0, min_v=float("inf"), max_v=float("-inf"))
            for a in self._buf:
                total = merge_window(total, a)

            logger = get_logger()
            with with_context(node=self.name):
                logger.info(
                    "sink.summary",
                    f"window_size={len(self._buf)} total_count={total.count} "
                    f"avg={total.avg:.4f} min={total.min_v:.4f} max={total.max_v:.4f}",
                )
# -

# ## 4. Interactive Controls and Running the Pipeline

# Use the widgets below to configure and run the streaming coalesce pipeline.

# +
import ipywidgets as widgets
from IPython.display import display
import threading

# Configure observability for the notebook
configure_observability(
    ObservabilityConfig(
        log_level="INFO",
        log_json=False,  # Human-readable logs for notebook
        metrics_enabled=False,
        tracing_enabled=False,
    )
)

# Create widgets for pipeline parameters
rate_hz_slider = widgets.FloatSlider(value=300.0, min=50.0, max=1000.0, step=50.0, description='Sensor Rate (Hz):')
tick_ms_slider = widgets.IntSlider(value=10, min=1, max=100, step=1, description='Scheduler Tick (ms):')
max_batch_slider = widgets.IntSlider(value=16, min=1, max=64, step=1, description='Max Batch Size:')
timeout_s_slider = widgets.FloatSlider(value=5.0, min=1.0, max=30.0, step=1.0, description='Shutdown Timeout (s):')
cap_sensor_to_agg_slider = widgets.IntSlider(value=256, min=64, max=1024, step=64, description='Capacity: Sensor to Agg:')
cap_agg_to_sink_slider = widgets.IntSlider(value=16, min=4, max=64, step=4, description='Capacity: Agg to Sink:')
keep_slider = widgets.IntSlider(value=10, min=1, max=50, step=1, description='Sink Buffer Size:')
quiet_checkbox = widgets.Checkbox(value=False, description='Quiet Sink (reduce per-item logs)')

run_button = widgets.Button(description='Run Streaming Coalesce Pipeline')
output_area = widgets.Output()

def run_streaming_coalesce_pipeline(b):
    with output_area:
        output_area.clear_output()
        print("=== Starting Streaming Coalesce Demo ===")

        sensor = SensorNode(rate_hz=rate_hz_slider.value)
        agg = WindowAggNode()
        sink = SinkNode(keep=keep_slider.value, verbose=not quiet_checkbox.value)

        g = Subgraph.from_nodes("streaming_coalesce", [sensor, agg, sink])

        # Sensor -> Agg: normal capacity
        g.connect((sensor.name, "out"), (agg.name, "in"), capacity=cap_sensor_to_agg_slider.value)

        # Agg -> Sink: small capacity with explicit Coalesce policy to merge bursts deterministically
        g.connect(
            (agg.name, "out"),
            (sink.name, "in"),
            capacity=cap_agg_to_sink_slider.value,
            policy=Coalesce(lambda a, b: merge_window(a, b)),  # type: ignore[arg-type]
        )

        sched = Scheduler(
            SchedulerConfig(
                tick_interval_ms=tick_ms_slider.value,
                fairness_ratio=(4, 2, 1),
                max_batch_per_node=max_batch_slider.value,
                idle_sleep_ms=1,
                shutdown_timeout_s=timeout_s_slider.value,
            )
        )

        sched.register(g)

        logger = get_logger()
        with with_context(node="driver"):
            logger.info(
                "demo.start",
                "Streaming coalesce demo starting",
                rate_hz=rate_hz_slider.value,
                cap_agg_to_sink=cap_agg_to_sink_slider.value,
            )

        # Run in a separate thread to keep notebook interactive
        pipeline_thread = threading.Thread(target=sched.run)
        pipeline_thread.start()
        pipeline_thread.join() # Wait for pipeline to complete

        with with_context(node="driver"):
            logger.info("demo.stop", "Streaming coalesce demo stopped")

        print("=== Streaming Coalesce Demo Finished ===")

run_button.on_click(run_streaming_coalesce_pipeline)

display(
    rate_hz_slider,
    tick_ms_slider,
    max_batch_slider,
    timeout_s_slider,
    cap_sensor_to_agg_slider,
    cap_agg_to_sink_slider,
    keep_slider,
    quiet_checkbox,
    run_button,
    output_area
)
# -
