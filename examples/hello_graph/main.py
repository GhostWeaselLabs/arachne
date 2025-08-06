from __future__ import annotations

from meridian.core import Scheduler, Subgraph, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection

from .consumer import Consumer
from .producer import ProducerNode


def build_graph(max_count: int = 5) -> tuple[Subgraph, Consumer]:
    consumer = Consumer()
    sg = Subgraph.from_nodes(
        "hello_graph", [ProducerNode(name="producer", max_count=max_count), consumer]
    )

    # Connect producer->consumer with capacity and policy
    sg.connect(("producer", "output"), ("consumer", "in"), capacity=16)

    return sg, consumer


def main() -> None:
    sg, consumer = build_graph(max_count=5)

    sched = Scheduler()
    sched.register(sg)
    sched.run()

    assert len(consumer.values) == 5


if __name__ == "__main__":
    main()
