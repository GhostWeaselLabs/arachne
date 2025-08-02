from __future__ import annotations

from arachne.core.edge import Edge
from arachne.core.policies import block
from arachne.core.ports import PortSpec
from arachne.core.scheduler import Scheduler
from arachne.core.subgraph import Subgraph

from .consumer import Consumer
from .producer import ProducerNode


def build_graph(max_count: int = 5) -> tuple[Subgraph, Consumer]:
    sg = Subgraph(name="hello_graph")

    producer = ProducerNode(name="producer", max_count=max_count)
    consumer = Consumer()

    sg.add_node(producer)
    sg.add_node(consumer, name="consumer")

    out_spec = PortSpec(name="output", schema=int)
    in_spec = PortSpec(name="in", schema=int)

    edge = Edge(
        src=("producer", out_spec),
        dst=("consumer", in_spec),
        capacity=16,
        policy=block(),
    )
    sg.connect(edge)

    sg.validate().raise_if_error()
    return sg, consumer


def main() -> None:
    sg, consumer = build_graph(max_count=5)

    sched = Scheduler(subgraph=sg)
    sched.run(ticks=10)

    assert len(consumer.values) == 5


if __name__ == "__main__":
    main()
