from __future__ import annotations

from meridian.core import Message, MessageType
from meridian.nodes import Merger, Router, Splitter
from meridian.nodes import NodeTestHarness, setup_standard_ports, FunctionNode


class Tap(FunctionNode):
    def __init__(self, name: str, in_port: str = "in") -> None:
        ins, outs = setup_standard_ports([in_port], ["out"])
        super().__init__(name, inputs=ins, outputs=outs)
        self._in = in_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if port == self._in:
            self.emit("out", msg)


def test_router_routes_to_named_ports() -> None:
    r = Router("r", routing_fn=lambda x: "a" if x % 2 == 0 else "b", output_ports=["a", "b"], input_port="in")
    hr = NodeTestHarness(r)
    hr.send_message("in", 1)
    hr.send_message("in", 2)
    out_a = hr.get_emitted_messages("a")
    out_b = hr.get_emitted_messages("b")
    assert [m.payload for m in out_a] == [2]
    assert [m.payload for m in out_b] == [1]


def test_merger_combines_multiple_inputs() -> None:
    m = Merger("m", input_ports=["i1", "i2"], output_port="out")
    hm = NodeTestHarness(m)
    hm.send_message("i1", 10)
    hm.send_message("i2", 20)
    out = hm.get_emitted_messages("out")
    assert [m.payload for m in out] == [10, 20]


def test_splitter_broadcast_and_filters() -> None:
    s = Splitter("s", output_ports=["x", "y"], input_port="in", port_filters={"x": lambda v: v > 5})
    hs = NodeTestHarness(s)
    hs.send_message("in", 3)
    hs.send_message("in", 7)
    out_x = hs.get_emitted_messages("x")
    out_y = hs.get_emitted_messages("y")
    # First payload 3 should only go to y; second 7 goes to both
    assert [m.payload for m in out_x] == [7]
    assert [m.payload for m in out_y] == [3, 7]
