from __future__ import annotations

import threading
import time

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import DataProducer, MapTransformer, MessageQueueNode


def build_graph() -> Subgraph:
    p = DataProducer("p", data_source=lambda: iter(range(5)), interval_ms=0)
    prod = MessageQueueNode("mq-producer", queue_type="redis", connection_config={}, queue_name="demo", mode="producer")
    cons = MessageQueueNode("mq-consumer", queue_type="redis", connection_config={}, queue_name="demo", mode="consumer")
    sink = MapTransformer("sink", transform_fn=lambda x: x)

    g = Subgraph.from_nodes("mq", [p, prod, cons, sink])
    g.connect(("p", "output"), ("mq-producer", "input"))
    g.connect(("mq-consumer", "output"), ("sink", "input"))
    return g


def main() -> None:
    g = build_graph()
    s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=5))
    s.register(g)
    th = threading.Thread(target=s.run, daemon=True)
    th.start(); time.sleep(0.3); s.shutdown(); th.join()


if __name__ == "__main__":
    main()
