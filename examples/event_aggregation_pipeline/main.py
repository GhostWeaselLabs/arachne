from __future__ import annotations

import threading
import time
from random import randint

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import DataProducer, EventAggregator, MapTransformer


def build_graph() -> Subgraph:
    # Producer emits random small ints
    def gen():
        for _ in range(30):
            yield randint(1, 5)

    p = DataProducer("p", data_source=gen, interval_ms=0)
    # Aggregate sum over 50ms windows
    agg = EventAggregator("agg", window_ms=50, aggregation_fn=lambda xs: {"sum": sum(xs), "n": len(xs)})
    sink = MapTransformer("sink", transform_fn=lambda x: x)

    g = Subgraph.from_nodes("event_agg", [p, agg, sink])
    g.connect(("p", "output"), ("agg", "input"))
    g.connect(("agg", "output"), ("sink", "input"))
    return g


def main() -> None:
    g = build_graph()
    s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=5))
    s.register(g)
    th = threading.Thread(target=s.run, daemon=True)
    th.start(); time.sleep(0.3); s.shutdown(); th.join()


if __name__ == "__main__":
    main()
