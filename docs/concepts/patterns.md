---
title: Patterns
description: Common graph patterns and architectural approaches for building robust dataflows with Meridian Runtime, including backpressure policies, control-plane messaging, observability, and error handling.
tags:
  - patterns
  - architecture
  - best-practices
  - examples
  - backpressure
  - observability
---

# Patterns

This page shows common graph patterns with minimal examples grounded in the actual runtime APIs.

!!! info "See Also"
    Check the [API Reference](../reference/api.md) for detailed API documentation and semantics.

## Tutorial: Basic Patterns

### Message Creation and Headers

Messages automatically populate `trace_id` and `timestamp` headers if not provided:

```python
from meridian.core import Message, MessageType

# Headers auto-populated # (1)
msg = Message(MessageType.DATA, payload="hello")
print(msg.get_trace_id())  # Auto-generated UUID
print(msg.get_timestamp()) # Current time

# Custom headers override defaults
msg = Message(
    MessageType.DATA, 
    payload="hello",
    headers={"trace_id": "custom-123", "timestamp": 1234567890.0}
)
```

- See [Message.__post_init__()](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/message.py#L58) for auto-population logic

## How-to: Backpressure and Overflow

Meridian provides bounded edges with configurable policies. The policy protocol and results are defined in `meridian.core.policies` (Block, Drop, Latest, Coalesce; see `PutResult`).

- Block (default): apply backpressure upstream (producer blocks/yields when full)
- Drop: discard new messages when full
- Latest: keep only the newest item when full (replace older)
- Coalesce: merge queued items under pressure via a deterministic function

### Block (default backpressure)

```python
from meridian.core import Subgraph, Scheduler, Node, Message, MessageType, PortSpec
from meridian.core.ports import Port, PortDirection
from meridian.core.policies import block # (1)

class Producer(Node):
    def __init__(self):
        super().__init__(
            "producer",
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
    def _handle_tick(self):
        self.emit("out", Message(type=MessageType.DATA, payload=1))

class Consumer(Node):
    def __init__(self):
        super().__init__(
            "consumer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
    def _handle_message(self, port, msg):
        print("got", msg.payload)

sg = Subgraph.from_nodes("p_block", [Producer(), Consumer()])
# Default policy is block(); producers cooperatively back off when capacity is reached. # (2)
sg.connect(("producer","out"), ("consumer","in"), capacity=16)
Scheduler().register(sg)
Scheduler().run()
```

- Factory function from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L175)
- Block policy implementation in [Block.on_enqueue()](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L67)

### Drop (lossy, prefer freshness)

```python
from meridian.core import Subgraph, Scheduler
from meridian.core.policies import drop # (1)
# Producer/Consumer as above...
sg = Subgraph.from_nodes("p_drop", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=drop())
Scheduler().register(sg)
Scheduler().run()
```

- Drop policy factory from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L180)

### Latest (replace older with newest)

```python
from meridian.core import Subgraph, Scheduler
from meridian.core.policies import latest # (1)
# Producer/Consumer as above...
sg = Subgraph.from_nodes("p_latest", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=4, policy=latest())
Scheduler().register(sg)
Scheduler().run()
```

- Latest policy factory from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L185)

### Coalesce (deterministic merge under pressure)

```python
from dataclasses import dataclass
from meridian.core import Subgraph, Scheduler
from meridian.core.policies import coalesce # (1)

@dataclass(frozen=True, slots=True)
class Stat:
    count: int
    total: float
def merge_stats(a: object, b: object) -> object:
    # Deterministic, pure merge; matches coalesce(fn: Callable[[object, object], object]) # (2)
    assert isinstance(a, Stat) and isinstance(b, Stat)
    return Stat(count=a.count + b.count, total=a.total + b.total)

# Producer emits Stat(count=1, total=value); Consumer reads Stat
sg = Subgraph.from_nodes("p_coalesce", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=8, policy=coalesce(merge_stats))
Scheduler().register(sg)
Scheduler().run()
```

- Coalesce policy factory from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L190)
- Coalesce policy implementation in [Coalesce.on_enqueue()](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L108)

!!! info "See Also"
    Backpressure semantics and `PutResult` are in [API: Backpressure and overflow](../reference/api.md#backpressure-and-overflow).

## How-to: Control-plane Priority

Control-plane messages (MessageType.CONTROL) can preempt data-plane work for predictable behavior under load. Use a dedicated `ctl` port and wire separate control edges.

```python
from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection

class Worker(Node):
    def __init__(self):
        super().__init__(
            "worker",
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", int)),
                Port("ctl", PortDirection.INPUT, spec=PortSpec("ctl", str)),
            ],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int))],
        )
        self._mode = "normal"

    def _handle_message(self, port, msg):
        if port == "ctl" and msg.type == MessageType.CONTROL: # (1)
            cmd = str(msg.payload).strip().lower()
            if cmd in {"normal", "quiet"}:
                self._mode = cmd
            return
        if port == "in" and self._mode != "quiet":
            self.emit("out", Message(MessageType.DATA, msg.payload))

class Controller(Node):
    def __init__(self):
        super().__init__("controller", inputs=[], outputs=[Port("ctl", PortDirection.OUTPUT, spec=PortSpec("ctl", str))])
    def _handle_tick(self):
        self.emit("ctl", Message(MessageType.CONTROL, "quiet"))

sg = Subgraph.from_nodes("ctl_demo", [Worker(), Controller()])
# Control edge: small capacity; scheduler treats CONTROL with higher priority. # (2)
sg.connect(("controller","ctl"), ("worker","ctl"), capacity=4)
# Add data edges as needed...
Scheduler().register(sg)
Scheduler().run()
```

- MessageType.CONTROL defined in [message.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/message.py#L15)
- Priority handling in [SchedulerConfig.fairness_ratio](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/scheduler.py#L35)

## How-to: Error Handling

Handle errors gracefully with proper message types and structured logging:

```python
from meridian.core import Message, MessageType
from meridian.observability.logging import get_logger, with_context

class SafeNode(Node):
    def _handle_message(self, port, msg):
        logger = get_logger()
        try:
            # Process message
            result = self._process(msg.payload)
            self.emit("out", Message(MessageType.DATA, result))
        except ValueError as e:
            # Emit structured error message # (1)
            error_info = {"error": str(e), "port": port, "payload_type": type(msg.payload).__name__}
            self.emit("error", Message(MessageType.ERROR, payload=error_info)) # (2)
            with with_context(node=self.name, port=port): # (3)
                logger.error("node.error", f"Validation error: {e}", error=str(e))
        except Exception as e:
            # Log and continue for unexpected errors
            with with_context(node=self.name, port=port):
                logger.error("node.fatal", f"Unexpected error: {e}", error=str(e))
            # Optionally emit error message
            self.emit("error", Message(MessageType.ERROR, payload={"error": str(e)}))
```

- Error message structure from [MessageType.ERROR](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/message.py#L25)
- ERROR message type for structured error reporting
- Contextual logging from [logging.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/observability/logging.py#L180)

## Reference: Scheduler Configuration and Lifecycle

The cooperative scheduler is tuned via `SchedulerConfig`. Nodes participate using lifecycle hooks (`on_start`, `on_message`, `on_tick`, `on_stop`).

```python
from meridian.core import Scheduler, SchedulerConfig

class LifecycleNode(Node):
    def on_start(self): # (1)
        """Called when node starts processing."""
        print(f"Node {self.name} starting")
    
    def on_stop(self): # (2)
        """Called when node stops processing."""
        print(f"Node {self.name} stopping")
    
    def _handle_message(self, port, msg): # (3)
        """Called for each incoming message."""
        print(f"Processing message on {port}")
    
    def _handle_tick(self): # (4)
        """Called periodically for time-based processing."""
        print(f"Tick for {self.name}")

cfg = SchedulerConfig(
    tick_interval_ms=25,        # tick readiness interval # (5)
    fairness_ratio=(4, 2, 1),   # (control, high, normal) priority weights # (6)
    max_batch_per_node=8,       # work quota per scheduling slice # (7)
    idle_sleep_ms=1,
    shutdown_timeout_s=6.0,     # graceful stop when idle
)
sched = Scheduler(cfg)
# Register subgraphs, then:
sched.run()
```

- Lifecycle hooks defined in [Node](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/node.py)
- Node lifecycle management in [Scheduler](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/scheduler.py#L147)
- Message handling in scheduler main loop
- Tick handling with interval from SchedulerConfig
5. SchedulerConfig definition in [scheduler.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/scheduler.py#L20)
6. Priority weights for different message types
7. Batch size limits for fairness

## Reference: Observability Patterns

Configure logging/metrics/tracing once; use contextual logging within nodes.

```python
from meridian.observability.config import ObservabilityConfig, configure_observability # (1)
from meridian.observability.logging import get_logger, with_context

# Configure all observability subsystems
configure_observability(ObservabilityConfig(
    log_level="INFO",
    log_json=False,           # human-readable
    metrics_enabled=True,     # Enable metrics collection
    metrics_namespace="myapp",
    tracing_enabled=True,     # Enable tracing
    tracing_provider="inmemory",
    tracing_sample_rate=-0,
))

logger = get_logger()
with with_context(node="demo", edge_id="main_pipeline"): # (2)
    logger.info("demo.start", "Starting pipeline", version="-0")
```

- ObservabilityConfig from [config.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/observability/config.py#L8)
- Context management from [logging.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/observability/logging.py#L180)

### Metrics and Tracing

```python
from meridian.observability.metrics import get_metrics, time_block # (1)
from meridian.observability.tracing import start_span # (2)

class InstrumentedNode(Node):
    def _handle_message(self, port, msg):
        metrics = get_metrics()
        
        # Time the processing
        with time_block("node_processing_duration"): # (3)
            with start_span("process_message", {"port": port, "type": msg.type.value}): # (4)
                result = self._process(msg.payload)
                metrics.counter("messages_processed_total").inc() # (5)
                self.emit("out", Message(MessageType.DATA, result))
```

- Metrics utilities from [metrics.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/observability/metrics.py)
- Tracing utilities from [tracing.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/observability/tracing.py)
- Timing instrumentation for performance monitoring
- Span creation for distributed tracing
5. Counter increment for metrics collection

## Reference: Subgraph Composition and Reuse

- Expose clear input/output ports and validate wiring.
- Compose smaller subgraphs and expose a clean surface.

```python
from meridian.core import Subgraph, Node, PortSpec, Message, MessageType
from meridian.core.ports import Port, PortDirection

class Upper(Node):
    def __init__(self):
        super().__init__(
            "upper",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", str))],
        )
    def _handle_message(self, port, msg):
        self.emit("out", Message(type=MessageType.DATA, payload=str(msg.payload).upper()))

class Printer(Node):
    def __init__(self):
        super().__init__(
            "printer",
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[],
        )
    def _handle_message(self, port, msg):
        print(msg.payload)

sg = Subgraph.from_nodes("upper_print", [Upper(), Printer()]) # (1)
sg.connect(("upper","out"), ("printer","in"), capacity=8)
```

- Subgraph composition from [subgraph.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/subgraph.py)

## Reference: Routing

Partition or direct items using a routing key. If a payload implements `Routable`, the runtime uses its `route_key()`. Otherwise, `RoutingPolicy.key` is used.

```python
from dataclasses import dataclass
from meridian.core.policies import Routable, RoutingPolicy # (1)

@dataclass(frozen=True, slots=True)
class Event(Routable): # (2)
   user_id: str
   value: int
   def route_key(self) -> str:
       # Route by user for per-user ordering/partitioning
       return self.user_id

policy = RoutingPolicy(key="default") # (3)
# In runtime paths that select a route, the policy will use Event.route_key() if available,
# else fall back to the provided default key.
rk1 = policy.select(Event(user_id="u123", value=7))  # "u123" # (4)
rk2 = policy.select({"value": 7})                    # "default"
```

- Routing types from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L150)
- Routable protocol definition
- RoutingPolicy implementation
- Policy selection logic in [RoutingPolicy.select()](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L175)

## Reference: Additional Policy Types

### RetryPolicy and BackpressureStrategy

```python
from meridian.core.policies import RetryPolicy, BackpressureStrategy # (1)

# Retry behavior for operations
retry_policy = RetryPolicy.SIMPLE  # or RetryPolicy.NONE # (2)

# High-level backpressure strategy
strategy = BackpressureStrategy.BLOCK  # or BackpressureStrategy.DROP # (3)
```

- Additional policy types from [policies.py](https://github.com/GhostWeaselLabs/meridian-runtime/blob/main/src/meridian/core/policies.py#L120)
- RetryPolicy enum values
- BackpressureStrategy enum values

## Explanation: Pattern Selection Guidelines

### When to Use Each Backpressure Policy

- **Block**: Use for lossless data where producers can wait (e.g., database writes, file processing)
- **Drop**: Use for telemetry, monitoring, or low-importance streams where freshness matters more than completeness
- **Latest**: Use for UI state, configuration updates, or single-slot consumers that only need the newest value
- **Coalesce**: Use for batchable workloads where combining items reduces pressure (e.g., aggregations, summaries)

### Control vs Data Messages

- **CONTROL**: Use for lifecycle events, configuration changes, or coordination signals
- **DATA**: Use for normal application payloads
- **ERROR**: Use for structured error reporting that should be handled by error consumers

### Performance Considerations

- Keep node processing time bounded to maintain fairness
- Use appropriate edge capacities based on producer/consumer rates
- Enable metrics and tracing in development to identify bottlenecks
- Consider `max_batch_per_node` tuning for latency-sensitive workloads 