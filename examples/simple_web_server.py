from __future__ import annotations

import threading
import time

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import (
    HttpServerNode,
    MapTransformer,
    MetricsCollectorNode,
    Router,
    SerializationNode,
)


def build_graph() -> Subgraph:
    srv = HttpServerNode("srv")
    router = Router(
        "router",
        routing_fn=lambda req: "metrics" if req.get("path") == "/metrics" else "echo",
        output_ports=["metrics", "echo"],
    )
    mc = MetricsCollectorNode(
        "metrics",
        metric_extractors={"requests": lambda req: 1.0},
        aggregation_window_ms=50,
    )
    echo = MapTransformer("echo", transform_fn=lambda req: {"path": req.get("path"), "ok": True})
    ser = SerializationNode("ser")

    g = Subgraph.from_nodes("web", [srv, router, mc, echo, ser])
    g.connect(("srv", "output"), ("router", "input"))
    g.connect(("router", "metrics"), ("metrics", "input"))
    g.connect(("router", "echo"), ("echo", "input"))
    g.connect(("metrics", "output"), ("ser", "input"))
    g.connect(("echo", "output"), ("ser", "input"))
    return g


def main() -> None:
    g = build_graph()
    s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=5))
    s.register(g)

    th = threading.Thread(target=s.run, daemon=True)
    th.start()

    srv = g.nodes["srv"]
    assert isinstance(srv, HttpServerNode)
    for path in ["/", "/echo", "/metrics", "/echo"]:
        srv.simulate_request("GET", path)

    time.sleep(0.2)
    s.shutdown()
    th.join()


if __name__ == "__main__":
    main()
