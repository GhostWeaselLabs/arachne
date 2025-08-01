from arachne.core import RoutingPolicy
from arachne.core.policies import Block, Coalesce, Drop, Latest, PutResult


class Dummy:
    def route_key(self) -> str:
        return "k"


def test_routing_policy() -> None:
    rp = RoutingPolicy()
    assert rp.select(Dummy()) == "k"
    assert rp.select(object()) == "default"


def test_put_policy_results() -> None:
    blk = Block()
    drp = Drop()
    lat = Latest()
    coal = Coalesce(lambda a, b: b)
    assert blk.on_enqueue(1, 0, 1) == PutResult.OK
    assert blk.on_enqueue(1, 1, 1) == PutResult.BLOCKED
    assert drp.on_enqueue(1, 1, 1) == PutResult.DROPPED
    assert lat.on_enqueue(1, 1, 1) == PutResult.REPLACED
    assert coal.on_enqueue(1, 1, 1) == PutResult.COALESCED
