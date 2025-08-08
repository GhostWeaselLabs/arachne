---
title: API Reference
icon: material/api
---

# API Reference

## Core

- `meridian.core.Message`, `MessageType`
- `meridian.core.Port`, `PortDirection`, `PortSpec`
- `meridian.core.Edge`
- `meridian.core.Node`
- `meridian.core.Scheduler`, `SchedulerConfig`
- `meridian.core.Subgraph`

## Built-in nodes

See [Built-in nodes](built-in-nodes.md) for a categorized overview and examples.

Complete API documentation for Meridian Runtime classes, methods, and configuration options.

!!! note
    **Import Pattern:** All core types are available from the main `meridian.core` module.

Install and import

1. Prereqs: Python 3.11+, `uv`
2. Install dev tools:

    ```bash
    uv lock
    uv sync
    ```
3. Import core primitives:

    ```python
    from meridian.core import (
        Message, MessageType, Node, Subgraph, Scheduler, SchedulerConfig,
        Port, PortDirection, PortSpec, Edge, BackpressureStrategy, RetryPolicy, RoutingPolicy
    )
    ```
4. Observability:

    ```python
    from meridian.observability.config import ObservabilityConfig, configure_observability
    from meridian.observability.config import get_default_config, get_development_config, get_production_config
    from meridian.observability.logging import get_logger, with_context
    ```

## Core types {#core-types}

### Message (`meridian.core.message.Message`) {#message}

- Immutable envelope with:

    - `type`: `MessageType.DATA` · `CONTROL` · `ERROR`
    - `payload`: `Any`
    - `metadata`: optional `Mapping`
    - `headers`: `dict` with `trace_id` and `timestamp` auto-populated if missing

- Helpers:

    - `is_data()`, `is_control()`, `is_error()`
    - `get_trace_id()`, `get_timestamp()`, `with_headers(...)`

- Notes:

    - `CONTROL` and `ERROR` may be routed or prioritized differently than `DATA`.

#### Message fields {#message-fields}

| Field              | Type                                 | Default/Behavior                               |
| ------------------ | ------------------------------------ | ---------------------------------------------- |
| `type`               | `MessageType`                         | Required: `DATA` · `CONTROL` · `ERROR`         |
| `payload`            | `Any`                                  | Required                                       |
| `metadata`           | `Mapping[str, Any]` \| `None`         | Optional                                       |
| `headers`            | `dict[str, Any]`                      | Auto-adds `trace_id` and `timestamp` if missing |
| `get_trace_id()`     | -> `str`                              | Returns `trace_id` or `""`                      |
| `get_timestamp()`    | -> `float`                            | Returns timestamp or `0.0`                      |
| `with_headers(...)`  | -> `Message`                          | Returns a copy with merged headers              |

### Port, PortSpec, PortDirection (`meridian.core.ports`) {#ports-and-portspec}

- `PortDirection`: `INPUT` | `OUTPUT`
- `PortSpec(name, schema: type | tuple[type,...] | None, policy: str | None)`

    - `validate(value)` performs `isinstance` checks when schema is provided

- `Port(name, direction, index: int | None = None, spec: PortSpec | None = None)`

#### Port and PortSpec summary {#portspec-summary}

| Symbol        | Fields                               | Notes                                        |
| ------------- | ------------------------------------ | -------------------------------------------- |
| `PortDirection` | `INPUT`, `OUTPUT`                    | Direction of message flow                    |
| `PortSpec`      | `name: str`                          | Logical id; typically same as port name      |
|               | `schema: type \| tuple[type,...] \| None` | If set, `validate(value)` uses `isinstance` |
|               | `policy: str \| None`                | Hint for router/backpressure layers          |
| `Port`          | `name: str`                          | Unique within node                           |
|               | `direction: PortDirection`           | `INPUT` or `OUTPUT`                          |
|               | `index: int \| None`                 | Optional ordering                            |
|               | `spec: PortSpec \| None`             | Optional type/policy hints                   |

### Node (`meridian.core.node.Node`) {#node}

- Lifecycle hooks:

    - `on_start() -> None` - Called once when scheduler starts the node
    - `on_message(port: str, msg: Message) -> None` - Called by scheduler when message arrives (calls `_handle_message`)
    - `on_tick() -> None` - Called periodically by scheduler (calls `_handle_tick`)
    - `on_stop() -> None` - Called once when scheduler stops the node

- Override methods:

    - `_handle_message(port: str, msg: Message) -> None` - Implement message processing logic
    - `_handle_tick() -> None` - Implement periodic work (timers, maintenance)

- Core methods:

    - `emit(port: str, msg: Message) -> Message` - Publish message on output port (respects backpressure)
    - `port_map() -> dict[str, Port]` - Return mapping of port name to Port for all inputs/outputs

- Factory method:

    - `Node.with_ports(name: str, input_names: Iterable[str], output_names: Iterable[str]) -> Node` - Create node with simple named ports

- Emissions respect runtime backpressure when registered to a `Scheduler`.

### Subgraph (`meridian.core.subgraph.Subgraph`) {#subgraph}

- `Subgraph.from_nodes(name: str, nodes: Iterable[Node]) -> Subgraph` - Create subgraph from node list
- `connect(src: tuple[str, str], dst: tuple[str, str], capacity: int = 1024, policy: object | None = None) -> str` - Connect ports with edge
- `add_node(node: Node, name: str | None = None) -> None` - Add node to subgraph
- `expose_input(name: str, target: tuple[str, str]) -> None` - Expose internal input as subgraph input
- `expose_output(name: str, source: tuple[str, str]) -> None` - Expose internal output as subgraph output
- `validate() -> list[ValidationIssue]` - Return list of `ValidationIssue` for structural problems
- `node_names() -> list[str]` - Return list of contained node names
- `inputs_of(node_name: str) -> dict[str, Edge[object]]` - Return mapping of input port name to incoming Edge

### Edge (`meridian.core.edge.Edge`) {#edge}

- Bounded, in-memory FIFO channel between a source node/port and a target node/port.
- Validates enqueued values against `PortSpec` when present; on mismatch logs `edge.validation_failed` and raises `TypeError`.
- Overflow behavior is controlled by a backpressure `Policy` (see Policies below). If none is provided at enqueue time, the runtime uses the edge's `default_policy` or falls back to `Latest()`.

!!! warning
    **Validation:** Edge validation occurs at enqueue time. Invalid payloads raise `TypeError` and are logged as `edge.validation_failed`.

- Core methods:

    - `try_put(item, policy: Policy | None = None)` - Attempt to enqueue item, returns `PutResult`
    - `try_get()` - Dequeue next item, returns item or `None`
    - `depth()` - Return current queue depth (updates gauge)
    - `is_empty()` - Return `True` if queue is empty
    - `is_full()` - Return `True` if queue at capacity

- Edge ID format: `"src_node:src_port->dst_node:dst_port"`

- Metrics (labeled by a stable `edge_id` in the form `"src_node:src_port->dst_node:dst_port"`):
    - `edge_enqueued_total`
    - `edge_dequeued_total`
    - `edge_dropped_total`
    - `edge_queue_depth` (gauge)
    - `edge_blocked_time_seconds` (histogram)
- Representative log events:
    - `edge.enqueue`, `edge.replace`, `edge.coalesce`, `edge.coalesce_error`, `edge.validation_failed`

See also:
- Policies: #backpressure-and-overflow
- PutResult: #putresult
- Port/PortSpec: #ports-and-portspec

### Scheduler and SchedulerConfig (`meridian.core.scheduler`) {#scheduler}

- `SchedulerConfig`:

    - `tick_interval_ms`: `int` (default `50`)
    - `fairness_ratio`: `tuple[int,int,int] = (4,2,1)`  # (`control`, `high`, `normal`)
    - `max_batch_per_node`: `int` = `8`
    - `idle_sleep_ms`: `int` = `1`
    - `shutdown_timeout_s`: `float` = `2.0`

- `Scheduler(config: SchedulerConfig | None = None)`

    - `register(Node | Subgraph) -> None`
    - `run() -> None`
    - `shutdown() -> None` — graceful termination
    - `is_running() -> bool` — return current running state
    - `get_stats() -> dict[str, int | str]` — return runtime statistics

!!! note
    **Error Handling:** Exceptions within node handlers are logged and re-raised to the scheduler. The processor applies the runtime's policy and continues shutdown on fatal errors.

#### SchedulerConfig defaults {#schedulerconfig-defaults}

| Field              | Type               | Default | Notes                                     |
| ------------------ | ------------------ | ------- | ----------------------------------------- |
| `tick_interval_ms` | `int`              | `50`    | Tick readiness cadence                    |
| `fairness_ratio`   | `tuple[int,int,int]` | `(4,2,1)` | Priority weights (`control`, `high`, `normal`)  |
| `max_batch_per_node` | `int`            | `8`     | Prevents monopolization per slice         |
| `idle_sleep_ms`    | `int`              | `1`     | Sleep while idle to reduce CPU churn      |
| `shutdown_timeout_s` | `float`          | `2.0`   | Graceful shutdown when idle               |

## Backpressure and overflow (`meridian.core.policies`) {#backpressure-and-overflow}

!!! note
    **Policy Implementation:** The runtime uses internal policy implementations. For high-level control, use `BackpressureStrategy` and `RetryPolicy` enums.

### PutResult {#putresult}

- `OK`, `BLOCKED`, `DROPPED`, `REPLACED`, `COALESCED`

### Policy protocol {#policy-protocol}

- `on_enqueue(capacity: int, size: int, item: object)` -> `PutResult`

### BackpressureStrategy {#backpressure-strategy}

!!! note
    **High-level Strategy:** Use `BackpressureStrategy` for runtime-level backpressure control.

| Strategy | Behavior | Use Case |
| -------- | -------- | -------- |
| `DROP` | Prefer dropping items when capacity is reached | Telemetry, low-importance streams |
| `BLOCK` | Prefer blocking/yielding when capacity is reached | Lossless delivery, critical data |

### RetryPolicy {#retry-policy}

!!! note
    **Retry Behavior:** Use `RetryPolicy` for operations that can be retried on failure.

| Policy | Behavior | Use Case |
| ------ | -------- | -------- |
| `NONE` | Do not retry | Critical operations, user-initiated actions |
| `SIMPLE` | Apply simple retry strategy | Network operations, transient failures |

### RoutingPolicy and Routable {#routing}

| Symbol        | Fields / Methods     | Behavior                                       |
| ------------- | -------------------- | ---------------------------------------------- |
| Routable      | route_key() -> str   | Payload supplies routing key                   |
| RoutingPolicy | key: str = "default" | Default key if payload is not Routable         |
|               | select(item) -> str  | Uses item.route_key() if Routable else default |

### ValidationIssue {#validation-issue}

- `ValidationIssue(level: str, code: str, message: str)`
- Used by `Subgraph.validate()` to report structural problems
- Levels: `"error"`, `"warning"`, `"info"`
- Common codes: `"DUP_NODE"`, `"UNKNOWN_NODE"`, `"NO_SRC_PORT"`, `"BAD_CAP"`, `"DUP_EDGE"`

#### Common validation issues {#validation-issues}

| Code | Level | Description | Resolution |
|------|-------|-------------|------------|
| `DUP_NODE` | error | Duplicate node names within subgraph | Ensure unique node names |
| `UNKNOWN_NODE` | error | Edge references non-existent node | Check node names in connection tuples |
| `NO_SRC_PORT` | error | Source node missing output port | Verify port name matches node definition |
| `NO_DST_PORT` | error | Target node missing input port | Verify port name matches node definition |
| `BAD_CAP` | error | Edge capacity ≤ 0 | Set capacity to positive integer |
| `DUP_EDGE` | error | Duplicate edge identifier | Check for duplicate connections |
| `DUP_EXPOSE_IN` | error | Duplicate exposed input names | Ensure unique external input names |
| `DUP_EXPOSE_OUT` | error | Duplicate exposed output names | Ensure unique external output names |
| `BAD_EXPOSE_IN` | error | Exposed input references invalid target | Verify node and port exist |
| `BAD_EXPOSE_OUT` | error | Exposed output references invalid source | Verify node and port exist |

Example: minimal pipeline

```python
from meridian.core import Message, MessageType, Node, Subgraph, Scheduler
from meridian.core.ports import Port, PortDirection, PortSpec

class Producer(Node):
    def __init__(self):
        super().__init__(
            "producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", float))],
        )
        self.count = 0
        self.max_count = 5
        
    def _handle_tick(self):
        if self.count < self.max_count:
            import time
            self.emit("out", Message(type=MessageType.DATA, payload=time.time()))
            self.count += 1

class Consumer(Node):
    def __init__(self):
        super().__init__(
            "consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", float))],
            outputs=[],
        )
        self.values = []
        
    def _handle_message(self, port, msg):
        if port == "in":
            self.values.append(msg.payload)
            print(f"Consumer received: {msg.payload}")

# Create and configure the pipeline
sg = Subgraph.from_nodes("hello", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=16)

# Validate the subgraph structure
issues = sg.validate()
if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  {issue.level}: {issue.message}")
    exit(1)

# Run with proper lifecycle management
scheduler = Scheduler()
scheduler.register(sg)

try:
    print("Starting pipeline...")
    scheduler.run()
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
    scheduler.shutdown()
except Exception as e:
    print(f"Error during execution: {e}")
    scheduler.shutdown()
    raise
```

## Scheduler configuration example {#scheduler-examples}
```python
from meridian.core import Scheduler, SchedulerConfig

cfg = SchedulerConfig(
    tick_interval_ms=25,
    fairness_ratio=(4, 2, 1),
    max_batch_per_node=8,
    idle_sleep_ms=1,
    shutdown_timeout_s=6.0,
)
sched = Scheduler(cfg)
# register graphs...
sched.run()
```

## Observability configuration {#observability}
```python
from meridian.observability.config import ObservabilityConfig, configure_observability
from meridian.observability.config import get_default_config, get_development_config
from meridian.observability.logging import get_logger, with_context

# Use predefined configurations
config = get_development_config()  # or get_default_config(), get_production_config()
configure_observability(config)

# Or configure manually
configure_observability(ObservabilityConfig(
    log_level="INFO",
    log_json=False,
    metrics_enabled=False,
    tracing_enabled=False,
))

logger = get_logger()
with with_context(node="demo"):
    logger.info("demo.start", "Starting pipeline", version="1.0")
```

## See also {#see-also}
- [Patterns](../concepts/patterns.md)
- [Observability](../concepts/observability.md)
- [Getting Started Guide](../getting-started/guide.md)
