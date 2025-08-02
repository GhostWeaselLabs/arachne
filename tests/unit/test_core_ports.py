from meridian.core import Port, PortDirection
from meridian.core.ports import PortSpec


def test_port_directions() -> None:
    p_in = Port("in", PortDirection.INPUT)
    p_out = Port("out", PortDirection.OUTPUT)
    assert p_in.is_input()
    assert p_out.is_output()


def test_port_spec_validate() -> None:
    ps = PortSpec(name="x", schema=int)
    assert ps.validate(1)
    assert not ps.validate("s")
