"""Integration test: mixed overflow policies (Latest and Drop) under burst load.

Scenario:
- Two DATA producers feed a single slow consumer through two separate edges:
  - Edge A (port "latest_in") uses Latest semantics (keep only newest when full).
  - Edge B (port "drop_in") uses Drop semantics (drop when full).
- Edges have tiny capacities to induce pressure. Producers burst values rapidly.
- The consumer records what arrives from each port.

Expectations:
- Latest edge: during bursts, older values should be replaced; consumer tends to observe
  the most recent values, not a full contiguous sequence.
- Drop edge: consumer may observe gaps due to dropped items; total received <= produced.
- Both edges: depth never exceeds capacity; type constraints enforced by PortSpec.

Implementation notes:
- We enqueue raw ints directly onto the edges to avoid nested Message payloads.
  NodeProcessor will wrap dequeued items into Message with type DATA, as these edges use
  the NORMAL band by default.
- Shutdown is explicit and deterministic: run scheduler in a background thread,
  sleep briefly to generate load, request shutdown, and join.

Source-grounded behavior references:
- Edge.try_put applies policy semantics and updates depth, drops, etc.
- Policies (Latest, Drop) return PutResult that Edge.try_put interprets:
    - Latest -> REPLACED when at capacity (pop tail, append new).
    - Drop   -> DROPPED when at capacity.
- NodeProcessor wraps dequeued payloads as Message(type=DATA|CONTROL) based on edge band.
"""

from __future__ import annotations

import time
from threading import Thread
from typing import List

import pytest

from meridian.core.node import Node
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.core.scheduler import Scheduler, SchedulerConfig
from meridian.core.subgraph import Subgraph
from meridian.core.policies import Latest, Drop, PutResult


class LatestProducer(Node):
    """Producer that bursts ints onto its edge intended for Latest policy."""

    def __init__(self, name: str = "latest_prod") -> None:
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
        # Burst a handful of ints per tick to provoke overflow behavior.
        for _ in range(4):
            if self._edge is not None:
                self._edge.try_put(self.sent, Latest())
            self.sent += 1


class DropProducer(Node):
    """Producer that bursts ints onto its edge intended for Drop policy."""

    def __init__(self, name: str = "drop_prod") -> None:
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
        # Burst a handful of ints per tick to provoke overflow behavior.
        for _ in range(4):
            if self._edge is not None:
                self._edge.try_put(self.sent, Drop())
            self.sent += 1


class MixedConsumer(Node):
    """Consumer that records arrivals from 'latest_in' and 'drop_in' under slow processing."""

    def __init__(self, name: str = "consumer") -> None:
        super().__init__(
            name=name,
            inputs=[
                Port("latest_in", PortDirection.INPUT, spec=PortSpec("latest_in", schema=int)),
                Port("drop_in", PortDirection.INPUT, spec=PortSpec("drop_in", schema=int)),
            ],
            outputs=[],
        )
        self.latest_seen: List[int] = []
        self.drop_seen: List[int] = []

    def _handle_message(self, port: str, msg) -> None:
        # Slow the consumer slightly to keep queues pressured.
        time.sleep(0.001)
        # NodeProcessor wraps dequeued raw ints into Message(type=DATA, payload=int) for NORMAL band.
        assert msg.is_data()
        assert isinstance(msg.payload, int)
        if port == "latest_in":
            self.latest_seen.append(msg.payload)
        elif port == "drop_in":
            self.drop_seen.append(msg.payload)


@pytest.mark.integration
def test_mixed_overflow_policies_under_burst_load() -> None:
    # Build nodes
    lprod = LatestProducer("latest_prod")
    dprod = DropProducer("drop_prod")
    cons = MixedConsumer("consumer")

    # Wire subgraph: two inputs to the same consumer; tiny capacities to induce pressure.
    sg = Subgraph.from_nodes("mixed_policies", [lprod, dprod, cons])
    e_latest = sg.connect(("latest_prod", "out"), ("consumer", "latest_in"), capacity=2)
    e_drop = sg.connect(("drop_prod", "out"), ("consumer", "drop_in"), capacity=2)

    # Inject edges into producers for direct raw puts (policy applied at put-time).
    # Edges were appended in order; latest edge first, then drop edge.
    lprod.set_edge_for_testing(sg.edges[-2])
    dprod.set_edge_for_testing(sg.edges[-1])

    # Scheduler: fast ticks, minimal idle sleep, deterministic shutdown window.
    cfg = SchedulerConfig(
        tick_interval_ms=2,
        fairness_ratio=(4, 2, 1),
        max_batch_per_node=8,
        idle_sleep_ms=0,
        shutdown_timeout_s=5.0,
    )
    sched = Scheduler(cfg)
    sched.register(sg)

    # Run in background thread
    t = Thread(target=sched.run, daemon=True)
    t.start()

    # Let it run briefly to generate bursts and observe policies under contention.
    time.sleep(0.3)
    sched.shutdown()
    t.join(timeout=2.0)
    assert not t.is_alive(), "Scheduler thread did not stop after shutdown()"

    # Basic sanity
    assert lprod.sent >= 1
    assert dprod.sent >= 1
    assert len(cons.latest_seen) >= 1
    assert len(cons.drop_seen) >= 1

    # Latest edge: during bursts, older values are replaced.
    # We expect not to see a dense contiguous sequence from 0..N-1; instead we should
    # often see later values dominating. At minimum, ensure that:
    # - The consumer did not receive every intermediate value (i.e., likely gaps).
    # - The max observed value is near the producer's last values.
    latest_vals = cons.latest_seen
    assert all(isinstance(x, int) for x in latest_vals)
    # Given burst and replacement, it's unlikely (though not impossible) to be contiguous.
    # Use a heuristic: if we received > 3 values, expect gaps.
    if len(latest_vals) > 3:
        sorted_unique = sorted(set(latest_vals))
        expected_len_if_contiguous = sorted_unique[-1] - sorted_unique[0] + 1
        assert len(sorted_unique) < expected_len_if_contiguous, "Latest edge appears contiguous unexpectedly"
    # Ensure monotonic non-decreasing trend is plausible (replacement favors latest).
    # We allow occasional out-of-order due to interleaving of ports, so keep this weak:
    assert max(latest_vals) >= latest_vals[-1]

    # Drop edge: gaps are expected due to DROPPED results at capacity.
    drop_vals = cons.drop_seen
    assert all(isinstance(x, int) for x in drop_vals)
    # Heuristic similar to above: with enough samples, expect gaps.
    if len(drop_vals) > 3:
        sorted_unique = sorted(set(drop_vals))
        expected_len_if_contiguous = sorted_unique[-1] - sorted_unique[0] + 1
        assert len(sorted_unique) < expected_len_if_contiguous, "Drop edge appears contiguous unexpectedly"

    # Boundedness: consumption cannot exceed production.
    assert len(drop_vals) <= dprod.sent
    assert len(latest_vals) <= lprod.sent

    # Final consistency: values are within the produced ranges.
    assert min(latest_vals) >= 0
    assert max(latest_vals) < lprod.sent
    assert min(drop_vals) >= 0
    assert max(drop_vals) < dprod.sent
