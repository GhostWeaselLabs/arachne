import os
import time

import pytest

from meridian.core import Edge
from meridian.core.policies import Latest
from meridian.core.ports import Port, PortDirection, PortSpec


def mk_edge(cap: int = 1024) -> Edge[int]:
    p_out = Port("o", PortDirection.OUTPUT, spec=PortSpec("o", int))
    p_in = Port("i", PortDirection.INPUT, spec=PortSpec("i", int))
    return Edge("A", p_out, "B", p_in, capacity=cap, spec=PortSpec("i", int))


@pytest.mark.benchmark
def test_micro_benchmark_edge_put_get_smoke() -> None:
    e = mk_edge(1024)
    n = 20_000
    pol = Latest()

    t0 = time.perf_counter()
    for i in range(n):
        e.try_put(i, pol)
    for _ in range(min(n, e.depth())):
        _ = e.try_get()
    dt = time.perf_counter() - t0

    # In warn-only mode, keep a soft target; in enforced mode (nightly/main) use stricter bound.
    warn_only = os.getenv("MERIDIAN_BENCH_WARN_ONLY", "1") == "1"
    bound = 0.75 if warn_only else 0.5
    assert dt < bound
