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

# # Control-Plane Priorities

# This notebook demonstrates how to use control-plane messages to prioritize critical operations in Meridian Runtime. In a real-time dataflow, it's often necessary to ensure that certain messages, such as shutdown commands or configuration updates, are processed before normal data messages. Meridian Runtime provides a mechanism for this called **control-plane priorities**.

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

# ## 2. The Problem: Starvation

# In a busy dataflow, it's possible for a high volume of data messages to "starve" control messages. This means that the control messages may be stuck in a queue for a long time, waiting for the data messages to be processed. This can be a serious problem if the control messages are time-sensitive, such as a command to shut down the system.

# ## 3. Meridian Runtime's Solution: Control-Plane Priorities

# Meridian Runtime solves this problem by giving priority to **control messages**. Control messages are messages with the `MessageType.CONTROL` type. When the scheduler selects the next message to process, it will always choose a control message over a data message if one is available.

# ## 4. Demonstrating Control-Plane Priorities

# Let's see how this works in practice. We'll use a graph with a worker node that can be controlled by a controller node.

# ### 4.1. The Worker and Controller Nodes

# First, let's define the worker and controller nodes.

# +
from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection

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

    def _handle_message(self, port, msg):
        if port == "ctl" and msg.type == MessageType.CONTROL:
            cmd = str(msg.payload).strip().lower()
            print(f"Received control message: {cmd}")
            if cmd in {"normal", "quiet"}:
                self._mode = cmd
            return
        if port == "in" and self._mode != "quiet":
            print(f"Processing data message: {msg.payload}")
            self.emit("out", Message(MessageType.DATA, msg.payload))

class Controller(Node):
    def __init__(self):
        super().__init__("controller", inputs=[], outputs=[Port("ctl", PortDirection.OUTPUT, spec=PortSpec("ctl", str))])
        self._sent = False

    def _handle_tick(self):
        if not self._sent:
            print("Sending control message")
            self.emit("ctl", Message(MessageType.CONTROL, "quiet"))
            self._sent = True

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
            print(f"Producing message {self._i}")
            self.emit("out", Message(payload=self._i))
            self._i += 1
# -

# ### 4.2. Building and Running the Graph

# Now, let's wire up the nodes in a subgraph and run it with the scheduler.

# +
# Create a subgraph
sg = Subgraph.from_nodes("ctl_demo", [Worker(), Controller(), Producer()])

# Control edge: small capacity; scheduler treats CONTROL with higher priority.
sg.connect(("controller","ctl"), ("worker","ctl"), capacity=4)

# Data edge
sg.connect(("producer","out"), ("worker","in"), capacity=4)

# Create a scheduler and register the subgraph
scheduler = Scheduler()
scheduler.register(sg)

# Run the scheduler
scheduler.run()
# -

# ## 5. Conclusion

# This notebook has demonstrated how to use control-plane priorities to ensure that critical messages are processed in a timely manner. By using `MessageType.CONTROL` for your control messages, you can build robust and reliable dataflows that can handle high volumes of data without starving critical operations.