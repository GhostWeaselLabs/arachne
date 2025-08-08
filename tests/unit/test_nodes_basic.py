from __future__ import annotations

from collections import deque
from typing import Any, Iterator

from meridian.core import Message, MessageType
from meridian.nodes import (
    BatchConsumer,
    BatchProducer,
    DataConsumer,
    DataProducer,
    FlatMapTransformer,
    MapTransformer,
    NodeConfig,
    NodeTestHarness,
)


def gen_seq(n: int) -> Iterator[int]:
    for i in range(n):
        yield i


def test_data_producer_emits_and_completes() -> None:
    p = DataProducer("p", data_source=lambda: gen_seq(3), interval_ms=0)
    h = NodeTestHarness(p)
    # Tick until completion
    for _ in range(5):
        h.trigger_tick()
    out = h.get_emitted_messages("output")
    types = [m.type for m in out]
    assert types.count(MessageType.DATA) == 3
    assert MessageType.CONTROL in types


def test_batch_producer_emits_batches() -> None:
    p = BatchProducer("p", data_source=lambda: gen_seq(5), batch_size=2, batch_timeout_ms=100)
    h = NodeTestHarness(p)
    for _ in range(10):
        h.trigger_tick()
    out = h.get_emitted_messages("output")
    # Expect 3 batches (2,2,1) + CONTROL
    sizes = [len(m.payload) for m in out if m.type == MessageType.DATA]
    assert sizes == [2, 2, 1]


def test_data_consumer_calls_handler() -> None:
    calls: list[Any] = []
    c = DataConsumer("c", handler=lambda x: calls.append(x))
    h = NodeTestHarness(c)
    h.send_message("input", 10)
    assert calls == [10]


def test_batch_consumer_batches_correctly() -> None:
    batches: list[list[Any]] = []
    c = BatchConsumer("c", batch_handler=lambda xs: batches.append(xs), batch_size=3)
    h = NodeTestHarness(c)
    for i in range(7):
        h.send_message("input", i)
    h.send_control("input", None)
    assert batches == [[0, 1, 2], [3, 4, 5], [6]]


def test_map_and_flatmap_transformers() -> None:
    m = MapTransformer("m", transform_fn=lambda x: x * 2)
    f = FlatMapTransformer("f", transform_fn=lambda x: (x, x + 1))
    hm = NodeTestHarness(m)
    hf = NodeTestHarness(f)

    hm.send_message("input", 3)
    out_m = hm.get_emitted_messages("output")
    assert len(out_m) == 1 and out_m[0].payload == 6

    hf.send_message("input", 3)
    out_f = hf.get_emitted_messages("output")
    assert [m.payload for m in out_f] == [3, 4]
