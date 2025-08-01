from arachne.core import Port, PortDirection


def test_port_directions() -> None:
    p_in = Port("in", PortDirection.INPUT)
    p_out = Port("out", PortDirection.OUTPUT)
    assert p_in.is_input()
    assert p_out.is_output()
