---
title: Built-in nodes
icon: material/puzzle
status: new
---

# Built-in node classes

Meridian ships a comprehensive library of built-in nodes under the `meridian.nodes` module. These nodes cover common patterns and are designed to compose with custom nodes seamlessly.

## Quick imports

```python
from meridian.nodes import (
  # Base & testing
  FunctionNode, NodeConfig, ErrorPolicy, NodeTestHarness,
  # Basics
  DataProducer, DataConsumer, MapTransformer, FilterTransformer, FlatMapTransformer,
  # Controllers
  Router, Merger, Splitter,
  # Events
  EventAggregator, EventCorrelator, TriggerNode,
  # Workers
  WorkerPool, AsyncWorker,
  # Storage
  CacheNode, BufferNode, FileWriterNode, FileReaderNode,
  # Network
  HttpClientNode, HttpServerNode, WebSocketNode, MessageQueueNode,
  # Monitoring
  MetricsCollectorNode, HealthCheckNode, AlertingNode, SamplingNode,
  # Data processing
  ValidationNode, SerializationNode, CompressionNode, EncryptionNode,
  # Flow control
  ThrottleNode, CircuitBreakerNode, RetryNode, TimeoutNode,
  # State management
  StateMachineNode, SessionNode, CounterNode, WindowNode,
)
```

!!! tip "Zero-to-node"
    Use `NodeTestHarness` from `meridian.nodes` to exercise node behavior without wiring a full graph or scheduler.

## Categories

=== "Basics"

    - `DataProducer`: tick-driven message generation from an iterator.
    - `DataConsumer`: handler-based sink for DATA messages.
    - `MapTransformer`, `FilterTransformer`, `FlatMapTransformer`.

=== "Controllers"

    - `Router`: route by function to named output ports.
    - `Merger`: N→1 fan-in across multiple inputs.
    - `Splitter`: broadcast or filter per-output.

=== "Events"

    - `EventAggregator`: keyed/windowed aggregation.
    - `EventCorrelator`: group by key until completion/timeout.
    - `TriggerNode`: emit on external condition.

=== "Workers"

    - `WorkerPool`: distribute sync work (RR/hash).
    - `AsyncWorker`: async function execution with ordering.

=== "Storage"

    - `CacheNode`: TTL + LRU/FIFO.
    - `BufferNode`: batch and flush by interval/CONTROL.
    - `FileWriterNode`, `FileReaderNode`.

=== "Network"

    - `HttpClientNode`: simple HTTP client (urllib).
    - `HttpServerNode`, `WebSocketNode` (simulated), `MessageQueueNode` (in-memory).

=== "Monitoring"

    - `MetricsCollectorNode`, `HealthCheckNode`, `AlertingNode`, `SamplingNode`.

=== "Data processing"

    - `ValidationNode` (callable / JSON Schema if installed), `SerializationNode` (JSON),
      `CompressionNode` (gzip), `EncryptionNode` (AES‑GCM/ChaCha20‑Poly1305).

=== "Flow control"

    - `ThrottleNode` (token bucket), `CircuitBreakerNode`, `RetryNode`, `TimeoutNode`.

=== "State management"

    - `StateMachineNode`, `SessionNode`, `CounterNode`, `WindowNode`.

## Examples

=== "Producer → Map → Consumer"

```python
from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import DataProducer, MapTransformer, DataConsumer

p = DataProducer("p", data_source=lambda: iter(range(5)), interval_ms=0)
m = MapTransformer("m", transform_fn=lambda x: x * 2)
seen = []
c = DataConsumer("c", handler=seen.append)

g = Subgraph.from_nodes("g", [p, m, c])
g.connect(("p", "output"), ("m", "input"))
g.connect(("m", "output"), ("c", "input"))

s = Scheduler(SchedulerConfig())
s.register(g)
# run in background thread for a short period
import threading, time
th = threading.Thread(target=s.run, daemon=True)
th.start(); time.sleep(0.1); s.shutdown(); th.join()
```

## EncryptionNode (secure by default)

!!! info "Hard dependency"
    `EncryptionNode` uses `cryptography` (AES‑GCM/ChaCha20‑Poly1305). Ensure it is installed (bundled by default).

```python
from meridian.nodes import EncryptionNode, EncryptionAlgorithm, EncryptionMode
key = b"0" * 32
enc = EncryptionNode("enc", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM)
dec = EncryptionNode("dec", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM, mode=EncryptionMode.DECRYPT)
```
