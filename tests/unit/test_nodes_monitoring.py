from __future__ import annotations

import time

from meridian.core import Message, MessageType
from meridian.nodes import (
    AlertingNode,
    HealthCheckNode,
    MetricsCollectorNode,
    NodeTestHarness,
    SamplingNode,
)


def test_metrics_collector_emits_window_snapshot() -> None:
    mc = MetricsCollectorNode("mc", metric_extractors={"v": lambda x: float(x)}, aggregation_window_ms=5)
    h = NodeTestHarness(mc)
    for i in [1, 2, 3]:
        h.send_message("input", i)
    time.sleep(0.01)
    h.trigger_tick()
    out = h.get_emitted_messages("output")
    assert out and out[0].payload["count"] == 3 and out[0].payload["v"] == 6.0


def test_health_check_node_periodic_emission() -> None:
    hc = HealthCheckNode("hc", health_checks=[lambda: True, lambda: False], check_interval_ms=5)
    h = NodeTestHarness(hc)
    time.sleep(0.01)
    h.trigger_tick()
    out = h.get_emitted_messages("output")
    assert out and out[0].payload["healthy"] is False and out[0].payload["checks"] == [True, False]


def test_alerting_node_emits_alerts_and_notifies() -> None:
    notices: list[str] = []
    al = AlertingNode("al", alert_rules=[lambda p: "high" if p > 5 else None], notification_channels=[notices.append])
    h = NodeTestHarness(al)
    h.send_message("input", 3)
    h.send_message("input", 7)
    out = h.get_emitted_messages("output")
    assert notices == ["high"]
    assert [m.payload for m in out] == [{"alert": "high"}]


def test_sampling_node_random() -> None:
    s = SamplingNode("s", sampling_rate=1.0)
    h = NodeTestHarness(s)
    for i in range(3):
        h.send_message("input", i)
    out = h.get_emitted_messages("output")
    # With rate=1.0, all should pass
    assert [m.payload for m in out] == [0, 1, 2]
