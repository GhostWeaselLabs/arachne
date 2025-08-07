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

# # Getting Started with Meridian Runtime

# This notebook provides a hands-on introduction to the core concepts of Meridian Runtime. We'll build a simple "Hello, World!" graph with a producer, a consumer, and an edge connecting them.

# ## 1. Setup: Add Project to Python Path

# This cell adds the project's `src` directory to the Python path. This is necessary for the notebook to find and import the `meridian` module.

# +
import sys
import os

# Add the project's 'src' directory to the Python path
# This is necessary for the notebook to find the 'meridian' module
# We assume the notebook is run from the 'notebooks/tutorials' directory.
src_path = os.path.abspath('../../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added '{src_path}' to the Python path.")
# -

# ## 2. Core Concepts

# Meridian Runtime is based on a few simple primitives:

# * **Node**: A single-responsibility processing unit.
# * **Edge**: A typed, bounded queue connecting nodes.
# * **Subgraph**: A composition of nodes and edges.
# * **Scheduler**: Drives the execution of the graph.

# ## 3. The "Hello, World!" Example

# Let's start by defining a simple producer node that emits a sequence of integers.

# +
from meridian.core import Node, Message

class Producer(Node):
    def __init__(self, n=5):
        super().__init__(name="producer")
        self._n = n
        self._i = 0

    def on_start(self):
        self._i = 0

    def on_tick(self):
        if self._i < self._n:
            print(f"Producing message {self._i}")
            self.emit("out", Message(payload=self._i))
            self._i += 1
# -

# Next, we'll define a consumer node that receives the integers and prints them.

# +
from meridian.core import Node

class Consumer(Node):
    def __init__(self):
        super().__init__(name="consumer")

    def on_message(self, port, msg):
        print(f"Consumed message: {msg.payload}")
# -

# ## 4. Building and Running the Graph

# Now, let's wire up the producer and consumer in a subgraph and run it with the scheduler.

# +
from meridian.core import Subgraph, Scheduler

# Create a subgraph
graph = Subgraph(name="hello_world")

# Add the producer and consumer nodes
graph.add_node(Producer(n=3))
graph.add_node(Consumer())

# Connect the producer's "out" port to the consumer's "in" port
graph.connect(("producer", "out"), ("consumer", "in"))

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(graph)

# Run the scheduler
scheduler.run()
# -

# ## 5. Conclusion

# You've successfully built and run your first Meridian Runtime graph! This simple example demonstrates the core concepts of nodes, edges, and the scheduler. In the next tutorial, we'll explore backpressure and overflow policies.