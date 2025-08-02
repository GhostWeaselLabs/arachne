# Quickstart

## Prerequisites
- Python 3.11+
- uv: https://docs.astral.sh/uv/ (manages a virtualenv automatically for uv run)

## Clone and setup
```bash
git clone <repo-url>
cd meridian-runtime
uv lock
uv sync
```

## Run examples
```bash
uv run python -m examples.hello_graph.main
uv run python -m examples.pipeline_demo.main
```

## Author your first node
```python
from meridian.core import Node, Message

class Printer(Node):
    def __init__(self):
        super().__init__("printer", inputs=[], outputs=[])
    def _handle_message(self, port: str, msg: Message) -> None:
        print("payload=", msg.payload)
```

## Wire a subgraph and run
```python
from meridian.core import Subgraph, Scheduler, Message, MessageType, Node
from meridian.core.ports import Port, PortDirection, PortSpec

class Producer(Node):
    def __init__(self):
        super().__init__(
            "producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
    def _handle_tick(self) -> None:
        self.emit("out", Message(type=MessageType.DATA, payload=1))

class Consumer(Node):
    def __init__(self):
        super().__init__(
            "consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
    def _handle_message(self, port: str, msg: Message) -> None:
        print(msg.payload)

sg = Subgraph.from_nodes("hello", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=16)
Scheduler().register(sg)
Scheduler().run()
```

## Dev loop
```bash
uv run ruff check .
uv run black --check .
uv run mypy src
uv run pytest -q
```

## Troubleshooting
- If uv is not found, install uv and then initialize the environment:
  ```bash
  uv lock
  uv sync
  ```
- If you see a type mismatch on enqueue, ensure PortSpec.schema matches the type of Message.payload (e.g., PortSpec("in", int) with payload=int).
- If imports fail when running examples, use module form with uv:
  ```bash
  uv run python -m examples.hello_graph.main
  ```
