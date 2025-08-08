from __future__ import annotations

import asyncio
from typing import Any

from meridian.core import MessageType
from meridian.nodes import AsyncWorker, NodeConfig, NodeTestHarness, WorkerPool


def test_worker_pool_round_robin() -> None:
    calls: list[Any] = []
    wp = WorkerPool("wp", worker_fn=lambda x: (calls.append(x), x)[1], pool_size=3)
    h = NodeTestHarness(wp)
    for i in range(5):
        h.send_message("input", i)
    out = h.get_emitted_messages("output")
    assert [m.payload for m in out] == [0, 1, 2, 3, 4]


def test_async_worker_ordering_and_concurrency() -> None:
    async def fn(x: int) -> int:
        # Stagger results to test ordering: reverse delay by value
        await asyncio.sleep(0.001 * (3 - (x % 3)))
        return x * 2

    aw = AsyncWorker("aw", async_fn=fn, max_concurrent=2)
    h = NodeTestHarness(aw)
    aw.on_start()
    for i in range(6):
        h.send_message("input", i)
    # Drive ticks while tasks complete
    for _ in range(20):
        h.trigger_tick()
    out = h.get_emitted_messages("output")
    # Despite out-of-order completion, emissions should be in input order doubled
    assert [m.payload for m in out] == [i * 2 for i in range(6)]
    aw.on_stop()
