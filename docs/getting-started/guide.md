---
title: Getting started
description: Set up Meridian Runtime, run your first example, and learn the core workflow.
tags:
  - getting-started
  - setup
  - installation
  - quickstart
---

# Getting started

Welcome to **Meridian Runtime** — a minimal, reusable graph runtime for Python. This guide gets you from zero to a running example and points you to next steps.

If you're familiar with dataflow systems (nodes/edges/graphs), you'll feel at home. Meridian emphasizes predictability under load, first‑class observability, and clean composition.

!!! tip "In a hurry?"
    Use the condensed [Quickstart](quickstart.md).

## Prerequisites {#prerequisites}

### Required {#required}
- Python 3.11+ (tested with 3.11, 3.12, 3.13)
- uv (recommended) — fast Python package manager (see [Install uv](https://docs.astral.sh/uv/))
- Git

### Recommended {#recommended}
- make (handy shortcuts)
- gh (GitHub CLI) if contributing
- macOS/Linux (Windows via WSL works)

### Version Compatibility {#version-compatibility}

| Component | Minimum Version | Recommended Version |
|-----------|----------------|-------------------|
| Python    | 3.11           | 3.12+             |
| uv        | 0.1.0          | Latest            |
| pip       | 21.0           | Latest            |

!!! note "Version Note"
    Meridian Runtime is actively developed. For the best experience, use the latest stable versions of dependencies.

---

## Install and setup {#install-and-setup}

1) Clone repository
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime.git
cd meridian-runtime
```

2) Create environment and install
```bash
# Create lockfile (if missing) and install deps into .venv
uv lock
uv sync
```

3) Verify install
```bash
uv run python -c "import meridian; print('✓ Meridian installed successfully')"
```

!!! tip "Environment Commands"
    Run commands inside the environment with: `uv run <command>`

---

## Verify the runtime {#verify-runtime}

Run a combined verification (tests + coverage thresholds):

```bash
uv run bash scripts/verify.sh
```

This:

- Runs smoke/integration/stress tests
- Enforces coverage gates (core ≥ 90%, overall ≥ 80%)
- Exits with a clear PASS/FAIL

!!! success "Verification Complete"
    If it passes, your environment is healthy and ready.

---

## Development loop {#development-loop}

Typical cycle: lint → type-check → test → run examples.

```bash
# Lint
uv run ruff check .

# Type-check
uv run mypy src

# Tests with coverage gate
uv run pytest --cov=src --cov-fail-under=80
```

!!! tip "Make Targets"
    Use these shortcuts if available:

    ```bash
    make demo-sentiment
    make demo-coalesce
    ```

---

## Run examples {#run-examples}

Examples are now documented on dedicated pages:

- **Sentiment pipeline** — priorities, control-plane preemption, mixed overflow policies  
  Run: `python examples/sentiment/main.py --human --timeout-s 6.0`

- **Streaming coalesce** — deterministic coalescing under pressure  
  Run: `python examples/streaming_coalesce/main.py --human --timeout-s 5.0`

!!! tip "Example Help"
    Add `--help` to any example command to see available flags.

---

## Core concepts {#core-concepts}

### Primitives {#primitives}

- **Node**: single-responsibility processing unit that consumes and emits messages (hooks: on_start, on_tick, on_stop)
- **Edge**: bounded, typed queue between nodes with a configurable overflow policy
- **Subgraph**: reusable composition of nodes and edges with typed ingress/egress
- **Scheduler**: fairness- and priority-aware orchestration
- **Observability**: structured logs, metrics, and optional trace hooks

### Overflow policies {#overflow-policies}

- **Block**: producers wait when the queue is full (default)
- **Drop**: new messages are dropped under pressure (explicit load shedding)
- **Latest**: keep only the most recent payloads when full
- **Coalesce**: deterministically merge incoming messages (for example, keep-latest-state)

### Control-plane priority {#control-plane-priority}

- Urgent control messages (shutdown, flush, reconfigure) can preempt data traffic to remain responsive under load

---

## Hello Graph {#hello-graph}

A minimal example showing two nodes wired by a typed, bounded edge. Comments explain each step.

```python
# Minimal "Hello Graph" with two nodes connected by a typed, bounded edge.

from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection

# Producer: emits an integer payload on every scheduler tick.
class Producer(Node):
    def __init__(self):
        super().__init__(
            "producer",
            inputs=[],
            outputs=[Port("output", PortDirection.OUTPUT, spec=PortSpec("output", int))],
        )
        self.count = 0
        
    def _handle_tick(self) -> None:
        if self.count < 5:  # Emit 5 messages then stop
            self.emit("output", Message(type=MessageType.DATA, payload=self.count))
            self.count += 1

# Consumer: prints the payload from the input port.
class Consumer(Node):
    def __init__(self):
        super().__init__(
            "consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
        self.values = []
        
    def _handle_message(self, port: str, msg: Message) -> None:
        if port == "in":
            self.values.append(msg.payload)
            print(f"Received: {msg.payload}")

# Wire a small graph with a bounded, typed edge and run the scheduler.
sg = Subgraph.from_nodes("hello", [Producer(), Consumer()])
sg.connect(("producer", "output"), ("consumer", "in"), capacity=8)

sch = Scheduler()
sch.register(sg)
sch.run()

print(f"Consumer received {len(Consumer().values)} messages")
```

Run:

- Save the code above to a file, e.g., hello.py
- Execute it in your environment:

  ```bash
  uv run python hello.py
  ```

Expected output:
```
Received: 0
Received: 1
Received: 2
Received: 3
Received: 4
Consumer received 0 messages
```

---

## Test Your Setup {#test-your-setup}

Verify your installation works correctly with this simple test:

```python
# test_setup.py
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

# Create and run a simple test
sg = Subgraph.from_nodes("test", [TestNode()])
sg.connect(("test", "out"), ("test", "in"), capacity=1)  # Self-loop for testing

sch = Scheduler()
sch.register(sg)

# Send initial message
test_node = sg.nodes[0]
test_node.emit("in", Message(type=MessageType.DATA, payload="Hello Meridian!"))

sch.run()
```

Run this test:
```bash
uv run python test_setup.py
```

Expected output:
```
✓ Setup working! Received: Hello Meridian!
```

!!! success "Setup Verified"
    If you see this output, your Meridian Runtime installation is working correctly!

---

## Example index {#example-index}

### Minimal Hello World {#minimal-hello-world}

- Basic concepts: nodes, edges, and simple dataflow  
  Run: `python examples/minimal_hello/main.py`

### Sentiment {#sentiment}

- Control-plane preemption, mixed overflow policies, graceful shutdown  
  Run: `python examples/sentiment/main.py --human --timeout-s 6.0`

### Streaming coalesce {#streaming-coalesce}

- Coalescing policy, deterministic merging under pressure  
  Run: `python examples/streaming_coalesce/main.py --human --timeout-s 5.0`

### Future examples {#future-examples}

- Backpressure E2E — block/drop/latest/coalesce comparison
- Observability cookbook — logs, metrics, traces

---

## Project layout {#project-layout}

```text
src/meridian/
  core/           # nodes, edges, subgraphs, scheduler, policies
  observability/  # logging/metrics/tracing hooks
examples/
  sentiment/
  streaming_coalesce/
tests/
  unit/
  integration/
  soak/
scripts/
  verify.sh       # one-shot verification gate (tests + coverage)
```

---

## Troubleshooting {#troubleshooting}

### Import Errors {#import-errors}

If you see errors like `ModuleNotFoundError: No module named 'meridian-runtime'`:

- **Cause**: Examples were using outdated imports
- **Fix**: All examples now use `meridian` imports. Update any old code to use:
  ```python
  from meridian.core import Node, Message, MessageType, Subgraph, Scheduler
  from meridian.core.ports import Port, PortDirection, PortSpec
  ```

### Installation Issues {#installation-issues}

If `uv sync` fails:

- **Check Python version**: Ensure you have Python 3.11+
  ```bash
  python --version
  ```
- **Update uv**: `pip install -U uv`
- **Clear cache**: `uv cache clean`

### Verification Failures {#verification-failures}

If `uv run bash scripts/verify.sh` fails:

- **Tests flaky or slow**: Ensure nothing else is consuming heavy CPU
  ```bash
  uv run pytest -q
  ```
- **Coverage below threshold**: Run subsets to identify gaps
  ```bash
  uv run pytest tests/unit -q
  ```
- **Example hangs**: Lower timeout using `--timeout-s <seconds>`

### Runtime Errors {#runtime-errors}

Common issues and solutions:

- **Port connection errors**: Ensure port names match exactly between nodes
  ```python
  # Correct: port names must match exactly
  sg.connect(("producer", "output"), ("consumer", "in"), capacity=8)
  ```
- **Type errors**: Verify PortSpec types match your payload types
  ```python
  # Correct: PortSpec type matches payload type
  Port("data", PortDirection.OUTPUT, spec=PortSpec("data", str))
  self.emit("data", Message(type=MessageType.DATA, payload="hello"))
  ```
- **Scheduler not running**: Call `sch.run()` after registering subgraphs
  ```python
  sch = Scheduler()
  sch.register(sg)
  sch.run()  # Don't forget this!
  ```
- **Messages not flowing**: Check edge capacities and overflow policies
  ```python
  # Small capacity can cause backpressure
  sg.connect(("fast", "out"), ("slow", "in"), capacity=1)
  ```
- **Node lifecycle issues**: Ensure proper initialization
  ```python
  # Correct: pass inputs and outputs to super().__init__
  super().__init__(
      name="my_node",
      inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
      outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
  )
  ```

### Debugging Tips {#debugging-tips}

!!! tip "Debugging Strategies"
    - Use `--human` flag with examples to see detailed output
    - Enable debug logging: `--debug` flag in examples
    - Check observability output for flow insights
    - Use smaller edge capacities to trigger backpressure scenarios

---

## Performance Characteristics {#performance-characteristics}

### Throughput & Latency {#throughput-latency}
- **Message throughput**: 100K+ messages/second on modern hardware
- **Latency**: Sub-millisecond for simple message passing
- **Memory overhead**: ~100 bytes per message + node overhead
- **CPU usage**: Proportional to message rate and processing complexity

### Scalability Limits {#scalability-limits}
- **Node count**: Hundreds of nodes per scheduler (limited by memory)
- **Edge capacity**: Configurable from 1 to millions of messages
- **Concurrent graphs**: Multiple schedulers can run independently
- **Backpressure**: Automatic flow control prevents memory exhaustion

### Resource Usage {#resource-usage}
- **Memory**: ~1MB base + ~100 bytes per message in flight
- **CPU**: Single-threaded scheduler (use multiple schedulers for parallelism)
- **Network**: No built-in networking (add your own transport layer)

---

## Contributing {#contributing}

We welcome issues, PRs, and discussions.

- Issues: [github.com/GhostWeaselLabs/meridian-runtime/issues](https://github.com/GhostWeaselLabs/meridian-runtime/issues)
- Discussions: [github.com/GhostWeaselLabs/meridian-runtime/discussions](https://github.com/GhostWeaselLabs/meridian-runtime/discussions)

### Before submitting: {#before-submitting}

!!! tip "Quality Checklist"

    ```bash title="Run the verification gate"
    uv run bash scripts/verify.sh
    ```
    
    ```bash title="Ensure lint checks pass"
    uv run ruff check .
    ```
    
    ```bash title="Ensure type checks pass"
    uv run mypy src
    ```

    ```bash title="Ensure tests pass"
    uv run pytest -q
    ```
Follow existing patterns for clarity and observability

Also see:

- [Contributing guide](../contributing/guide.md)
- [Patterns](../concepts/patterns.md)
- [API reference](../reference/api.md)

---

## What's next {#whats-next}

- [Concepts and patterns](../concepts/patterns.md)
- [API reference](../reference/api.md)
- Extend an example (add a control‑plane message or a new edge policy)
- Add observability hooks and inspect logs/metrics under load
