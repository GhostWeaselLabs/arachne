---
title: Quickstart
description: Set up Meridian Runtime and run an example in under 60 seconds.
tags:
  - quickstart
  - setup
  - examples
---

# Quickstart {#quickstart}

Follow these steps to get started immediately.

## Prerequisites {#prerequisites}
- `Python 3.11+`
- `uv` package manager ([Install uv](https://docs.astral.sh/uv/))

## Setup {#setup}
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime.git
cd meridian-runtime
uv sync
```

## Test your setup {#test-your-setup}
```bash
# Create a simple test file
cat > test_setup.py << 'EOF'
from meridian.core import Node, Message, MessageType, Subgraph, Scheduler
from meridian.core.ports import Port, PortDirection, PortSpec

class TestNode(Node):
    def __init__(self):
        super().__init__(
            "test",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
        )
    
    def _handle_message(self, port: str, msg: Message) -> None:
        if port == "in":
            print(f"✓ Setup working! Received: {msg.payload}")
            self.emit("out", Message(type=MessageType.DATA, payload="success"))

sg = Subgraph.from_nodes("test", [TestNode()])
sg.connect(("test", "out"), ("test", "in"), capacity=1)

sch = Scheduler()
sch.register(sg)
test_node = sg.nodes[0]
test_node.emit("in", Message(type=MessageType.DATA, payload="Hello Meridian!"))
sch.run()
EOF

# Run the test
uv run python test_setup.py
```

Expected output: `✓ Setup working! Received: Hello Meridian!`

!!! success "Setup Complete"
    Your Meridian Runtime installation is working correctly!

## Run an example {#run-an-example}
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
uv run python examples/sentiment/main.py --human --timeout-s 6.0
```

## Verify (optional) {#verify-optional}
```bash
uv run bash scripts/verify.sh
```

## Next steps {#next-steps}
- `Guide`: [Getting started](../getting-started/guide.md)
- `Examples`: [Examples](../examples/index.md)
- `API reference`: [API reference](../reference/api.md)

