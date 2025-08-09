---
title: Streaming Coalesce
description: Demonstrates deterministic coalescing under bursty load using a per-edge coalescing policy.
tags:
  - examples
  - coalesce
  - backpressure
  - streaming
---

# Streaming Coalesce

A focused example that demonstrates the coalescing policy in the Meridian runtime. It simulates a high-rate sensor stream, converts each reading into a small aggregate, and uses a coalescing edge to merge items under burst pressure without losing information.

Code location: `meridian-runtime-examples/examples/streaming_coalesce/`

- Entry point: `examples/streaming_coalesce/main.py`
- Local README: `examples/streaming_coalesce/README.md`

---

## What it does

### Nodes

- **SensorNode** — emits `SensorReading(ts: float, value: float)` at a configurable rate using scheduler ticks (constructor default: 200.0 Hz, CLI default: 300.0 Hz).
- **WindowAggNode** — converts each `SensorReading` into `WindowAgg(count=1, sum=value, min_v=value, max_v=value)` with strict payload validation.
- **SinkNode** — prints per-item aggregates and periodic 1-second summaries, showing stable behavior under load.

### Wiring

- `Sensor(out)` → `WindowAgg(in)`: normal capacity.
- `WindowAgg(out)` → `Sink(in)`: small capacity with a `Coalesce(merge_window)` policy attached to the edge.

### Coalescing

- When the `agg → sink` edge is pressured (small capacity, high rate), queued `WindowAgg` items are merged with a pure, deterministic merge function:
  - `count` and `sum` add
  - `min_v`/`max_v` take min/max
- This compresses bursts and maintains aggregate correctness (no information loss for sum/min/max/count).

---

## How to run

From the examples repository root (`meridian-runtime-examples`):

```bash
python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

You should see:

- Scheduler and node startup logs.
- Frequent per-item aggregate logs (count=1 initially), then coalesced items as load/pressure increases.
- Periodic 1-second summary logs (window size, total_count, avg, min, max).
- Timeout leading to graceful shutdown.

!!! tip
    Add `--help` to see all available flags and their descriptions.

!!! note
    The demo uses a deterministic random seed (1234) for reproducible sensor readings across runs.

---

## CLI flags

These flags are defined by the program (see `examples/streaming_coalesce/main.py` for authoritative defaults):

- `--rate-hz 300.0`         Sensor emit rate (items/sec)
- `--tick-ms 10`            Scheduler tick interval (ms)
- `--max-batch 16`          Max messages per node per scheduling slice
- `--timeout-s 5.0`         Idle timeout for scheduler shutdown (s)
- `--cap-sensor-to-agg 256` Capacity: `sensor → agg`
- `--cap-agg-to-sink 16`    Capacity: `agg → sink` (smaller makes coalescing more visible)
- `--keep 10`               Sink buffer size (items kept for windowed summary)
- `--quiet`                 Reduce per-item logs and focus on periodic summaries
- `--human`                 Human-readable logs (key=value style)
- `--debug`                 Enable debug-level logs

---

## Examples

Emphasize coalescing with higher rate and smaller agg→sink capacity:
```bash
python examples/streaming_coalesce/main.py --human --rate-hz 600 --cap-agg-to-sink 8
```

Quieter output focusing on summaries:
```bash
python examples/streaming_coalesce/main.py --human --quiet
```

### Performance Tuning

**For maximum coalescing visibility**:
```bash
python examples/streaming_coalesce/main.py --human --rate-hz 1000 --cap-agg-to-sink 4
```

**For high-throughput scenarios**:
```bash
python examples/streaming_coalesce/main.py --human --rate-hz 500 --tick-ms 5 --max-batch 32 --cap-sensor-to-agg 512
```

**For memory-constrained environments**:
```bash
python examples/streaming_coalesce/main.py --human --cap-sensor-to-agg 64 --cap-agg-to-sink 8 --rate-hz 100
```

---

## What to look for

- Coalescing under pressure:
    - With a high `--rate-hz` and small `--cap-agg-to-sink`, `WindowAgg` items will be merged, increasing `count` and `sum` while maintaining `min_v` and `max_v`.
- Stability:
    - No unbounded queue growth; the system remains responsive even during bursts.
- Clean lifecycle:
    - Deterministic start, steady loop, and graceful shutdown on timeout.

!!! warning
    **Performance Note**: Running with very high rates (`--rate-hz > 1000`) or very small capacities may cause excessive coalescing and affect aggregate accuracy.

---

## Troubleshooting

### Common Issues

**No coalescing observed**

- Increase `--rate-hz` to generate more pressure
- Decrease `--cap-agg-to-sink` to create backpressure
- Check that the coalescing policy is properly configured

**Excessive coalescing (count > 100)**

- Increase `--cap-agg-to-sink` capacity
- Decrease `--rate-hz` to reduce pressure
- Monitor with `--debug` to see queue depths

**High memory usage**

- Reduce edge capacities (`--cap-sensor-to-agg`, `--cap-agg-to-sink`)
- Lower sensor rate with `--rate-hz`
- Monitor with `--debug` to see queue depths

**Poor performance**

- Increase `--tick-ms` for less frequent scheduling
- Reduce `--max-batch` for more frequent context switches
- Check system load and available CPU resources

---

## Implementation notes

- **Domain model**:

    - `SensorReading` carries a timestamp and value.
    - `WindowAgg` holds `{count, sum, min_v, max_v}` with a computed `avg` property.
    - `merge_window(a, b)` is a pure function used by the `Coalesce` policy to deterministically merge queued items.

- **Graph wiring**:

    - Built via `Subgraph.from_nodes(...)` and `connect(...)` for each edge.
    - The `agg → sink` edge sets `policy=Coalesce(lambda a, b: merge_window(a, b))` with a small capacity.

- **Scheduling**:

    - The `Scheduler` is configured with `tick_interval_ms`, `fairness_ratio=(4, 2, 1)`, `max_batch_per_node`, `idle_sleep_ms=1`, and `shutdown_timeout_s` to demonstrate steady behavior under load.

- **Observability**:

    - Logs use contextual fields; `--human` switches to key=value formatting.

### Architecture Decisions

**Immutable Data Structures**: Uses `@dataclass(frozen=True, slots=True)` for `SensorReading` and `WindowAgg` to ensure thread safety and prevent accidental mutations during coalescing.

**Deterministic Coalescing**: The `merge_window` function is pure and deterministic, ensuring reproducible behavior across runs and preventing data corruption.

**Per-Edge Policy**: Coalescing is configured at the edge level via `policy=Coalesce(...)`, demonstrating the runtime's declarative policy system.

**Strict Validation**: `WindowAggNode` includes strict payload validation to prevent `AttributeError` during processing.

---

## Source references

- Main entry and graph wiring:
    - `examples/streaming_coalesce/main.py`
- Additional background and usage notes:
    - `examples/streaming_coalesce/README.md`

Use these as the single source of truth for flags and behavior when extending or adapting the example.
