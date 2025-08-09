---
title: Hello Graph
description: Modular example with separate producer and consumer modules, demonstrating proper project structure and observability integration.
tags:
  - examples
  - modular
  - observability
  - structure
---

# Hello Graph

A modular example with separate producer and consumer modules, demonstrating proper project structure and observability integration. This example shows how to organize complex nodes into separate files with comprehensive logging.

Code location: `meridian-runtime-examples/examples/hello_graph/`

- Entry point: `examples/hello_graph/main.py`
- Producer: `examples/hello_graph/producer.py`
- Consumer: `examples/hello_graph/consumer.py`

---

## What it does

### Nodes

- **ProducerNode** — emits a bounded sequence of integers with comprehensive logging and metadata
- **Consumer** — receives messages, tracks them in a list, and prints payloads

### Wiring

- `ProducerNode(output)` → `Consumer(in)`: bounded edge with capacity 16

### Modular Design

- Producer and consumer are implemented in separate files
- Comprehensive logging with contextual fields and metadata
- Assertion-based validation to ensure correct behavior
- Demonstrates proper project structure for complex applications

---

## How to run

From the examples repository root (`meridian-runtime-examples`):

```bash
python examples/hello_graph/main.py
```

You should see:

- Structured startup logs with configuration details
- Message emission logs with sequence metadata
- Consumer processing logs
- Structured shutdown logs with final statistics
- Validation assertion confirming correct behavior

!!! tip
    This example demonstrates best practices for organizing complex Meridian applications.

!!! note
    The example includes comprehensive logging and validation to ensure reliable operation.

---

## Implementation notes

- **Modular Structure**: Producer and consumer in separate files for maintainability
- **Comprehensive Logging**: Uses contextual logging with metadata and sequence numbers
- **Message Metadata**: Includes sequence numbers and other metadata in messages
- **Message Tracking**: Consumer maintains a list of received values for validation
- **Lifecycle Management**: Proper startup and shutdown with detailed logging

### Key Code Patterns

```python
# Comprehensive logging with metadata
with with_context(node=self.name):
    self._logger.info(
        "producer.emitted",
        f"Emitted value: {self.current_value}",
        value=self.current_value,
        sequence=self.count_emitted,
    )

# Message with metadata
msg = Message(
    type=MessageType.DATA,
    payload=self.current_value,
    metadata={"sequence": self.count_emitted},
)
```

---

## What to look for

- **Modular Organization**: Clean separation of concerns across files
- **Structured Logging**: Rich contextual information in all log messages
- **Message Metadata**: Sequence numbers and other metadata for tracking
- **Message Tracking**: Consumer tracks received values in a list
- **Professional Structure**: Demonstrates production-ready code organization

---

## Project Structure

```
examples/hello_graph/
├── main.py          # Graph assembly and execution
├── producer.py      # ProducerNode implementation
├── consumer.py      # Consumer implementation
└── __init__.py      # Package initialization
```

This structure demonstrates how to organize complex Meridian applications with proper separation of concerns.

---

## Source references

- Main entry and graph wiring:
    - `examples/hello_graph/main.py`
- Producer implementation:
    - `examples/hello_graph/producer.py`
- Consumer implementation:
    - `examples/hello_graph/consumer.py`

Use this as a template for organizing complex Meridian applications with proper modularity and observability. 