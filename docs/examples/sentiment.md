---
title: Sentiment Pipeline
description: Control-plane preemption, mixed capacities, and graceful shutdown in an end-to-end text processing graph.
tags:
  - examples
  - sentiment
  - control-plane
  - backpressure
---

# Sentiment Pipeline

A small, end-to-end example that simulates a real-time text processing pipeline with a control-plane channel. It demonstrates priorities, bounded queues, observability, and graceful shutdown in the Meridian runtime.

Code location: `examples/sentiment/`

- Entry point: `examples/sentiment/main.py`
- Local README: `examples/sentiment/README.md`

---

## What it does

### Nodes:

- **IngestNode** — emits short text samples at a configurable rate (default: 10.0 Hz).
- **TokenizeNode** — splits text into tokens (lowercased, punctuation stripped).
- **SentimentNode** — computes a naive sentiment score; responds to CONTROL messages to change mode:
  - `avg` (default): continuous score in [-1.0, 1.0]
  - `binary`: discrete score in {-1.0, 0.0, 1.0} (rounds continuous score to nearest discrete value)
- **ControlNode** — periodically emits CONTROL commands in rotation to demonstrate preemption and live configuration:
  - `avg`, `binary`, `flush`, `quiet`, `verbose` (cycles through all commands)
- **SinkNode** — prints per-item results and periodic summaries; supports `flush`, `quiet`, `verbose` via CONTROL.

### Wiring:

- Data plane: `Ingest(text) → Tokenize(in) → Sentiment(in) → Sink(in)`
- Control plane: `Control(ctl) → Sentiment(ctl)` and `Control(ctl) → Sink(ctl)`

### Priorities and policies:

- CONTROL messages are prioritized by the scheduler and pierce data-plane load.
- Edges are bounded with configurable capacities (see flags below).

---

## How to run

From the repository root:

```bash
python examples/sentiment/main.py --human --timeout-s 6.0
```

You should see:

- Scheduler and node startup logs.
- Per-item logs from `SinkNode` with scores (when not in quiet mode).
- CONTROL effects every few seconds (toggle avg/binary, flush, quiet/verbose).
- Scheduler timeout leading to graceful shutdown.

!!! tip
    Add `--help` to see all available flags and their descriptions.

!!! note
    The demo uses a deterministic random seed (42) for reproducible text samples across runs.

---

## CLI flags

The program defines the following arguments (exact names and defaults come from the code in `examples/sentiment/main.py`):

- `--rate-hz 10.0`      Ingest rate (items per second)
- `--control-period 4.0` CONTROL message period (sec)
- `--keep 10`            Sink buffer size for summaries
- `--quiet`              Sink prints periodic summaries only (still logs flush)
- `--tick-ms 25`         Scheduler tick interval (ms)
- `--max-batch 8`        Max messages per node per scheduling slice
- `--timeout-s 6.0`      Idle timeout for scheduler shutdown (seconds)
- `--cap-text 64`        Capacity: ingest → tokenize
- `--cap-tokens 64`      Capacity: tokenize → sentiment
- `--cap-scored 128`     Capacity: sentiment → sink
- `--cap-control 8`      Capacity: control → sentiment/sink
- `--human`              Human-readable logs (key=value style)
- `--debug`              Enable debug-level logs

---

## Examples

Higher rate and smaller capacities (induces more backpressure):
```bash
python examples/sentiment/main.py --human --rate-hz 20 --cap-text 32 --cap-tokens 32 --cap-scored 64
```

Emphasize control-plane preemption (faster ticks, more frequent control):
```bash
python examples/sentiment/main.py --human --tick-ms 10 --control-period 2.0
```

Quiet output (focus on periodic summaries):
```bash
python examples/sentiment/main.py --human --quiet
```

### Performance Tuning

**For high-throughput scenarios**:
```bash
python examples/sentiment/main.py --rate-hz 50 --tick-ms 10 --max-batch 16 --cap-text 256 --cap-tokens 256 --cap-scored 512
```

**For low-latency control response**:
```bash
python examples/sentiment/main.py --tick-ms 5 --control-period 1.0 --cap-control 16
```

**For memory-constrained environments**:
```bash
python examples/sentiment/main.py --cap-text 16 --cap-tokens 16 --cap-scored 32 --cap-control 4
```

---

## What to look for

- Control-plane preemption:
    - Mode changes (`avg`/`binary`), `flush`, and verbosity toggles apply promptly even while many data messages flow.
- Bounded queues:
    - No unbounded memory growth; throughput remains stable under configured capacities.
- Observability:
    - Logs carry contextual fields (e.g., node name); `--human` switches to key=value formatting.
- Clean shutdown:
    - The scheduler announces timeout and stops nodes in order.

!!! warning
    **Performance Note**: Running with very high rates (`--rate-hz > 50`) or very small capacities may cause backpressure and affect control message responsiveness.

---

## Troubleshooting

### Common Issues

**No output appears**
- Check that the scheduler is running (look for startup logs)
- Verify `--timeout-s` is not too short for your system
- Try adding `--debug` for more verbose logging

**Control messages not taking effect**
- Ensure `--control-period` is reasonable (default 4.0s)
- Check that `--cap-control` is not too small (default 8)
- Verify scheduler fairness ratio allows control priority

**High memory usage**
- Reduce edge capacities (`--cap-text`, `--cap-tokens`, `--cap-scored`)
- Lower ingest rate with `--rate-hz`
- Monitor with `--debug` to see queue depths

**Poor performance**
- Increase `--tick-ms` for less frequent scheduling
- Reduce `--max-batch` for more frequent context switches
- Check system load and available CPU resources

---

## Implementation notes

- The graph is assembled with `Subgraph.from_nodes(...)` and `connect(...)` for each edge.
- **CONTROL vs DATA**:
    - `SentimentNode` listens to `ctl` and `in` ports; CONTROL on `ctl` changes state without interfering with data processing on `in`.
    - `SinkNode` supports `flush`, `quiet`, and `verbose` via its `ctl` port.
- **Scheduling**:
    - The `Scheduler` is configured with `tick_interval_ms`, `fairness_ratio=(4, 2, 1)`, `max_batch_per_node`, `idle_sleep_ms=1`, and `shutdown_timeout_s` to demonstrate stability under load.
- **Edge Policies**:
    - Data plane edges use bounded capacities with `Latest` policy (default) for freshness
    - Control edges use `Block` policy to ensure CONTROL messages are prioritized by the scheduler
    - The demo demonstrates how "freshness" and blocking behavior interplay with prioritized CONTROL messages.

### Architecture Decisions

**Separate Control Plane**: The example uses dedicated control channels (`ctl` ports) to demonstrate how control messages can be prioritized independently of data flow.

**Bounded Queues**: All edges use finite capacities to prevent unbounded memory growth and demonstrate backpressure handling.

**Deterministic Sampling**: Uses a fixed random seed (42) to ensure reproducible behavior across runs for testing and debugging.

**Thread-Safe Ingest**: The `IngestNode` uses a separate producer thread to simulate real-world streaming scenarios where data arrives asynchronously.

---

## Source references

- Main entry and graph wiring:
    - `examples/sentiment/main.py`
- Additional background and usage notes:
    - `examples/sentiment/README.md`

Use these as the single source of truth for flags and behavior when extending or adapting the example.
