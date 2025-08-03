# Sentiment Pipeline Demo

A small, end-to-end example that simulates a real-time text processing pipeline with a control-plane channel. It demonstrates priorities, backpressure, observability, and graceful shutdown in the Meridian runtime.

## What it does

Nodes:
- IngestNode: emits short text samples at a configurable rate.
- TokenizeNode: splits text into tokens (lowercased, punctuation stripped).
- SentimentNode: computes a naive sentiment score; responds to CONTROL messages to change mode.
  - `avg` (default): continuous score in [-1.0, 1.0].
  - `binary`: discrete score {-1.0, 0.0, 1.0}.
- ControlNode: periodically emits CONTROL commands to demonstrate preemption and live configuration.
  - `avg`, `binary`, `flush`, `quiet`, `verbose`.
- SinkNode: prints per-item results and periodic summaries; supports `flush`, `quiet`, `verbose` via CONTROL.

Edges and policies:
- Ingest(text) → Tokenize(in) → Sentiment(in) → Sink(in): data-plane edges with bounded capacities.
- Control(ctl) → Sentiment(ctl) and Control(ctl) → Sink(ctl): control-plane edges with small capacity.
- The scheduler prioritizes CONTROL messages, so control effects apply even under heavy data load.

## What it shows

- Priority preemption: CONTROL messages pierce data-plane load (bounded latency).
- Backpressure and capacities: bounded queues for text, tokens, scored output, and control.
- Deterministic lifecycle: start order, stable loop, graceful shutdown on timeout.
- Observability: structured logs (JSON by default, human-readable with `--human`).
- Developer ergonomics: simple Node + Subgraph wiring; per-node logging context.

## Quick start

From repository root:

```
python examples/sentiment/main.py --human --timeout-s 6.0
```

You should see:
- Scheduler and node startup logs.
- Per-item logs from `SinkNode` with scores (when not in quiet mode).
- CONTROL effects every few seconds (toggle avg/binary, flush, quiet/verbose).
- Scheduler timeout → graceful shutdown.

## Tuning knobs

CLI flags:
- `--rate-hz 8.0`        Ingest rate (items per second).
- `--control-period 4.0` CONTROL command cadence (seconds).
- `--keep 10`            Sink buffer size for summaries.
- `--quiet`              Sink prints periodic summaries only (still logs flush).
- `--tick-ms 25`         Scheduler tick interval (ms).
- `--max-batch 8`        Max messages per node per scheduling slice.
- `--timeout-s 6.0`      Idle timeout for scheduler shutdown (seconds).
- `--cap-text 64`        Capacity: ingest → tokenize.
- `--cap-tokens 64`      Capacity: tokenize → sentiment.
- `--cap-scored 128`     Capacity: sentiment → sink.
- `--cap-control 8`      Capacity: control → sentiment/sink.
- `--human`              Human-readable logs (key=value style).
- `--debug`              Enable debug-level logs.

Examples:
```
# Higher rate and smaller capacities (more backpressure)
python examples/sentiment/main.py --human --rate-hz 20 --cap-text 32 --cap-tokens 32 --cap-scored 64

# Emphasize control-plane preemption (lower tick interval, more frequent control)
python examples/sentiment/main.py --human --tick-ms 10 --control-period 2.0
```

## What to look for

- CONTROL preemption: mode changes (`avg`/`binary`), `flush`, and verbosity apply promptly even while many data messages flow.
- Bounded queues: no unbounded memory growth; throughput remains stable under configured capacities.
- Clean shutdown: scheduler announces timeout and stops nodes in order.

## Notes

- This demo uses the runtime’s default per-edge policies and relies on the scheduler to prioritize CONTROL messages.
- Logs include contextual fields (e.g., node, port, optional trace IDs) and can be switched between JSON and human-readable formats.
- For more performance-oriented behavior and budgets, run the stress/perf tests in `tests/stress` or integrate metrics/tracing as desired.