---
title: Pipeline Demo
description: Multi-stage data processing with validation, transformation, and control flow demonstrating complex graph topology.
tags:
  - examples
  - pipeline
  - validation
  - multi-stage
---

# Pipeline Demo

A comprehensive example demonstrating multi-stage data processing with validation, transformation, and control flow. This example shows how to build complex graph topologies with multiple processing stages and error handling.

Code location: `examples/pipeline_demo/`

- Entry point: `examples/pipeline_demo/main.py`
- Control: `examples/pipeline_demo/control.py`
- Transformer: `examples/pipeline_demo/transformer.py`
- Validator: `examples/pipeline_demo/validator.py`
- Sink: `examples/pipeline_demo/sink.py`

---

## What it does

### Nodes

- **KillSwitch** — publishes a shutdown signal on control-plane edge
- **Validator** — drops invalid inputs, emits valid items only (requires "id" field)
- **Transformer** — normalizes payloads and forwards with "normalized" flag
- **SlowSink** — simulates I/O latency to trigger backpressure

### Wiring

- `Validator(out)` → `Transformer(in)`: data plane with capacity 64
- `Transformer(out)` → `Sink(in)`: data plane with capacity 8
- `KillSwitch(out)` → `Sink(control)`: control plane with capacity 1

### Multi-Stage Processing

- Demonstrates validation and transformation pipeline
- Shows control plane shutdown signal
- Includes backpressure simulation with slow sink
- Validates graph wiring and basic functionality

---

## How to run

From the repository root:

```bash
python examples/pipeline_demo/main.py
```

You should see:

- Graph wiring and node startup
- Basic pipeline execution
- Shutdown signal processing
- Backpressure simulation

!!! tip
    This example demonstrates basic pipeline wiring and control plane signals.

!!! note
    The example validates graph construction and basic functionality without external inputs.

---

## Implementation notes

- **Validation Logic**: Validator only forwards messages with "id" field in payload
- **Transformation**: Transformer adds "normalized" flag to all payloads
- **Backpressure Simulation**: SlowSink introduces artificial delay to demonstrate backpressure
- **Control Signal**: KillSwitch sends shutdown signal on first tick
- **Graph Wiring**: Demonstrates basic graph construction and node connections

### Key Code Patterns

```python
# Validation logic
def _handle_message(self, port: str, msg: Message[Any]) -> None:
    if port != "in":
        return
    self.seen += 1
    payload = msg.payload
    if isinstance(payload, dict) and "id" in payload:
        self.valid += 1
        self.emit("out", Message(type=MessageType.DATA, payload=payload))

# Transformation
def _handle_message(self, port: str, msg: Message[dict[str, Any]]) -> None:
    if port != "in":
        return
    payload = dict(msg.payload)
    payload.setdefault("normalized", True)
    self.emit("out", Message(type=MessageType.DATA, payload=payload))
```

---

## What to look for

- **Basic Wiring**: Simple graph construction with multiple nodes
- **Control Signal**: KillSwitch sends shutdown signal on first tick
- **Validation**: Validator filters messages based on payload structure
- **Transformation**: Transformer adds metadata to payloads
- **Backpressure**: SlowSink demonstrates backpressure with artificial delay

---

## Project Structure

```
examples/pipeline_demo/
├── main.py          # Pipeline assembly and execution
├── control.py       # KillSwitch implementation
├── transformer.py   # Transformer implementation
├── validator.py     # Validator implementation
├── sink.py          # SlowSink implementation
└── __init__.py      # Package initialization
```

This structure demonstrates basic pipeline organization with separate node implementations.

---

## Source references

- Main entry and pipeline assembly:
    - `examples/pipeline_demo/main.py`
- KillSwitch implementation:
    - `examples/pipeline_demo/control.py`
- Transformer implementation:
    - `examples/pipeline_demo/transformer.py`
- Validator implementation:
    - `examples/pipeline_demo/validator.py`
- SlowSink implementation:
    - `examples/pipeline_demo/sink.py`

Use this as a template for basic pipeline wiring and control plane signal handling. 