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

# # Backpressure Policies

# This notebook demonstrates the different backpressure policies available in Meridian Runtime. Backpressure is a critical mechanism for building robust and resilient dataflows. It allows a system to gracefully handle load spikes and prevent downstream components from being overwhelmed.

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

# ## 2. The Problem: Unbounded Queues

# In a typical dataflow, a producer sends messages to a consumer through a queue. If the producer is faster than the consumer, the queue will grow indefinitely, eventually leading to memory exhaustion and system failure. This is known as the "unbounded queue" problem.

# ## 3. Meridian Runtime's Solution: Bounded Edges and Backpressure Policies

# Meridian Runtime solves this problem by using **bounded edges** (queues with a fixed capacity) and **backpressure policies**. When an edge is full, the runtime applies a backpressure policy to prevent the queue from growing further. Meridian Runtime provides four backpressure policies:

# * **Block**: The producer is blocked until space becomes available in the queue. This is the default policy.
# * **Drop**: The new message is dropped.
# * **Latest**: The oldest message in the queue is dropped to make space for the new message.
# * **Coalesce**: The new message is merged with an existing message in the queue.

# ## 4. Demonstrating the Backpressure Policies

# Let's see how these policies work in practice. We'll use a simple graph with a fast producer and a slow consumer to simulate a load spike.

# ### 4.1. The Base Graph

# First, let's define the producer and consumer nodes.

# +
import time
from meridian.core import Node, Message

from meridian.core import MessageType, Port, PortDirection, PortSpec

class FastProducer(Node):
    def __init__(self, n=10):
        super().__init__(
            name="producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
        self._n = n
        self._i = 0

    def on_start(self):
        self._i = 0

    def _handle_tick(self):
        if self._i < self._n:
            print(f"Producing message {self._i}")
            self.emit("out", Message(type=MessageType.DATA, payload=self._i))
            self._i += 1

class SlowConsumer(Node):
    def __init__(self):
        super().__init__(
            name="consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )

    def _handle_message(self, port, msg):
        print(f"Consuming message: {msg.payload}")
        time.sleep(0.1) # Simulate a slow consumer
# -

# ### 4.2. The "Block" Policy (Default)

# The "Block" policy is the default policy. When the edge is full, the producer is blocked until the consumer has processed a message and freed up space in the queue.

# +
from meridian.core import Subgraph, Scheduler

# Create a subgraph
graph = Subgraph(name="block_policy_graph")

# Add the producer and consumer nodes
graph.add_node(FastProducer(n=5))
graph.add_node(SlowConsumer())

# Connect the producer and consumer with a small capacity
graph.connect(("producer", "out"), ("consumer", "in"), capacity=2)

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(graph)

# Run the scheduler
scheduler.run()
# -

# ### 4.3. The "Drop" Policy

# The "Drop" policy simply drops the new message when the edge is full.

# +
from meridian.core import Subgraph, Scheduler
from meridian.core.policies import drop

# Create a subgraph
graph = Subgraph(name="drop_policy_graph")

# Add the producer and consumer nodes
graph.add_node(FastProducer(n=5))
graph.add_node(SlowConsumer())

# Connect the producer and consumer with the "Drop" policy
graph.connect(("producer", "out"), ("consumer", "in"), capacity=2, policy=drop())

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(graph)

# Run the scheduler
scheduler.run()
# -

# ### 4.4. The "Latest" Policy

# The "Latest" policy drops the oldest message in the queue to make space for the new message.

# +
from meridian.core import Subgraph, Scheduler
from meridian.core.policies import latest

# Create a subgraph
graph = Subgraph(name="latest_policy_graph")

# Add the producer and consumer nodes
graph.add_node(FastProducer(n=5))
graph.add_node(SlowConsumer())

# Connect the producer and consumer with the "Latest" policy
graph.connect(("producer", "out"), ("consumer", "in"), capacity=2, policy=latest())

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(graph)

# Run the scheduler
scheduler.run()
# -

# ## 5. Conclusion

# This notebook has demonstrated the different backpressure policies available in Meridian Runtime. By choosing the right policy for your use case, you can build robust and resilient dataflows that can handle load spikes and prevent system failures.