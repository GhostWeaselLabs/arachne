# Patterns

This page shows common graph patterns with minimal examples. See also: ./api.md for API details and semantics.

## Backpressure and overflow

- block: apply backpressure upstream; default
- drop: drop new messages when full
- latest: keep only newest beyond capacity
- coalesce: merge bursts via function

Example: latest (keep only newest)
```python
from arachne.core import Subgraph, Scheduler, Node, Message, MessageType, PortSpec
from arachne.core.ports import Port, PortDirection
from arachne.core.policies import Latest

class Producer(Node):
    def __init__(self):
        super().__init__(
            "producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
    def _handle_tick(self):
        self.emit("out", Message(type=MessageType.DATA, payload=1))

class Consumer(Node):
    def __init__(self):
        super().__init__(
            "consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
    def _handle_message(self, port, msg):
        print("got", msg.payload)

sg = Subgraph.from_nodes("p_latest", [Producer(), Consumer()])
# Capacity=4, keep only latest when full
sg.connect(("producer","out"), ("consumer","in"), capacity=4, policy=Latest())
Scheduler().register(sg)
Scheduler().run()
```

Other policies
- block (default): apply backpressure
```python
sg.connect(("producer","out"), ("consumer","in"), capacity=16)  # default: block
```

- drop: drop when full
```python
from arachne.core.policies import Drop
sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=Drop())
```

- coalesce: merge bursts via a function
```python
from arachne.core.policies import Coalesce
def combine(old, new):
    return new  # or custom logic to merge items
sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=Coalesce(combine))
```

See overflow semantics in ./api.md.

## Control-plane priority

Use higher priority edges for kill switches or coordination. Control-plane messages can preempt data-plane work for predictable behavior under load. See Scheduler priorities in ./api.md.

## Subgraph composition

- Expose input/output ports; validate wiring; ensure schema compatibility.
- Reuse subgraphs by composing them and exposing a clean surface.

Minimal example
```python
from arachne.core import Subgraph, Node, PortSpec, Message, MessageType
from arachne.core.ports import Port, PortDirection

class Upper(Node):
    def __init__(self):
        super().__init__(
            "upper",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
        )
    def _handle_message(self, port, msg):
        self.emit("out", Message(type=MessageType.DATA, payload=msg.payload.upper()))

class Printer(Node):
    def __init__(self):
        super().__init__(
            "printer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[],
        )
    def _handle_message(self, port, msg):
        print(msg.payload)

sg = Subgraph.from_nodes("upper_print", [Upper(), Printer()])
sg.connect(("upper","out"), ("printer","in"), capacity=8)
```

## Error handling

- Handle exceptions in node hooks; the default policy is skip/continue and log structured errors.
- Prefer small try/except blocks inside `_handle_message` and `_handle_tick` to localize failures.
- Emit diagnostics through observability hooks; see ./observability.md.
