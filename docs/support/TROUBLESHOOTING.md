# Troubleshooting (Privacy‑First)

## Summary
This page helps you diagnose and fix common issues when building and running Meridian Runtime, with minimal, privacy‑respecting steps. It also cross‑links to the API Reference where appropriate and includes corroborated metrics/log event names emitted by the runtime.

If a problem isn't covered here, open an issue with full context (OS, Python, commands, logs) or start a discussion.

---

## Quick checklist

1. Verify environment

    - Python 3.11+ is installed and active in your virtualenv.
    - Dependencies installed via `uv sync` (or `pip install -e ".[dev]"`).

2. Reproduce with a minimal example

    - Simplify the graph: few nodes, clear edge capacities/policies.
    - Replace real data with dummy values; remove payload contents.

3. Collect redacted artifacts

    - Structured logs: redact values; keep keys, counts, and policy names.
    - Config snippets: include only relevant keys; mask secrets.
    - Metrics snapshots: numeric values; avoid PII in labels.

4. Compare observed vs expected

    - Write down what actually happens vs what you expect.

5. Sanity checks

    - Lint/type/tests pass:

        - `make lint`
        - `uv run pytest -q`

    - Docs build:

        - `make docs-build`
        - `uv run mkdocs build`

---

## Common issues and fixes

### Environment and imports

**Symptoms**

- `ModuleNotFoundError` for project modules or extras.
- Examples crash or can't import modules.

**Fix**

- Ensure your env is active:

    - `source .venv/bin/activate` (or platform equivalent)

- Re-install dependencies:

    - `uv sync`

- Verify Python version:

    - `python --version` (must be 3.11+)

- Run examples using module form to ensure proper PYTHONPATH:

    - `git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git && cd meridian-runtime-examples && uv run python examples/hello_graph/main.py`

**See also**

- [Concepts overview](../concepts/about.md)

---

### Edge overflow or backpressure surprises

#### What the runtime does

- Edges are capacity‑bounded FIFO queues with policy‑controlled overflow (see [API: Edge](../reference/api.md#edge)).
- If you don't provide a policy on enqueue, the runtime applies internal policy implementations or the edge's configured `default_policy`.
- Runtime behavior and outcomes (see [API: PutResult](../reference/api.md#putresult)):
    - `Block` → `PutResult.BLOCKED`: producer should yield/wait when full.
    - `Drop` → `PutResult.DROPPED`: item is discarded when full.
    - `Latest` → `PutResult.REPLACED`: keep only the most recent item when full.
    - `Coalesce(fn)` → `PutResult.COALESCED`: merge old/new via fn when full.

#### Metrics 

(emitted per edge_id: `"src_node:src_port->dst_node:dst_port"`)

- `edge_enqueued_total`
- `edge_dequeued_total`
- `edge_dropped_total`
- `edge_queue_depth` (gauge)
- `edge_blocked_time_seconds` (histogram)

#### Representative log events

- `edge.enqueue`
- `edge.replace`
- `edge.coalesce`
- `edge.coalesce_error`
- `edge.validation_failed`
- `edge.drop`
- `edge.blocked`
- `edge.dequeue`

**Symptoms**

- Messages stall or appear to drop.
- Queue depth near capacity; lower throughput than expected.

**Likely causes**

- Capacity too small for bursty workloads.
- Policy mismatch for the workload (`Drop` vs `Block` vs `Latest` vs `Coalesce`).
- Upstream/downstream rate mismatch or blocking operations.

**What to try**

1. Inspect and adjust edge configuration

    - Increase capacity for bursty edges.
    - Use `Block` for strict delivery (be aware of backpressure).
    - Use `Latest` for freshness when only the newest matters.
    - Use `Coalesce(fn)` to merge bursts into fewer items.

2. Balance node workloads

    - Move blocking I/O to async or dedicated executors; batch where appropriate.

3. Add metrics/logs

    - Track enqueued/dequeued/dropped, blocked time, and depth per edge.

4. Validate fairness

    - Ensure scheduler policies aren't starving a node.

**What to collect (redacted)**

- Edge definitions with capacity and policy names.
- Logs:

    - `event="edge.enqueue" edge_id="A:out->B:in"`
    - `event="edge.replace" edge_id="A:out->B:in"`
    - `event="edge.coalesce" edge_id="A:out->B:in"`
    - `event="edge.drop" edge_id="A:out->B:in"`

- Metrics snapshot: `edge_queue_depth`, `edge_dropped_total`, `edge_blocked_time_seconds`.

**See also**

- [API Reference: Edge](../reference/api.md#edge)
- [API Reference: Backpressure and Overflow](../reference/api.md#backpressure-and-overflow)
- [API Reference: PutResult](../reference/api.md#putresult)

---

### Scheduler starvation or unfairness

**Symptoms**

- Certain nodes rarely run or lag behind others.
- Control‑plane tasks take too long to apply.

**Likely causes**

- Long‑running tasks monopolize execution.
- Blocking operations in async contexts causing stalls.
- High contention on shared resources.

**What to try**

1. Audit node work

    - Break long tasks into smaller units.
    - Use asyncio‑friendly APIs; offload blocking calls.

2. Control‑plane prioritization

    - Ensure control operations have clear priority.

3. Tune fairness strategy

    - Try round‑robin vs weighted fairness; adjust weights if supported.

**What to collect (redacted)**

- Summary of node durations (ranges).
- Structured logs around scheduling decisions (no payloads).
- Minimal graph snapshot: node names, edge topology.
- Scheduler metrics: `scheduler_runnable_nodes`, `scheduler_loop_latency_seconds`.

**See also**

- [API Reference: Scheduler](../reference/api.md#scheduler)
- [Concepts: Observability](../concepts/observability.md)

---

### Shutdown hangs or unclean teardown

**Symptoms**

- Runtime fails to exit promptly.
- Nodes' `on_stop` hooks not called or appear stuck.
- In‑flight work not draining.

**Likely causes**

- Blocking in shutdown paths.
- Pending tasks waiting on unbounded/stuck conditions.
- Missing timeouts or cancellation guards.

**What to try**

1. Add timeouts to `on_stop` and drain operations

2. Make `on_stop` idempotent

    - Avoid enqueuing new work on shutdown.

3. Emit lifecycle logs

    - Provide start/end markers for shutdown sequences.

4. Use per‑edge policies

    - Drain or drop remaining work explicitly.

5. Implement proper shutdown handling:

    ```python
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        scheduler.shutdown()
    except Exception as e:
        print(f"Error during execution: {e}")
        scheduler.shutdown()
        raise
    ```

**What to collect (redacted)**

- Logs:

    - `event="scheduler.shutdown_start"`
    - `event="scheduler.shutdown_requested"`
    - `event="scheduler.shutdown_complete"`
    - `event="node.start"`
    - `event="node.stop"`

- Note tasks still pending after timeout.

**See also**

- [API Reference: Node](../reference/api.md#node)
- [API Reference: Scheduler](../reference/api.md#scheduler)

---

### Validation errors or unexpected payload handling

**What the runtime does**

- If an edge has a `PortSpec`, values (or `Message.payload`) are validated during enqueue. Mismatch logs `edge.validation_failed` and raises `TypeError`.

**Symptoms**

- Frequent validation failures.
- Error events too sparse or too verbose.

**Likely causes**

- Mismatched schema vs runtime data shape.
- Validation at the wrong boundary.
- Error policy not configured as intended.

**What to try**

1. Validate at boundaries

    - Use `PortSpec` at ingress/egress and, when applicable, schema validators in your producer/consumer code.

2. Tighten/loosen schema choices

    - Optional vs required fields as systems evolve.

3. Confirm privacy posture

    - No payloads in error logs; attach only metadata.

4. Use subgraph validation before execution:

    ```python
    issues = subgraph.validate()
    if issues:
        print("Validation issues found:")
        for issue in issues:
            print(f"  {issue.level}: {issue.message}")
        exit(1)
    ```

**What to collect (redacted)**

- Schema shape (names and types only; no values).
- Error logs without payload contents:

    - `event="edge.validation_failed" edge_id="A:out->B:in"`

- Validation issues from `Subgraph.validate()`.

**See also**

- [API Reference: Ports and PortSpec](../reference/api.md#ports-and-portspec)
- [API Reference: Message](../reference/api.md#message)
- [API Reference: ValidationIssue](../reference/api.md#validation-issue)

---

### Logging/tracing too verbose or too sparse

**Symptoms**

- High log volume impacting performance.
- Not enough information to diagnose issues.

**What to try**

1. Right‑size log levels

    - `INFO` for lifecycle, `WARN`/`ERROR` for anomalies, `DEBUG` sparingly.

2. Adopt key conventions

    - `event`, `node_id`, `edge_id`, `policy`, `counts`, `durations`.

3. Sampling

    - Apply sampling for repetitive debug events.

**What to collect (redacted)**

- A short sequence (last 200–500 lines) with structured entries.
- Note which events are missing for diagnosis.

**See also**

- [Concepts: Observability](../concepts/observability.md)

---

### Performance regressions

**Symptoms**

- Increased latency or reduced throughput vs a previous run.
- Hot CPU or I/O saturation.

**Likely causes**

- New blocking paths introduced.
- Higher cardinality in metric labels or verbose logging.
- Insufficient edge capacity or missing coalescing for bursty flows.

**What to try**

1. Revert to known‑good settings

    - Compare metrics before/after a change.

2. Profile hot paths (locally)

    - Identify blocking calls; offload or batch.

3. Reduce label cardinality

    - Keep metrics labels low and stable.

**What to collect (redacted)**

- Before/after metrics: `throughput`, `queue_depth`, `dropped counts`, `latency percentiles` (if available).
- Configuration diffs: policy names, capacities.
- Scheduler metrics: `scheduler_loop_latency_seconds`, `scheduler_runnable_nodes`.

**See also**

- [API Reference: Backpressure and Overflow](../reference/api.md#backpressure-and-overflow)
- [Concepts: Patterns](../concepts/patterns.md)

---

## Debugging

- Enable debug logs in your observability configuration.
- Use metrics to inspect edge depths and drops.
- Use module execution for tests/examples to avoid path issues:

    - `uv run pytest`
    - `git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git && cd meridian-runtime-examples && uv run python examples/pipeline_demo/main.py`

**Key metrics to monitor:**

- **Edge metrics:** `edge_queue_depth`, `edge_dropped_total`, `edge_blocked_time_seconds`
- **Scheduler metrics:** `scheduler_runnable_nodes`, `scheduler_loop_latency_seconds`, `scheduler_priority_applied_total`
- **Node metrics:** `node_messages_total`, `node_errors_total`, `node_tick_duration_seconds`

**See also**

- [Concepts: Observability](../concepts/observability.md)
- [API Reference](../reference/api.md)

---

## Minimal reproduction strategy

1. Start small

    - One or two nodes, one edge, a single message type.

2. Replace data

    - Use shape‑equivalent dummy values; avoid real payloads.

3. Fix the seed

    - Avoid non‑determinism in tests unless necessary.

4. Log only essentials

    - Lifecycle transitions, scheduling decisions, edge `enqueues`/`replaces`/`coalesce`, error summaries.
    
**Conceptual example (sanitized)**

- Configure an edge with `capacity=10` and `policy="Drop"`.
- Send 100 synthetic messages; confirm `dropped counts` rise.
- Observe metrics and expected behavior.

---

## Safe artifacts for triage

- Environment

    - OS, Python, Meridian versions; tooling versions.

- Graph topology snapshot

    - Node/edge names, capacities, policies; no payload schemas required.

- Logs (redacted)

    - Keep keys; redact values: `<REDACTED>`.

- Metrics

    - Numeric `counters`/`gauges`/`histograms`; avoid PII in labels.

- Config differences

    - Show changed keys and `enum`/`boolean` values; mask secrets or replace with `CHECKSUM(...)` or `PLACEHOLDER`.

**Never include**

- Secrets, tokens, credentials.
- PII or business data payloads.
- Proprietary identifiers without anonymization.

---

## Diagnostics to include when asking for help

- OS and Python version.
- Exact command(s) you ran.
- Minimal snippet or steps to reproduce.
- Full error output and any relevant logs (redacted).
- Any local changes or configuration differences.

---

## Known pitfalls

- Mixing package managers

    - Prefer `uv` for this repo to avoid environment drift; don't interleave `pip` unless necessary.

- Stale caches

    - Clear `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, and any build artifacts if behavior seems inconsistent.

- Renamed documentation

    - After file moves/renames, update internal links and nav in `mkdocs.yml`. In strict mode, broken links abort the build.

---

## **See also**

- [How to report issues](./HOW-TO-REPORT-ISSUES.md)
- [Contributing guide](../contributing/guide.md)
- [API Reference](../reference/api.md)
- [Concepts overview](../concepts/about.md)
