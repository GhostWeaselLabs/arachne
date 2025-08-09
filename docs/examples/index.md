---
title: Examples
description: Browse runnable Meridian Runtime examples with clear goals, commands, and expected behavior.
tags:
  - examples
  - demos
---

# Examples {#examples}

!!! info "Examples moved"
    Examples and notebooks now live in the separate public repository `meridian-runtime-examples`. Clone it to run examples locally: `https://github.com/GhostWeaselLabs/meridian-runtime-examples`.

Welcome to the Meridian Runtime example gallery. Each example is a real, runnable program in the external examples repository, designed to show off core capabilities of the runtime with real dataflow, backpressure, and observability. Copy, run, and adapt.

---

### Minimal Hello World {#minimal-hello-world}

**What it demonstrates:**

- The absolute basics: how to wire up two nodes, send integer messages, and see output.
- Shows the core API: `Node`, `Subgraph`, `Scheduler`, typed ports, and bounded edges.

**Why it matters:**

- If you can run this, your install works. If you can extend it, you understand the core.

**How to run:**
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/minimal_hello/main.py
```

**Detailed documentation:** [Minimal Hello](minimal-hello.md)

---

### Hello Graph {#hello-graph}

**What it demonstrates:**

- Modular design with separate producer and consumer modules.
- Comprehensive logging with contextual fields and metadata.
- Proper project structure for complex applications.

**Why it matters:**

- Shows how to organize complex Meridian applications with proper separation of concerns.
- Demonstrates production-ready code organization and observability integration.

**How to run:**
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/hello_graph/main.py
```

**Detailed documentation:** [Hello Graph](hello-graph.md)

---

### Sentiment Pipeline {#sentiment-pipeline}

**What it demonstrates:**

- Real-time text processing pipeline with control-plane preemption and mixed edge capacities.
- Five nodes: `IngestNode`, `TokenizeNode`, `SentimentNode`, `ControlNode`, `SinkNode`.
- Shows priorities, bounded queues, observability, and graceful shutdown.

**Why it matters:**

- Demonstrates how control messages (like mode changes or flush) can preempt heavy data-plane load.
- Shows how to wire up a non-trivial, multi-node graph with both data and control edges.

**How to run:**
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/sentiment/main.py --human --timeout-s 6.0
```

**Detailed documentation:** [Sentiment Pipeline](sentiment.md)

---

### Streaming Coalesce {#streaming-coalesce}

**What it demonstrates:**

- Deterministic coalescing under bursty load using a per-edge coalescing policy.
- Three nodes: `SensorNode`, `WindowAggNode`, `SinkNode`.
- Shows how to merge queued items on a pressured edge without losing information.

**Why it matters:**

- Illustrates how to handle high-rate streams and compress bursts without unbounded queues.
- Shows how to use the `Coalesce` policy for lossless aggregation.

**How to run:**

```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

**Detailed documentation:** [Streaming Coalesce](streaming-coalesce.md)

---

### Pipeline Demo {#pipeline-demo}

**What it demonstrates:**

- Basic pipeline wiring with validation, transformation, and control signals.
- Simple graph topology with multiple nodes and different edge capacities.
- Backpressure simulation and control plane shutdown signals.

**Why it matters:**

- Shows how to wire up a basic pipeline with validation and transformation stages.
- Demonstrates control plane signals and backpressure handling.

**How to run:**
```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/pipeline_demo/main.py
```

**Detailed documentation:** [Pipeline Demo](pipeline-demo.md)

---

## How to run examples {#how-to-run-examples}

From the examples repository root (`meridian-runtime-examples`), use Python directly or `uv run`:

```bash
# Minimal Hello World (start here!)
python examples/minimal_hello/main.py

# Hello Graph
python examples/hello_graph/main.py

# Sentiment pipeline
python examples/sentiment/main.py --human --timeout-s 6.0

# Streaming coalesce
python examples/streaming_coalesce/main.py --human --timeout-s 5.0

# Pipeline Demo
python examples/pipeline_demo/main.py
```

!!! tip "Example Help"
    Append `--help` to any example to see supported flags.

---

## Contributing new examples {#contributing-new-examples}

- Contribute in `meridian-runtime-examples` under `examples/<example_name>/`
- Keep a small `README.md` in the example directory with:

    - What it demonstrates
    - How to run
    - Key flags and expected behavior
- Add a new page under `docs/examples/` and link it here

This keeps each example self-contained, testable, and easy to extend over time.
