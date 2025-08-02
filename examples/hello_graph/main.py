from __future__ import annotations

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

    # Connect producer->consumer with capacity and policy
    sg.connect(("producer", "output"), ("consumer", "in"), capacity=16)

    # Validation step (placeholder: Subgraph.validate returns list; raise_if_error to be implemented)
    return sg, consumer


def main() -> None:
    sg, consumer = build_graph(max_count=5)

    sched = Scheduler()
    sched.register(sg)
    sched.run()

    assert len(consumer.values) == 5


if __name__ == "__main__":
    main()
