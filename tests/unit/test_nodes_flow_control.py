from __future__ import annotations

import time

from meridian.core import Message, MessageType
from meridian.nodes import (
    BackoffStrategy,
    CircuitBreakerNode,
    NodeConfig,
    NodeTestHarness,
    ThrottleNode,
    TimeoutAction,
    TimeoutNode,
    RetryNode,
)


def test_throttle_token_bucket() -> None:
    t = ThrottleNode("t", rate_limit=2.0, burst_size=2)
    h = NodeTestHarness(t)
    # Enqueue 3
    for i in range(3):
        h.send_message("input", i)
    # First tick should emit up to 2
    h.trigger_tick()
    out1 = h.get_emitted_messages("output")
    assert [m.payload for m in out1] == [0, 1]
    # After small wait and tick, remaining should flush
    time.sleep(0.6)
    h.trigger_tick()
    out2 = h.get_emitted_messages("output")
    assert [m.payload for m in out2][-1] == 2


def test_circuit_breaker_transitions() -> None:
    cb = CircuitBreakerNode("cb", failure_threshold=2, recovery_timeout_ms=5, success_threshold=1)
    h = NodeTestHarness(cb)
    # Two errors -> open
    h.send_message("input", Message(MessageType.ERROR, "e1"))
    h.send_message("input", Message(MessageType.ERROR, "e2"))
    # Data now rejected
    h.send_message("input", 1)
    out = h.get_emitted_messages("output")
    assert any(m.type == MessageType.ERROR for m in out)
    # After recovery timeout, half-open
    time.sleep(0.01)
    h.trigger_tick()
    # Next success closes
    h.send_message("input", 2)
    out2 = h.get_emitted_messages("output")
    assert any(m.type == MessageType.DATA and m.payload == 2 for m in out2)


def test_retry_node_with_exponential_backoff_and_dlq() -> None:
    attempts = {"count": 0}

    def handler(x):  # noqa: ANN001
        attempts["count"] += 1
        raise RuntimeError("fail")

    r = RetryNode("r", handler=handler, max_retries=2, backoff_strategy=BackoffStrategy.EXPONENTIAL)
    h = NodeTestHarness(r)
    h.send_message("input", 123)
    # Drive ticks for retries
    for _ in range(5):
        h.trigger_tick()
        time.sleep(0.02)
    out_dlq = h.get_emitted_messages("dead_letter")
    assert any(m.type == MessageType.ERROR for m in out_dlq)


def test_timeout_node_emits_on_timeout() -> None:
    def slow(x):  # noqa: ANN001
        time.sleep(0.02)
        return x

    n = TimeoutNode("to", handler=slow, timeout_ms=5, timeout_action=TimeoutAction.EMIT_ERROR)
    h = NodeTestHarness(n)
    h.send_message("input", 7)
    # Drive ticks while work executes
    for _ in range(5):
        h.trigger_tick()
        time.sleep(0.005)
    out = h.get_emitted_messages("output")
    assert any(m.type == MessageType.ERROR for m in out)
