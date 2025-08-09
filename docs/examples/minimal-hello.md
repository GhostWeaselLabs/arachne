---
title: Minimal Hello
description: Basic node creation, port configuration, and graph wiring with proper lifecycle management.
tags:
  - examples
  - minimal
  - lifecycle
  - basics
---

# Minimal Hello

A complete, runnable example demonstrating basic node creation and graph wiring with proper lifecycle management. This example shows the fundamental building blocks of the Meridian runtime.

Code location: `meridian-runtime-examples/examples/minimal_hello/`

- Entry point: `meridian-runtime-examples/examples/minimal_hello/main.py`

---

## What it does

### Nodes

- **ProducerNode** — emits a bounded sequence of integers (0-4) on each scheduler tick
- **Consumer** — receives and prints messages, tracking all received values

### Wiring

- `ProducerNode(output)` → `Consumer(in)`: bounded edge with capacity 8

### Lifecycle

- Demonstrates proper node lifecycle management with `on_start` and `on_stop` methods
- Shows bounded message emission with `max_count` parameter
- Includes structured logging with contextual fields

---

## How to run

From the examples repository root (`meridian-runtime-examples`):

```bash
python examples/minimal_hello/main.py
```

You should see:

- Structured startup logs from both nodes
- Message emission logs with sequence numbers
- Consumer receiving and printing messages
- Structured shutdown logs with final counts
- Success confirmation message

!!! tip
    This example is perfect for understanding the basic concepts before moving to more complex examples.

!!! note
    The example uses a deterministic sequence (0-4) to demonstrate predictable behavior.

---

## Implementation notes

- **Node Lifecycle**: Both nodes implement proper `on_start` and `on_stop` methods
- **Structured Logging**: Uses contextual logging with node names and metadata
- **Bounded Emission**: Producer stops after emitting `max_count` messages
- **Message Tracking**: Consumer maintains a list of received values for validation
- **Simple Wiring**: Single edge connection demonstrating basic graph construction

### Key Code Patterns

```python
# Bounded message emission
def _handle_tick(self) -> None:
    if self.count < self.max_count:
        self.emit("output", Message(type=MessageType.DATA, payload=self.count))
        self.count += 1

# Message tracking
def _handle_message(self, port: str, msg: Message) -> None:
    if port == "in":
        self.values.append(msg.payload)
        print(f"Consumer received: {msg.payload}")
```

---

## What to look for

- **Clean Lifecycle**: Proper startup and shutdown sequence
- **Structured Logs**: Contextual logging with node names and metadata
- **Bounded Behavior**: Predictable message count (5 messages total)
- **Simple Topology**: Single producer-consumer pattern
- **Validation**: Final assertion confirms all messages were processed

---

## Source references

- Main entry and graph wiring:
    - `examples/minimal_hello/main.py`

Use this as the foundation for understanding Meridian runtime concepts before exploring more complex examples. 