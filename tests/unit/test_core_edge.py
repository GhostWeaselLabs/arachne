from arachne.core import Edge, Port, PortDirection
from arachne.core.policies import Block, Drop, Latest, PutResult, Coalesce
from arachne.core.ports import PortSpec


def mk_edge(cap: int = 2) -> Edge[int]:
    p_out = Port("o", PortDirection.OUTPUT, spec=PortSpec("o", int))
    p_in = Port("i", PortDirection.INPUT, spec=PortSpec("i", int))
    return Edge("A", p_out, "B", p_in, capacity=cap, spec=PortSpec("i", int))


def test_edge_self_loop() -> None:
    e = mk_edge()
    e.source_node = "X"
    e.target_node = "X"
    assert e.source_node == e.target_node


def test_edge_put_get_latest() -> None:
    e = mk_edge(1)
    r1 = e.try_put(1, Latest())
    r2 = e.try_put(2, Latest())
    assert r1 == PutResult.OK and r2 == PutResult.REPLACED
    assert e.depth() == 1
    assert e.try_get() == 2
    assert e.try_get() is None


def test_edge_block_and_drop() -> None:
    e = mk_edge(1)
    assert e.try_put(1, Block()) == PutResult.OK
    assert e.try_put(2, Block()) == PutResult.BLOCKED
    e2 = mk_edge(1)
    assert e2.try_put(1, Drop()) == PutResult.OK
    assert e2.try_put(2, Drop()) == PutResult.DROPPED


def test_edge_coalesce() -> None:
    e = mk_edge(1)
    pol = Coalesce(lambda a, b: a + b)
    assert e.try_put(1, pol) == PutResult.OK
    assert e.try_put(2, pol) == PutResult.COALESCED
    assert e.try_get() == 3


def test_schema_validation() -> None:
    e = mk_edge(1)
    e.try_put(1, Latest())
    try:
        e.try_put("x", Latest())
    except TypeError:
        pass
    else:
        assert False, "expected TypeError"
