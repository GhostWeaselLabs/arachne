---
title: Getting started with built-in nodes
icon: material/rocket-launch
---

# Getting started with built-in nodes

This guide shows how to build a small pipeline using built-in nodes from `meridian.nodes`.

## Install

```bash
uv pip install meridian-runtime
```

## Create a simple pipeline

=== "Producer → Map → Consumer"

```python
from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import DataProducer, MapTransformer, DataConsumer

p = DataProducer("p", data_source=lambda: iter(range(10)), interval_ms=0)
m = MapTransformer("m", transform_fn=lambda x: x * 2)
seen: list[int] = []
c = DataConsumer("c", handler=seen.append)

g = Subgraph.from_nodes("g", [p, m, c])
g.connect(("p", "output"), ("m", "input"))
g.connect(("m", "output"), ("c", "input"))

s = Scheduler(SchedulerConfig())
s.register(g)
import threading, time
th = threading.Thread(target=s.run, daemon=True)
th.start(); time.sleep(0.2); s.shutdown(); th.join()
print(seen)
```

## Next steps

- Explore categories in the [reference for built-in nodes](../reference/built-in-nodes.md).
- Add reliability with `ThrottleNode`, `RetryNode`, or `CircuitBreakerNode`.
- Use `NodeTestHarness` to test nodes in isolation.
