from __future__ import annotations

import time

from meridian.core import MessageType
from meridian.nodes import EventAggregator, EventCorrelator, NodeTestHarness, TriggerNode


def test_event_aggregator_time_window() -> None:
    agg = EventAggregator("agg", window_ms=1, aggregation_fn=lambda xs: sum(xs))
    h = NodeTestHarness(agg)
    for v in [1, 2, 3]:
        h.send_message("input", v)
    # No tick yet, should not emit
    assert h.get_emitted_messages("output") == []
    # After tick and tiny sleep to pass window
    time.sleep(0.002)
    h.trigger_tick()
    out = h.get_emitted_messages("output")
    assert len(out) >= 1
    assert out[0].payload == 6


def test_event_correlator_completion_and_timeout() -> None:
    corr = EventCorrelator(
        "corr",
        correlation_fn=lambda x: x[0],
        completion_predicate=lambda items: len(items) >= 2,
        timeout_ms=1,
    )
    h = NodeTestHarness(corr)
    h.send_message("input", ("a", 1))
    h.send_message("input", ("a", 2))  # should complete
    out = h.get_emitted_messages("output")
    assert out and out[0].payload["key"] == "a"
    # Send partial group and enforce timeout
    h.send_message("input", ("b", 1))
    time.sleep(0.002)
    h.trigger_tick()
    out2 = h.get_emitted_messages("output")
    assert any(p.payload.get("timeout") for p in out2 if p.type == MessageType.DATA)


def test_trigger_node_emits_on_rising_edge() -> None:
    state = {"flag": False}

    def trigger():
        return state["flag"]

    t = TriggerNode("t", trigger_fn=trigger, trigger_payload=123, check_interval_ms=1)
    h = NodeTestHarness(t)
    h.trigger_tick()
    assert h.get_emitted_messages("output") == []
    state["flag"] = True
    time.sleep(0.002)
    h.trigger_tick()
    out = h.get_emitted_messages("output")
    assert out and out[0].payload == 123
