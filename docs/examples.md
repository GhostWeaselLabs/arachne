# Examples

Build real-time, observable dataflows with small, single‑responsibility nodes connected by typed, bounded edges. This section showcases runnable, production‑style examples that emphasize predictability under load, clean composition, and first‑class observability.

Use these examples to learn common patterns and to bootstrap your own graphs.

---

## How to Run

All commands are run from the repository root. Use uv to ensure a clean, reproducible environment.

Initialize the environment:
```text
uv lock
uv sync
```

Run an example:
```text
uv run python examples/<example_name>/main.py --help
```

Convenience targets:
```text
make demo-sentiment
make demo-coalesce
```

---

## Examples Catalog

### 1) Sentiment Pipeline
A small, realistic pipeline that demonstrates control‑plane priorities, mixed overflow policies, and graceful shutdown. It includes human‑friendly rendering of the pipeline state so you can see how priority preemption and flow control actually behave.

Key capabilities:
- Control‑plane messages (e.g., FLUSH, QUIET/VERBOSE) that preempt standard traffic
- Mixed overflow policies per edge (e.g., Latest/Drop) under pressure
- Priority fairness and deterministic shutdown
- Built‑in observability and structured logging

Run:
```text
uv run python examples/sentiment/main.py --human --timeout-s 6.0
```

Source:
- examples/sentiment/main.py
- examples/sentiment/README.md

What to look for:
- CONTROL messages surfacing ahead of regular messages
- Bounded edges enforcing backpressure with different policies
- Clean lifecycle: on_start, on_tick, on_stop order and logs

---

### 2) Streaming Coalesce
A high‑rate sensor stream that uses coalescing to merge updates deterministically under load. This is a canonical example for burst smoothing and reducing downstream load without losing the latest signal.

Key capabilities:
- Coalesce overflow policy (merge many updates into a single representative value)
- Deterministic merging under pressure
- Per‑edge default policy configuration via Subgraph and Edge

Run:
```text
uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

Source:
- examples/streaming_coalesce/main.py
- examples/streaming_coalesce/README.md

What to look for:
- Aggregation behavior as rate increases
- Stable latency characteristics under bursty input
- Predictable, reproducible merging semantics

---

## Patterns Illustrated

These examples showcase several core Meridian patterns and best practices:

- Single‑Responsibility Nodes
  Small, focused processing units with explicit inputs/outputs and lifecycle hooks.

- Bounded Edges with Policies
  Edges enforce backpressure and apply policies explicitly: Block, Drop, Latest, Coalesce.

- Control‑Plane Priorities
  Urgent messages (e.g., flush, reconfigure, shutdown) preempt normal traffic for predictable behavior.

- Subgraphs as First‑Class Units
  Compose reusable graphs; expose typed ingress/egress and configure per‑edge defaults declaratively.

- Observability as a Primitive
  Structured logs, metrics, and trace hooks are built in to aid debugging, performance tuning, and ops.

---

## Tips for Extending the Examples

- Add a new control‑plane command
  Try introducing a throttle or a reset signal and ensure it routes with CONTROL priority.

- Experiment with Edge Policies
  Swap policies (Latest vs Drop vs Coalesce) to see how they affect throughput and latency.

- Parameterize Throughput
  Adjust rate, tick interval, and batch sizes to observe behavior at different scales.

- Add Instrumentation
  Emit counters/timers and inspect performance under different workloads.

- Compose Subgraphs
  Wrap the producer/processor/sink into a Subgraph and reuse it inside a larger topology.

---

## Troubleshooting

- Example seems idle or too quiet
  Use --human or --debug flags if available to increase visibility.

- Running out of capacity
  Tune per‑edge caps and policies; increase consumer throughput or batching.

- Non‑deterministic output
  Ensure consistent seeds and stable scheduling where appropriate; check for accidental shared mutable state.

---

## Related Documentation

- Getting Started: ./getting-started.md
- Quickstart: ./quickstart.md
- Patterns: ./patterns.md
- Observability: ./observability.md
- API Reference: ./api.md
- Troubleshooting: ./troubleshooting.md

---

## Contributing New Examples

We welcome practical, self‑contained examples that demonstrate:
- Clear node responsibilities and typed edges
- Realistic policies and scheduling decisions
- Robust lifecycle and logging
- Minimal dependencies and easy reproducibility

Before submitting:
- Verify locally with scripts/verify.sh
- Include a short README and run instructions
- Follow existing style and observability patterns

Happy weaving.