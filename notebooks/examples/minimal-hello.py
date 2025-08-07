

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

# # Minimal Hello World

# This notebook demonstrates the basic concepts of Meridian Runtime:
# - Creating nodes with typed ports
# - Connecting nodes with bounded edges
# - Running a simple dataflow

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

# First, let's define the producer and consumer nodes.

# +
from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Producer(Node):
    """Produces integer messages on tick intervals."""

    def __init__(self, name: str = "producer", max_count: int = 5):
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("output", PortDirection.OUTPUT, spec=PortSpec("output", int))],
        )
        self.max_count = max_count
        self.count = 0

    def _handle_tick(self) -> None:
        if self.count < self.max_count:
            self.emit("output", Message(type=MessageType.DATA, payload=self.count))
            self.count += 1


class Consumer(Node):
    """Consumes and prints integer messages."""

    def __init__(self, name: str = "consumer"):
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
        self.values = []

    def _handle_message(self, port: str, msg: Message) -> None:
        if port == "in":
            self.values.append(msg.payload)
            print(f"Consumer received: {msg.payload}")
# -

# ## 3. Building and Running the Graph

# Now, let's build the graph and run it with the scheduler.

# +
# Create nodes
producer = Producer(max_count=5)
consumer = Consumer()

# Create subgraph and connect nodes
sg = Subgraph.from_nodes("hello_world", [producer, consumer])
sg.connect(("producer", "output"), ("consumer", "in"), capacity=8)

# Create scheduler and run
sch = Scheduler()
sch.register(sg)

print("Starting dataflow...")
sch.run()

print(f"\nConsumer processed {len(consumer.values)} messages")
print("✓ Example completed successfully!")
# -

