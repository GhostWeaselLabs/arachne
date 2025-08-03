# Streaming Coalesce Demo

A focused example that demonstrates the coalescing policy in the Meridian runtime. It simulates a high-rate sensor stream, converts each reading into a small aggregate, and uses a coalescing edge to merge items under burst pressure without losing information.

## What it does

Nodes:
- SensorNode:
  - Emits `SensorReading(ts: float, value: float)` at a configurable rate using scheduler ticks.
- WindowAggNode:
  - Converts each `SensorReading` into a `WindowAgg(count=1, sum=value, min=value, max=value)`.
- SinkNode:
  - Prints per-item aggregates and periodic 1-second summaries, showing stable behavior under load.

Wiring:
- `Sensor(out)` → `WindowAgg(in)`: normal capacity.
- `WindowAgg(out)` → `Sink(in)`: small capacity with `Coalesce(merge_window)` policy (default_policy on the edge).

Coalescing:
- When the `agg → sink` edge is pressured (small capacity, high rate), queued `WindowAgg` items are merged with a pure, deterministic merge function:
  - `count` and `sum` add
  - `min`/`max` take min/max
- This compresses bursts and maintains aggregate correctness (no information loss for sum/min/max/count).

## Why it’s useful

- Demonstrates bounded queues and stable throughput under bursty load.
- Shows a unique runtime feature: coalescing reduces queue pressure while retaining key aggregate statistics.
- Clean, declarative configuration: the coalescing policy is attached per edge at wiring time (no monkey patching or custom scheduler hooks).

## Quick start

From repository root:

```
python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

You should see:
- Scheduler and node startup logs.
- Frequent per-item aggregate logs (count=1 initially), then coalesced items as load/pressure increases.
- Periodic 1-second summary logs (window size, total_count, avg, min, max).
- Timeout → graceful shutdown.

## Tuning knobs

CLI flags:
- `--rate-hz 300.0`        Sensor emit rate (items per second).
- `--tick-ms 10`           Scheduler tick interval (ms).
- `--max-batch 16`         Max messages per node per scheduling slice.
- `--timeout-s 5.0`        Idle timeout for scheduler shutdown (seconds).
- `--cap-sensor-to-agg 256` Capacity: `sensor → agg`.
- `--cap-agg-to-sink 16`   Capacity: `agg → sink` (smaller makes coalescing more visible).
- `--keep 10`              Sink buffer size (items kept for windowed summary).
- `--quiet`                Reduce per-item logs and focus on periodic summaries.
- `--human`                Human-readable logs (key=value style).
- `--debug`                Enable debug-level logs.

Examples:
```
# Emphasize coalescing with higher rate and smaller agg->sink capacity
python examples/streaming_coalesce/main.py --human --rate-hz 600 --cap-agg-to-sink 8

# Quieter output focusing on summaries
python examples/streaming_coalesce/main.py --human --quiet
```

## What to look for

- Coalescing under pressure:
  - With a high `--rate-hz` and small `--cap-agg-to-sink`, the `WindowAgg` items will be merged, increasing `count` and `sum` while maintaining `min` and `max`.
- Stability:
  - No unbounded queue growth; the system remains responsive even during bursts.
- Clean lifecycle:
  - Deterministic start, steady loop, and graceful shutdown on timeout.

## Implementation notes

- Per-edge policy:
  - The `Coalesce(merge_window)` policy is attached via `Subgraph.connect(..., policy=Coalesce(...))`.
  - `Edge.try_put()` uses the provided policy or falls back to the edge’s `default_policy` (else `Latest()`).
- Message pass-through:
  - If a producer enqueues a `Message`, it is passed through without being rewrapped, preserving payloads and headers end-to-end.
