---
title: Migration and extension guide
icon: material/transition
status: new
---

# Migration and extension guide

This guide shows how to:

- Migrate existing custom `Node` subclasses to built-in node classes under `meridian.nodes`
- Decide when to use built-ins vs writing custom nodes
- Extend and compose built-in nodes for specialized behaviors

!!! tip
    Built-ins favor composition over inheritance. Prefer wiring multiple simple nodes over subclassing a large custom node.

## When to use built-ins vs custom

- Use built-ins when your logic matches a common pattern:
  - Producer/consumer, map/filter/flatmap
  - Routing, splitting, merging
  - Event windowing/correlation, triggers
  - Async/concurrent workers
  - Storage/file IO, HTTP/websocket, simple queues
  - Metrics/alerting/sampling
  - Validation/serialization/compression/encryption
  - Flow-control (throttle, circuit breaker, retry, timeout)
- Write a custom node when you need:
  - A new port/flow pattern not covered above
  - A domain adapter with external APIs and custom lifecycles
  - Highly specialized performance optimizations (after measuring)

## Migration cookbook

=== "Map/Filter"

    Original custom node:

    ```python
    from meridian.core import Node, Message, MessageType

    class Double(Node):
        def __init__(self):
            super().__init__("double", inputs=[], outputs=[])
        def _handle_message(self, port: str, msg: Message) -> None:
            if msg.type == MessageType.DATA:
                self.emit("out", Message(MessageType.DATA, msg.payload * 2))
    ```

    Migrate to built-in:

    ```python
    from meridian.nodes import MapTransformer
    double = MapTransformer("double", transform_fn=lambda x: x * 2)
    ```

=== "Producer"

    ```python
    from meridian.nodes import DataProducer

    source = lambda: iter(range(100))
    producer = DataProducer("p", data_source=source, interval_ms=0)
    ```

=== "Consumer"

    ```python
    from meridian.nodes import DataConsumer

    results: list[int] = []
    sink = DataConsumer("c", handler=results.append)
    ```

=== "Event windows"

    ```python
    from meridian.nodes import EventAggregator

    agg = EventAggregator("agg", window_ms=1000, aggregation_fn=lambda xs: sum(xs))
    ```

=== "Async work"

    ```python
    from meridian.nodes import AsyncWorker

    async def fn(x: int) -> int: ...
    aw = AsyncWorker("aw", async_fn=fn, max_concurrent=8)
    ```

=== "Encryption"

    ```python
    from meridian.nodes import EncryptionNode, EncryptionAlgorithm, EncryptionMode

    key = b"0" * 32
    enc = EncryptionNode("enc", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM)
    dec = EncryptionNode("dec", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM, mode=EncryptionMode.DECRYPT)
    ```

## Extension patterns

- Compose using subgraphs:

  ```python
  from meridian.core import Subgraph
  from meridian.nodes import Router, MapTransformer

  router = Router("r", routing_fn=lambda x: "errors" if isinstance(x, dict) and x.get("error") else "ok", output_ports=["ok", "errors"])
  redact = MapTransformer("redact", transform_fn=lambda d: {**d, "secret": "***"})

  g = Subgraph.from_nodes("authz", [router, redact])
  # wire router.errors -> redact.input; expose ports as needed
  ```

- Wrap domain-specific logic as handler functions:

  ```python
  from meridian.nodes import DataConsumer

  def write_to_db(row: dict) -> None:
      ...
  sink = DataConsumer("db_sink", handler=write_to_db)
  ```

- Subclassing FunctionNode (advanced) — keep the surface small and composed internally. Prefer composition first.

## Policies and errors

- All built-ins support `NodeConfig(error_policy=...)` on construction
- Use `ErrorPolicy.EMIT_ERROR` to propagate standardized error messages downstream
- Prefer attaching backpressure/routing via edges and scheduler config rather than custom logic inside nodes

## Performance notes

- Built-ins are optimized for clarity and composability
- Use `ThrottleNode`, `RetryNode`, `CircuitBreakerNode` to protect downstream systems
- For hotspots, measure first; then consider a custom node or specialized handler

## Migration checklist

- Replace custom synchronous map/filter logic with `MapTransformer` / `FilterTransformer`
- Replace ad-hoc batching with `BatchProducer` / `BatchConsumer` / `BufferNode`
- Replace custom async pools with `AsyncWorker` and tune `max_concurrent`
- Replace plain-text encryption with `EncryptionNode` (AES‑GCM/ChaCha20‑Poly1305)
- Centralize error handling with `ErrorPolicy` and standard error messages

## Example: full graph before/after

=== "Before"

    ```python
    # Custom: ingest → transform → sink
    class Ingest(Node): ...
    class Transform(Node): ...
    class Sink(Node): ...
    ```

=== "After"

    ```python
    from meridian.nodes import DataProducer, MapTransformer, DataConsumer

    prod = DataProducer("ingest", data_source=my_iter, interval_ms=0)
    xf = MapTransformer("xf", transform_fn=my_transform)
    sink = DataConsumer("sink", handler=my_sink)
    ```

!!! info
    Need a richer tutorial? See the example modules under the repository `examples/` directory and the [Built‑in nodes reference](../reference/built-in-nodes.md).
