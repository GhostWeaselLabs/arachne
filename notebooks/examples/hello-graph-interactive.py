
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

# # Hello, Graph! (Interactive)

# This notebook is an interactive version of the `hello-graph` example. It demonstrates how to build and run a simple graph with a producer and a consumer, and how to interact with it using widgets.

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

# ## 2. The Producer and Consumer Nodes

# First, let's define the producer and consumer nodes. The producer will emit a sequence of integers, and the consumer will receive them and store them in a list.

# +
from meridian.core import Node, Message, MessageType, Port, PortDirection, PortSpec

class Producer(Node):
    def __init__(self, n=5):
        super().__init__(
            name="producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))]
        )
        self._n = n
        self._i = 0

    def on_start(self):
        self._i = 0

    def _handle_tick(self):
        if self._i < self._n:
            print(f"Producer emitting: {self._i}")
            self.emit("out", Message(type=MessageType.DATA, payload=self._i))
            self._i += 1

class Consumer(Node):
    def __init__(self):
        super().__init__(
            name="consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[]
        )
        self.values = []

    def _handle_message(self, port, msg):
        print(f"Consumer received: {msg.payload}")
        self.values.append(msg.payload)
# -

# ## 3. Building and Running the Graph

# Now, let's build the graph and run it with the scheduler. We'll use a slider to control the number of messages the producer emits.

# +
import ipywidgets as widgets
from IPython.display import display
from meridian.core import Subgraph, Scheduler, SchedulerConfig

# Create a slider to control the number of messages
slider = widgets.IntSlider(value=5, min=1, max=10, description='Messages:')

# Create a button to run the graph
button = widgets.Button(description='Run Graph')

# Create an output widget to display the results
output = widgets.Output()

def run_graph(b):
    with output:
        output.clear_output()
        print(f"🚀 Running graph with {slider.value} messages...")
        
        # Create a subgraph
        graph = Subgraph(name="hello_graph")

        # Add the producer and consumer nodes
        producer = Producer(n=slider.value)
        consumer = Consumer()
        graph.add_node(producer)
        graph.add_node(consumer)

        # Connect the producer and consumer
        graph.connect(("producer", "out"), ("consumer", "in"))

        # Create a scheduler and register the subgraph
        scheduler = Scheduler(SchedulerConfig(
            tick_interval_ms=100,
            shutdown_timeout_s=2.0
        ))
        scheduler.register(graph)

        # Run the scheduler
        scheduler.run()

        print(f"✅ Consumer received: {consumer.values}")

button.on_click(run_graph)

display(slider, button, output)
# -
