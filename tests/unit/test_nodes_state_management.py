from __future__ import annotations

import time

from meridian.core import Message, MessageType
from meridian.nodes import CounterNode, SessionNode, StateMachineNode, WindowNode, WindowType, NodeTestHarness


def test_state_machine_emits_transitions() -> None:
    def trans(state: str, event: str) -> str:
        return "B" if (state == "A" and event == "go") else state

    sm = StateMachineNode("sm", initial_state="A", transition_fn=trans)
    h = NodeTestHarness(sm)
    h.send_message("input", "go")
    out = h.get_emitted_messages("output")
    assert out and out[0].payload["event"] == "state_changed" and out[0].payload["to"] == "B"


def test_session_node_start_touch_expire() -> None:
    s = SessionNode("s", session_timeout_ms=5, max_sessions=2, session_key_fn=lambda x: x)
    h = NodeTestHarness(s)
    h.send_message("input", "k1")
    h.send_message("input", "k2")
    out1 = h.get_emitted_messages("output")
    assert any(m.payload.get("event") == "session_started" for m in out1)
    # Touch k1 to refresh; wait for timeout to expire k2 first
    time.sleep(0.01)
    h.send_message("input", "k1")
    time.sleep(0.01)
    h.trigger_tick()
    out2 = h.get_emitted_messages("output")
    assert any(m.payload.get("event") == "session_expired" for m in out2)


def test_counter_and_window_nodes() -> None:
    c = CounterNode("c", counter_keys=["a", "b"], summary_interval_ms=5, reset_on_summary=True)
    w = WindowNode("w", window_type=WindowType.TUMBLING, window_size_ms=5)
    hc = NodeTestHarness(c)
    hw = NodeTestHarness(w)
    hc.send_message("input", {"a": 1, "b": 2})
    time.sleep(0.01)
    hc.trigger_tick()
    outc = hc.get_emitted_messages("output")
    assert outc and outc[0].payload == {"a": 1.0, "b": 2.0}

    for i in range(3):
        hw.send_message("input", i)
    time.sleep(0.01)
    hw.trigger_tick()
    outw = hw.get_emitted_messages("output")
    assert outw and isinstance(outw[0].payload, list) and outw[0].payload == [0, 1, 2]
