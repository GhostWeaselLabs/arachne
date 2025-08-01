from arachne.core import RoutingPolicy, RetryPolicy, BackpressureStrategy


class Dummy:
    def route_key(self) -> str:
        return "k"


def test_policies_exist_and_routing() -> None:
    assert RetryPolicy.NONE.name == "NONE"
    assert BackpressureStrategy.DROP.name == "DROP"
    rp = RoutingPolicy()
    assert rp.select(Dummy()) == "k"
    assert rp.select(object()) == "default"
