

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

# # Pipeline Demo (Interactive)

# This notebook demonstrates a simple data processing pipeline with multiple stages: validation, transformation, and a slow sink. It also includes a control-plane kill switch to gracefully shut down the pipeline.

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

# ## 2. Pipeline Nodes

# Let's define the nodes that make up our pipeline:

# * **Validator**: Drops invalid inputs, emits valid items only.
# * **Transformer**: Normalizes payloads and forwards.
# * **SlowSink**: Simulates I/O latency to trigger backpressure.
# * **KillSwitch**: Publishes a shutdown signal on control-plane edge.

# +
from __future__ import annotations

import time
from typing import Any

from meridian.core import Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Validator(Node):
    """Drops invalid inputs, emits valid items only."""

    def __init__(self) -> None:
        super().__init__(
            name="validator",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", dict))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", dict))],
        )
        self.seen: int = 0
        self.valid: int = 0

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port != "in":
            return
        self.seen += 1
        payload = msg.payload
        if isinstance(payload, dict) and "id" in payload:
            self.valid += 1
            self.emit("out", Message(type=MessageType.DATA, payload=payload))


class Transformer(Node):
    """Normalizes payloads and forwards."""

    def __init__(self) -> None:
        super().__init__(
            name="transformer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", dict))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", dict))],
        )

    def _handle_message(self, port: str, msg: Message[dict[str, Any]]) -> None:
        if port != "in":
            return
        payload = dict(msg.payload)
        payload.setdefault("normalized", True)
        self.emit("out", Message(type=MessageType.DATA, payload=payload))


class SlowSink(Node):
    """Simulates I/O latency to trigger backpressure."""

    def __init__(self, delay_s: float = 0.02) -> None:
        super().__init__(
            name="sink",
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", dict)),
                Port("control", PortDirection.INPUT, spec=PortSpec("control", str)),
            ],
            outputs=[],
        )
        self.delay_s = delay_s
        self.count = 0

    def _handle_message(self, port: str, msg: Message[Any]) -> None:
        if port == "in":
            time.sleep(self.delay_s)
            self.count += 1
        elif port == "control":
            print(f"Sink received control message: {msg.payload}")


class KillSwitch(Node):
    """Publishes a shutdown signal on control-plane edge."""

    def __init__(self) -> None:
        super().__init__(
            name="control",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
        )
        self.triggered = False

    def _handle_tick(self) -> None:
        if self.triggered:
            return
        self.triggered = True
        self.emit("out", Message(type=MessageType.CONTROL, payload="shutdown"))
# -

# ## 3. Building and Running the Pipeline

# Now, let's build the pipeline and run it with the scheduler. We'll also add a simple producer to feed messages into the pipeline.

# +
from meridian.core import Subgraph, Scheduler
import ipywidgets as widgets
from IPython.display import display
import threading

class SimpleProducer(Node):
    def __init__(self, num_messages: int = 10):
        super().__init__(
            name="simple_producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", dict))],
        )
        self.num_messages = num_messages
        self.count = 0

    def _handle_tick(self) -> None:
        if self.count < self.num_messages:
            self.emit("out", Message(payload={"id": self.count, "data": f"message_{self.count}"}))
            self.count += 1
        else:
            # Stop the producer once all messages are sent
            self.stop()

# Create a slider for the number of messages
message_slider = widgets.IntSlider(value=10, min=1, max=100, step=1, description='Messages:')

# Create a button to run the pipeline
run_button = widgets.Button(description='Run Pipeline')

# Create an output widget to display results
output_area = widgets.Output()

def run_pipeline(b):
    with output_area:
        output_area.clear_output()
        print("=== Starting Pipeline Demo ===")

        # Create nodes
        validator = Validator()
        transformer = Transformer()
        sink = SlowSink(delay_s=0.01) # Small delay to show backpressure
        kill_switch = KillSwitch()
        producer = SimpleProducer(num_messages=message_slider.value)

        # Create subgraph and connect nodes
        sg = Subgraph.from_nodes("pipeline_demo", [validator, transformer, sink, kill_switch, producer])

        # Data pipeline
        sg.connect(("simple_producer", "out"), ("validator", "in"), capacity=64)
        sg.connect(("validator", "out"), ("transformer", "in"), capacity=64)
        sg.connect(("transformer", "out"), ("sink", "in"), capacity=8)

        # Control plane
        sg.connect(("control", "out"), ("sink", "control"), capacity=1) # Kill switch to sink

        # Create scheduler and run
        sched = Scheduler()
        sched.register(sg)

        # Run in a separate thread to keep notebook interactive
        pipeline_thread = threading.Thread(target=sched.run)
        pipeline_thread.start()
        pipeline_thread.join() # Wait for pipeline to complete

        print(f"\nSink processed {sink.count} messages.")
        print("=== Pipeline Demo Finished ===")

run_button.on_click(run_pipeline)

display(message_slider, run_button, output_area)
# -

