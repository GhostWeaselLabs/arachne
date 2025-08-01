# Integration smoke tests for Arachne examples
# This file now includes an M2 minimal wiring test.

from arachne.core import Message, MessageType, Node, Subgraph


class Producer(Node):
    def __init__(self) -> None:
        super().__init__("P", inputs=[], outputs=[Node.with_ports("tmp", [], ["out"]).outputs[0]])


class Consumer(Node):
    def __init__(self) -> None:
        super().__init__("C", inputs=[Node.with_ports("tmp", ["in"], []).inputs[0]], outputs=[])
        self.seen: list[int] = []

    def on_message(self, port: str, msg: Message) -> None:
        if msg.type == MessageType.DATA:
            self.seen.append(int(msg.payload))


def test_minimal_producer_edge_consumer_manual_wiring() -> None:
    p = Producer()
    c = Consumer()
    sg = Subgraph.from_nodes("G", [p, c])
    eid = sg.connect(("P", "out"), ("C", "in"), capacity=2)
    assert eid == "P:out->C:in"
    edge = sg.edges[0]

    p.on_start()
    c.on_start()
    assert edge.try_put(1)
    assert edge.try_put(2)
    m = edge.try_get()
    assert isinstance(m, int)
    c.on_message("in", Message(MessageType.DATA, m))
    m2 = edge.try_get()
    if m2 is not None:
        c.on_message("in", Message(MessageType.DATA, m2))
    c.on_stop()
    p.on_stop()

    assert c.seen in ([1, 2], [2])
