from __future__ import annotations

from arachne.core import Message, MessageType, Node, Scheduler, Subgraph


class P(Node):
    def __init__(self) -> None:
        super().__init__("P", inputs=[], outputs=[Node.with_ports("tmp", [], ["out"]).outputs[0]])
        self.did_tick = 0

    def on_tick(self) -> None:
        self.did_tick += 1


class C(Node):
    def __init__(self) -> None:
        super().__init__("C", inputs=[Node.with_ports("tmp", ["in"], []).inputs[0]], outputs=[])
        self.seen = 0

    def on_message(self, port: str, msg: Message) -> None:
        if msg.type == MessageType.DATA:
            self.seen += 1


def test_scheduler_starts_and_processes_message() -> None:
    p = P()
    c = C()
    sg = Subgraph.from_nodes("G", [p, c])
    sg.connect(("P", "out"), ("C", "in"), capacity=1)

    sch = Scheduler()
    sch.register(sg)

    # Pre-fill one message and run for a short period
    edge = sg.edges[0]
    assert edge.try_put(123)

    sch.run()
    sch.shutdown()

    assert c.seen >= 1
    assert p.did_tick >= 0
