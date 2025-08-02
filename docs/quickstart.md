# Quickstart

Prerequisites
- Python 3.11+
- uv: https://docs.astral.sh/uv/

Clone and setup
- git clone <repo-url>; cd Arachne
- uv lock; uv sync

Run examples
- uv run python -m examples.hello_graph.main
- uv run python -m examples.pipeline_demo.main

Author your first node
```python
from arachne.core import Node, Message

class Printer(Node):
    def __init__(self):
        super().__init__("printer", inputs=[], outputs=[])
    def _handle_message(self, port, msg):
        print("payload=", msg.payload)
```

Wire a subgraph and run
```python
from arachne.core import Subgraph, Scheduler, Message, Node
from arachne.core.ports import Port, PortDirection, PortSpec
from arachne.core.policies import latest

class Producer(Node):
    def __init__(self):
        super().__init__("producer", outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))])
    def _handle_tick(self):
        self.emit("out", Message(type=MessageType.DATA, payload=1))

class Consumer(Node):
    def __init__(self):
        super().__init__("consumer", inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))])
    def _handle_message(self, port, msg):
        print(msg.payload)

sg = Subgraph.from_nodes("hello", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=16, spec=PortSpec("in", int))
Scheduler().register(sg)
Scheduler().run()
```

Dev loop
- uv run ruff check .
- uv run black --check .
- uv run mypy src
- uv run pytest -q

Troubleshooting
- If uv not found: install uv, redo lock/sync
- If type mismatch: ensure PortSpec.schema matches Message.payload type
