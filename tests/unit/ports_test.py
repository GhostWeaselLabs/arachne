from arachne.core.ports import PortSpec


def test_portspec_creation_and_validate() -> None:
    ps = PortSpec(name="x", schema=int)
    assert ps.validate(1)
    assert not ps.validate("s")


def test_invalid_schema_tuple() -> None:
    ps = PortSpec(name="u", schema=(int, str))
    assert ps.validate(2)
    assert ps.validate("ok")
    assert not ps.validate(1.0)
