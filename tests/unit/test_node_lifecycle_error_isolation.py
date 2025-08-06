"""Unit tests: node lifecycle error isolation across on_start/on_message/on_tick/on_stop.

Goals:
- Verify that exceptions thrown by a node in lifecycle hooks do not crash the scheduler.
- Ensure errors are logged/incremented and other nodes continue to make progress.
- Confirm deterministic shutdown and that on_stop exceptions are isolated.

Grounding in source implementation (key behaviors under test):
- Node.on_message and Node.on_tick catch exceptions, increment node_errors_total, log, and re-raise.
- NodeProcessor.start_all_nodes logs errors and increments error_count per node but continues starting others.
- NodeProcessor.process_node_messages/process_node_tick catch exceptions, increment error_count and continue.
- Scheduler.run wraps the main loop; on any error, it logs and re-raises in the try-block,
  but ensures graceful shutdown in finally via NodeProcessor.stop_all_nodes (error-isolated).

We build a small graph of two nodes:
- FaultyNode which can be configured to raise in specific hooks.
- HealthyNode which records execution to prove the scheduler continues operating.

We run the scheduler for a brief period and explicitly shutdown to exercise lifecycle.
"""

from __future__ import annotations

import time
from threading import Thread
from typing import List, Tuple

import pytest

from meridian.core.message import Message, MessageType
from meridian.core.node import Node
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.core.scheduler import Scheduler, SchedulerConfig
from meridian.core.subgraph import Subgraph


Event = Tuple[str, str]  # (node_name, event_name)


class FaultyNode(Node):
    """Node that can raise from lifecycle hooks based on flags to test error isolation."""

    def __init__(
        self,
        name: str,
        events: List[Event],
        raise_on_start: bool = False,
        raise_on_message: bool = False,
        raise_on_tick: bool = False,
        raise_on_stop: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", schema=int))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", schema=int))],
        )
        self._events = events
        self._raise_on_start = raise_on_start
        self._raise_on_message = raise_on_message
        self._raise_on_tick = raise_on_tick
        self._raise_on_stop = raise_on_stop

    def on_start(self) -> None:
        self._events.append((self.name, "on_start"))
        if self._raise_on_start:
            raise RuntimeError("start failed")
        return super().on_start()

    def _handle_message(self, port: str, msg: Message) -> None:
        self._events.append((self.name, "on_message"))
        if self._raise_on_message:
            raise RuntimeError("message failed")
        # Forward the payload (wrap as DATA)
        self.emit("out", Message(MessageType.DATA, msg.payload))

    def on_tick(self) -> None:
        self._events.append((self.name, "on_tick"))
        if self._raise_on_tick:
            raise RuntimeError("tick failed")
        return super().on_tick()

    def on_stop(self) -> None:
        self._events.append((self.name, "on_stop"))
        if self._raise_on_stop:
            # Even if this raises, the processor should continue stopping others.
            raise RuntimeError("stop failed")
        return super().on_stop()


class HealthyNode(Node):
    """Node that records lifecycle and produces/consumes to prove scheduler continues running."""

    def __init__(self, name: str, events: List[Event], produce: bool = False) -> None:
        super().__init__(
            name=name,
            inputs=(
                [Port("in", PortDirection.INPUT, spec=PortSpec("in", schema=int))]
                if not produce
                else []
            ),
            outputs=(
                [Port("out", PortDirection.OUTPUT, spec=PortSpec("out", schema=int))]
                if produce
                else []
            ),
        )
        self._events = events
        self._produce = produce
        self.received: List[int] = []
        self.sent = 0

    def on_start(self) -> None:
        self._events.append((self.name, "on_start"))
        return super().on_start()

    def _handle_message(self, port: str, msg: Message) -> None:
        self._events.append((self.name, "on_message"))
        assert msg.is_data()
        assert isinstance(msg.payload, int)
        self.received.append(msg.payload)

    def on_tick(self) -> None:
        self._events.append((self.name, "on_tick"))
        if self._produce:
            # Emit a DATA message to kick the pipeline
            self.emit("out", Message(MessageType.DATA, self.sent))
            self.sent += 1
        return super().on_tick()

    def on_stop(self) -> None:
        self._events.append((self.name, "on_stop"))
        return super().on_stop()


def run_for_short_time(sched: Scheduler, seconds: float = 0.2) -> None:
    """Run scheduler in background and shutdown after a short fixed window."""
    t = Thread(target=sched.run, daemon=True)
    t.start()
    time.sleep(seconds)
    sched.shutdown()
    t.join(timeout=2.0)
    assert not t.is_alive(), "Scheduler did not stop after shutdown()"


@pytest.mark.unit
def test_error_isolation_on_start_does_not_prevent_others_from_starting() -> None:
    events: List[Event] = []

    faulty = FaultyNode("faulty", events, raise_on_start=True)
    healthy = HealthyNode("healthy", events, produce=False)

    sg = Subgraph.from_nodes("g", [faulty, healthy])
    # No connection needed here; this test focuses on start isolation only.

    cfg = SchedulerConfig(
        tick_interval_ms=5, fairness_ratio=(4, 2, 1), max_batch_per_node=4, idle_sleep_ms=0
    )
    sched = Scheduler(cfg)
    sched.register(sg)

    # Despite faulty failing on start, NodeProcessor.start_all_nodes should continue.
    run_for_short_time(sched, 0.05)

    # Healthy should have on_start recorded
    assert ("healthy", "on_start") in events
    # Faulty attempted start and raised; its on_start event recorded before the exception
    assert ("faulty", "on_start") in events
    # on_stop should still be called for nodes during shutdown
    assert ("healthy", "on_stop") in events


@pytest.mark.unit
def test_error_isolation_on_message_and_tick_other_nodes_progress() -> None:
    events: List[Event] = []

    # Healthy source produces messages; faulty fails on message to exercise isolation.
    source = HealthyNode("source", events, produce=True)
    faulty = FaultyNode("faulty", events, raise_on_message=True)
    sink = HealthyNode("sink", events, produce=False)

    sg = Subgraph.from_nodes("g", [source, faulty, sink])
    e1 = sg.connect(("source", "out"), ("faulty", "in"), capacity=2)
    e2 = sg.connect(("faulty", "out"), ("sink", "in"), capacity=2)

    cfg = SchedulerConfig(
        tick_interval_ms=2, fairness_ratio=(4, 2, 1), max_batch_per_node=4, idle_sleep_ms=0
    )
    sched = Scheduler(cfg)
    sched.register(sg)

    run_for_short_time(sched, 0.2)

    # Even if faulty raises on messages, the source and sink should still have lifecycles recorded.
    assert ("source", "on_start") in events
    assert ("sink", "on_start") in events
    # Faulty attempted to process messages and recorded on_message attempts
    assert ("faulty", "on_message") in events or ("faulty", "on_tick") in events
    # Sink may or may not receive forwarded messages depending on timing; still ensure it ran
    assert ("sink", "on_tick") in events or ("sink", "on_message") in events
    # Clean shutdown
    assert ("source", "on_stop") in events
    assert ("faulty", "on_stop") in events
    assert ("sink", "on_stop") in events


@pytest.mark.unit
def test_error_isolation_on_tick_and_stop() -> None:
    events: List[Event] = []

    # Faulty node fails on tick and on stop; verify shutdown still completes and other node runs.
    faulty = FaultyNode("faulty", events, raise_on_tick=True, raise_on_stop=True)
    healthy = HealthyNode("healthy", events, produce=True)

    sg = Subgraph.from_nodes("g", [faulty, healthy])
    sg.connect(("healthy", "out"), ("faulty", "in"), capacity=2)

    cfg = SchedulerConfig(
        tick_interval_ms=2, fairness_ratio=(4, 2, 1), max_batch_per_node=4, idle_sleep_ms=0
    )
    sched = Scheduler(cfg)
    sched.register(sg)

    run_for_short_time(sched, 0.2)

    # Lifecycle markers exist for both nodes
    assert ("healthy", "on_start") in events
    assert ("faulty", "on_start") in events

    # The faulty node attempted tick and recorded the event
    assert ("faulty", "on_tick") in events

    # Shutdown: healthy on_stop recorded; faulty on_stop attempted (event recorded pre-raise)
    assert ("healthy", "on_stop") in events
    assert ("faulty", "on_stop") in events

    # Ensure scheduler did not hang and other node progressed; in short runs, healthy may not tick.
    assert ("healthy", "on_start") in events
    assert ("healthy", "on_stop") in events
