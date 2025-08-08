from __future__ import annotations

import asyncio
import threading
import time

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import AsyncWorker, DataProducer, MapTransformer


def build_graph() -> Subgraph:
    # Producer emits integers 0..9
    p = DataProducer("p", data_source=lambda: iter(range(10)), interval_ms=0)

    # Async worker doubles after small delay (out-of-order completes)
    async def fn(x: int) -> int:
        await asyncio.sleep(0.01 * (x % 3))
        return x * 2

    aw = AsyncWorker("aw", async_fn=fn, max_concurrent=3)
    # Identity map as sink to demonstrate emit
    sink = MapTransformer("sink", transform_fn=lambda x: x)

    g = Subgraph.from_nodes("async_demo", [p, aw, sink])
    g.connect(("p", "output"), ("aw", "input"))
    g.connect(("aw", "output"), ("sink", "input"))
    return g


def main() -> None:
    g = build_graph()
    s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=1))
    s.register(g)
    th = threading.Thread(target=s.run, daemon=True)
    th.start(); time.sleep(0.5); s.shutdown(); th.join()


if __name__ == "__main__":
    main()
