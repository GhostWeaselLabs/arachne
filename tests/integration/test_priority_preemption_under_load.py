"""Integration test: priority preemption under sustained DATA load.

Scenario:
- Two DATA producers flood a shared slow consumer via NORMAL-priority edges.
- A CONTROL producer occasionally emits control messages to the same consumer via a CONTROL-priority edge.
- All edges have tiny capacities to induce pressure and contention.
- Expectation: CONTROL messages preempt DATA and are delivered with bounded latency,
  despite high DATA load. DATA may be dropped or delayed, but CONTROL should pierce through.

Notes:
- We push raw int payloads directly into edges for DATA producers to avoid nested Message payloads.
- CONTROL producer uses Node.emit (CONTROL MessageType) so the Scheduler applies Block() on puts.
- NodeProcessor wraps dequeued payloads using the edge PriorityBand; thus, the consumer sees CONTROL
  MessageTypes only from the control edge, and DATA from the data edges.
- We keep timing short and deterministic, using explicit shutdown and tight tick intervals.

Assertions:
- At least one CONTROL message is received.
- CONTROL messages appear interleaved amid DATA receipts (i.e., not all at the end).
- CONTROL delivery latency is bounded: no CONTROL burst should be delayed excessively relative to tick cadence.
"""

from __future__ import annotations

import time
from threading import Thread
from typing import Any, List, Tuple

import pytest

from meridian.core.message import Message, MessageType
from meridian.core.node import Node
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.core.scheduler import Scheduler, SchedulerConfig
from meridian.core.subgraph import Subgraph
from meridian.core.runtime_plan import PriorityBand


class DataProducer(Node):
    """DATA producer that floods raw ints into its output edge."""

    def __init__(self, name: str) -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", schema=int))],
        )
        self.sent = 0
        self._edge = None

    def set_edge_for_testing(self, edge) -> None:
        self._edge = edge

    def _handle_tick(self) -> None:
        # Emit a small burst each tick to sustain pressure
        for _ in range(3):
            if self._edge is not None:
                self._edge.try_put(self.sent)
            else:
                # Fallback to emit as DATA (not expected path in this test)
                self.emit("out", Message(MessageType.DATA, self.sent))
            self.sent += 1


class ControlProducer(Node):
    """CONTROL producer that occasionally emits a CONTROL message via Node.emit."""

    def __init__(self, name: str = "control") -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("ctrl", PortDirection.OUTPUT, spec=PortSpec("ctrl", schema=int))],
        )
        self.sent = 0
        self._tick_counter = 0

    def _handle_tick(self) -> None:
        # Emit a CONTROL message every few ticks to simulate low-rate control-plane traffic
        self._tick_counter += 1
        if self._tick_counter % 5 == 0:
            self.emit("ctrl", Message(MessageType.CONTROL, self.sent))
            self.sent += 1


class SlowConsumer(Node):
    """Slow consumer that records the sequence of (type, payload) it receives."""

    def __init__(self, name: str = "consumer") -> None:
        super().__init__(
            name=name,
            inputs=[
                Port("d1", PortDirection.INPUT, spec=PortSpec("d1", schema=int)),
                Port("d2", PortDirection.INPUT, spec=PortSpec("d2", schema=int)),
                Port("ctrl_in", PortDirection.INPUT, spec=PortSpec("ctrl_in", schema=int)),
            ],
            outputs=[],
        )
        self.received: List[Tuple[str, int]] = []

    def _handle_message(self, port: str, msg: Message) -> None:
        # Simulate slow processing
        time.sleep(0.001)
        # Record type + payload
        typ = "CTRL" if msg.is_control() else ("ERR" if msg.is_error() else "DATA")
        assert isinstance(msg.payload, int)
        self.received.append((typ, msg.payload))


@pytest.mark.integration
def test_priority_preemption_under_load() -> None:
    # Build nodes
    prod1 = DataProducer("data1")
    prod2 = DataProducer("data2")
    ctrlp = ControlProducer("control")
    cons = SlowConsumer("consumer")

    # Wire subgraph: data producers to consumer (NORMAL), control producer to consumer (CONTROL)
    sg = Subgraph.from_nodes("preempt", [prod1, prod2, ctrlp, cons])
    e_d1 = sg.connect(("data1", "out"), ("consumer", "d1"), capacity=2)
    e_d2 = sg.connect(("data2", "out"), ("consumer", "d2"), capacity=2)
    e_ctrl = sg.connect(("control", "ctrl"), ("consumer", "ctrl_in"), capacity=2)

    # Inject edges to data producers for raw puts
    prod1.set_edge_for_testing(sg.edges[-3])  # order corresponds to append sequence
    prod2.set_edge_for_testing(sg.edges[-2])

    # Scheduler config: fast ticks, small sleep, allow explicit shutdown
    cfg = SchedulerConfig(
        tick_interval_ms=2,
        fairness_ratio=(4, 2, 1),
        max_batch_per_node=4,
        idle_sleep_ms=0,
        shutdown_timeout_s=5.0,
    )
    sched = Scheduler(cfg)

    # Set priorities: control edge -> CONTROL band; data edges remain NORMAL (default).
    sched.set_priority(e_ctrl, PriorityBand.CONTROL)
    # Explicitly ensure data edges are NORMAL for clarity (not strictly required if default)
    sched.set_priority(e_d1, PriorityBand.NORMAL)
    sched.set_priority(e_d2, PriorityBand.NORMAL)

    # Register and run
    sched.register(sg)
    t = Thread(target=sched.run, daemon=True)
    t.start()

    # Let the system run briefly to generate load and interleave control
    time.sleep(0.3)
    sched.shutdown()
    t.join(timeout=2.0)
    assert not t.is_alive(), "Scheduler thread did not stop after shutdown()"

    # Basic sanity: sent and received
    assert prod1.sent >= 1 or prod2.sent >= 1
    assert len(cons.received) >= 1

    # Extract CONTROL and DATA events
    controls = [p for (typ, p) in cons.received if typ == "CTRL"]
    datas = [p for (typ, p) in cons.received if typ == "DATA"]

    # Expect at least one control message delivered despite high DATA load
    assert len(controls) >= 1, "Expected at least one CONTROL message to be delivered"

    # CONTROL should not be starved: check interleaving evidence.
    # Find first and last positions for CONTROL in the sequence; if all CONTROL were at the very end,
    # interleaving would be weak. We allow some tolerance but assert there's at least one CONTROL
    # that appears before the last 10% of the sequence length.
    seq_types = [typ for (typ, _) in cons.received]
    total = len(seq_types)
    # Indexes of CONTROL appearances
    control_positions = [i for i, typ in enumerate(seq_types) if typ == "CTRL"]
    assert control_positions, "Expected CONTROL positions to exist in the received sequence"

    # Interleaving heuristic: some CONTROL should appear before the very end under sustained DATA load
    latest_allowed = max(0, total - max(1, total // 10))
    assert any(pos < latest_allowed for pos in control_positions), (
        "CONTROL messages appear only at the tail; expected preemption to interleave CONTROL earlier"
    )

    # Latency bound heuristic:
    # As the control producer emits every 5 ticks, and tick_interval_ms=2, typical spacing is ~10ms.
    # Given fairness and batching, assert that between two CONTROL receipts there aren't excessive DATA-only
    # stretches. We allow a small upper bound on DATA-run length between CONTROLs.
    # This bound is intentionally loose to avoid flakes while still catching regressions.
    max_allowed_data_run = 25  # corresponds to roughly several scheduling slices under load
    last_ctrl_idx = None
    longest_data_run = 0
    current_run = 0
    for i, typ in enumerate(seq_types):
        if typ == "CTRL":
            if last_ctrl_idx is not None:
                longest_data_run = max(longest_data_run, current_run)
            last_ctrl_idx = i
            current_run = 0
        else:
            current_run += 1
    # Account for the tail run if no trailing control
    longest_data_run = max(longest_data_run, current_run)
    assert (
        longest_data_run <= max_allowed_data_run
    ), f"Excessive DATA-only run between CONTROL deliveries: {longest_data_run} > {max_allowed_data_run}"

    # Final consistency assertions
    # - DATA payloads and CONTROL payloads are ints
    assert all(isinstance(x, int) for x in controls)
    assert all(isinstance(x, int) for x in datas)
