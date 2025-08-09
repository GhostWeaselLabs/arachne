---
title: Examples
description: Runnable examples that demonstrate backpressure, priorities, and observability with clean composition.
tags:
  - examples
  - demos
  - dataflow
  - patterns
---

# Examples

Build real-time, observable dataflows using small, single-responsibility nodes connected by typed, bounded edges. These examples are copy-pasteable and focus on predictable behavior under load.

> Tip  
> Initialize your environment once with:
> 
> ```bash
> uv sync
> ```

---

## Hello Graph (minimal)

A tiny, commented example that wires two nodes with a typed, bounded edge and runs the scheduler.

```python
# Minimal "Hello Graph" with two nodes connected by a typed, bounded edge.

from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection

# Producer: emits an integer payload on each scheduler tick.
class ProducerNode(Node):
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

# Consumer: prints messages from input port "in".
class Consumer(Node):
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

# Wire a small graph and run the scheduler.
sg = Subgraph.from_nodes("hello_world", [ProducerNode(max_count=5), Consumer()])
sg.connect(("producer", "output"), ("consumer", "in"), capacity=8)

sch = Scheduler()
sch.register(sg)
sch.run()
```

Run:

1. Save as hello.py
2. Execute:

```bash
uv run python hello.py
```

!!! note
    This example demonstrates basic node creation, port configuration, and graph wiring. The `ProducerNode` emits a bounded sequence (0-4) and the `Consumer` tracks received values.

!!! tip
    For more comprehensive examples with lifecycle management, observability, and advanced patterns, see the detailed documentation in the `examples/` folder.

## Sentiment pipeline

Demonstrates control-plane priorities, mixed overflow policies, and graceful shutdown with human-friendly output.

Key capabilities:

- CONTROL messages (e.g., FLUSH, QUIET/VERBOSE) preempt standard traffic
- Mixed overflow policies per edge (Latest/Drop) under pressure
- Priority fairness and deterministic shutdown
- Structured logging for lifecycle and flow

Run:
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
uv run python examples/sentiment/main.py --human --timeout-s 6.0
```

Look for:

- CONTROL messages surfacing ahead of regular messages
- Bounded edges enforcing policies under load
- Clean lifecycle: on_start → on_tick → on_stop

!!! note
    See [detailed documentation](../examples/sentiment.md) for comprehensive CLI flags, troubleshooting, and implementation details.



## Streaming coalesce

A high-rate stream that uses coalescing to merge updates deterministically under load—ideal for burst smoothing without losing the latest state.

Key capabilities:

- Coalesce overflow policy (merge many updates into one representative value)
- Deterministic merging under pressure
- Per-edge defaults via Subgraph/Edge configuration

Run:
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

Observe:

- Aggregation behavior as the rate increases
- Stable latency characteristics under bursty input
- Predictable, reproducible merging semantics

!!! note
    See [detailed documentation](../examples/streaming-coalesce.md) for comprehensive CLI flags, troubleshooting, and implementation details.

---

## Available Examples

The examples are organized in the external `meridian-runtime-examples` repository under the `examples/` folder with detailed documentation:

- **[Minimal Hello](../examples/minimal-hello.md)** - Basic node lifecycle and wiring
- **[Hello Graph](../examples/hello-graph.md)** - Modular design with observability
- **[Sentiment Pipeline](../examples/sentiment.md)** - Control-plane priorities and mixed policies
- **[Streaming Coalesce](../examples/streaming-coalesce.md)** - Deterministic coalescing under load
- **[Pipeline Demo](../examples/pipeline-demo.md)** - Multi-stage processing with validation

Each example includes:

- Complete source code with comments
- Local README with usage instructions
- Integration tests for validation
- Observability configuration examples

---

## Patterns illustrated

- **Single-responsibility nodes**: explicit inputs/outputs and small, testable logic
- **Bounded edges with policies**: Block, Drop, Latest, Coalesce
- **Control-plane priorities**: urgent actions (flush, reconfigure, shutdown) preempt normal traffic
- **Subgraphs as units**: reusable graphs with typed ingress/egress and per-edge defaults
- **Observability as a primitive**: structured logs, metrics, and trace hooks
- **Node lifecycle management**: `on_start`, `on_tick`, `on_stop` methods for proper resource management
- **Modular design**: separate files for complex nodes and reusable components

---

## Troubleshooting

!!! warning
    **Common Issues**:
    - **Seems idle or quiet?** Add `--human` or `--debug` where available
    - **Capacity issues?** Increase edge capacity or consumer throughput; adjust policies
    - **Non-determinism?** Use stable seeds and avoid shared mutable state

!!! tip
    **Debugging Tips**:
    - Use `--debug` flag for verbose logging
    - Check scheduler configuration for fairness and timing
    - Verify edge capacities match your expected throughput
    - Monitor for backpressure indicators in logs

---

## Related docs

- Getting started: ../getting-started/guide.md
- Quickstart: ../getting-started/quickstart.md
- Patterns: ../concepts/patterns.md
- Observability: ../concepts/observability.md
- API reference: ../reference/api.md
- Troubleshooting: ../support/TROUBLESHOOTING.md

---

## Contribute an example

We welcome practical, self-contained examples that showcase:

- Clear node responsibilities and typed edges
- Realistic policies and scheduling decisions
- Robust lifecycle and logging
- Minimal dependencies and easy reproducibility

Before submitting:

- Verify with scripts/verify.sh
- Include a short README and run instructions
- Follow existing style and observability patterns
