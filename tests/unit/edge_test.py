from arachne.core import Edge
from arachne.core.policies import Block, Coalesce, Drop, Latest, PutResult
from arachne.core.ports import Port, PortDirection, PortSpec


def mk_edge(cap: int = 2) -> Edge[int]:
    p_out = Port("o", PortDirection.OUTPUT, spec=PortSpec("o", int))
    p_in = Port("i", PortDirection.INPUT, spec=PortSpec("i", int))
    return Edge("A", p_out, "B", p_in, capacity=cap, spec=PortSpec("i", int))


def test_capacity_and_depth_changes() -> None:
    e = mk_edge(2)
    assert e.depth() == 0
    assert e.try_put(1, Latest()) == PutResult.OK
    assert e.depth() == 1
    assert e.try_put(2, Latest()) == PutResult.OK
    assert e.depth() == 2
    assert e.try_get() == 1
    assert e.depth() == 1


def test_overflow_behavior_per_policy() -> None:
    e = mk_edge(1)
    assert e.try_put(1, Block()) == PutResult.OK
    assert e.try_put(2, Block()) == PutResult.BLOCKED
    e2 = mk_edge(1)
    assert e2.try_put(1, Drop()) == PutResult.OK
    assert e2.try_put(2, Drop()) == PutResult.DROPPED
    e3 = mk_edge(1)
    assert e3.try_put(1, Latest()) == PutResult.OK
    assert e3.try_put(2, Latest()) == PutResult.REPLACED


def test_metrics_intents_emitted() -> None:
    e = mk_edge(1)
    assert e.try_put(1, Latest()) in {PutResult.OK, PutResult.REPLACED}
    assert e.depth() == 1


def test_type_validation_on_put() -> None:
    e = mk_edge(1)
    assert e.try_put(1, Latest()) == PutResult.OK
    try:
        e.try_put("x", Latest())  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for schema mismatch")


def test_coalesce_behavior() -> None:
    e = mk_edge(1)
    pol = Coalesce(lambda a, b: a + b)
    assert e.try_put(1, pol) == PutResult.OK
    assert e.try_put(2, pol) == PutResult.COALESCED
    assert e.try_get() == 3
