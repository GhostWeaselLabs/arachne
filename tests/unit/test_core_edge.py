from arachne.core import Edge, Port, PortDirection


def test_edge_self_loop() -> None:
    p_out = Port("o", PortDirection.OUTPUT)
    p_in = Port("i", PortDirection.INPUT)
    e = Edge("A", p_out, "A", p_in)
    assert e.is_self_loop()
