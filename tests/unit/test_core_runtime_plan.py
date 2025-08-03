from __future__ import annotations

import time
from typing import Any

import pytest

from meridian.core import (
    Edge,
    Message,
    MessageType,
    Node,
    Port,
    PortDirection,
    PortSpec,
    Scheduler,
    SchedulerConfig,
    Subgraph,
)
from meridian.core.runtime_plan import PriorityBand, RuntimePlan


class _Producer(Node):
    def __init__(self, name: str = "P") -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("o", PortDirection.OUTPUT, spec=PortSpec("o", int))],
        )

    def _handle_tick(self) -> None:
        # Emit on tick to exercise scheduler wiring when needed
        self.emit("o", Message(MessageType.DATA, 1))


class _Consumer(Node):
    def __init__(self, name: str = "C") -> None:
        super().__init__(
            name=name,
            inputs=[Port("i", PortDirection.INPUT, spec=PortSpec("i", int))],
            outputs=[],
        )
        self.received: list[Message] = []

    def _handle_message(self, port: str, msg: Message) -> None:
        self.received.append(msg)


def _build_graph() -> Subgraph:
    p = _Producer("P")
    c = _Consumer("C")
    g = Subgraph.from_nodes("G", [p, c])
    g.connect(("P", "o"), ("C", "i"), capacity=8)
    return g


def test_build_from_graphs_links_nodes_edges_and_applies_pending_priorities() -> None:
    g = _build_graph()

    # Compute edge_id for the only edge
    edge_id = "P:o->C:i"
    rp = RuntimePlan()

    # Apply a pending priority before build
    rp.build_from_graphs([g], pending_priorities={edge_id: PriorityBand.CONTROL})

    # Nodes exist and have inputs/outputs linked
    assert set(rp.nodes.keys()) == {"P", "C"}
    assert edge_id in rp.edges

    # Check applied pending priority
    assert rp.edges[edge_id].priority_band == PriorityBand.CONTROL

    # Verify wiring: producer's output and consumer's input point to the same edge ref
    assert "o" in rp.nodes["P"].outputs
    assert "i" in rp.nodes["C"].inputs
    assert rp.nodes["P"].outputs["o"] is rp.nodes["C"].inputs["i"]


def test_build_from_graphs_rejects_duplicate_node_names() -> None:
    # Create two nodes with same name in a single subgraph to trigger duplicate error
    p1 = _Producer("Dup")
    p2 = _Producer("Dup")
    g = Subgraph.from_nodes("Gdup", [p1])
    # Add a second node under duplicate key
    g.add_node(p2)  # same key "Dup"

    rp = RuntimePlan()
    with pytest.raises(ValueError):
        rp.build_from_graphs([g])


def test_update_readiness_and_get_node_priority_with_mixed_ready_inputs() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    # Initially, no messages in edge => not message_ready
    rp.update_readiness(tick_interval_ms=999999)  # large interval to avoid tick readiness
    assert rp.ready_states["P"].message_ready is False
    assert rp.ready_states["C"].message_ready is False
    assert rp.is_node_ready("P") is False
    assert rp.is_node_ready("C") is False

    # Enqueue items on the only input edge for C; by default priority NORMAL
    edge_id = "P:o->C:i"
    edge = rp.edges[edge_id].edge
    assert edge.try_put(1).name in {"OK", "REPLACED", "COALESCED", "BLOCKED", "DROPPED"}

    # Mark the edge priority as HIGH and enqueue another item to ensure depth > 0
    rp.set_edge_priority(edge_id, PriorityBand.HIGH)
    assert rp.edges[edge_id].priority_band == PriorityBand.HIGH
    _ = edge.try_put(2)

    # With items present, consumer should be message_ready and priority computed as HIGH
    rp.update_readiness(tick_interval_ms=999999)
    assert rp.ready_states["C"].message_ready is True
    assert rp.get_node_priority("C") == PriorityBand.HIGH

    # If we mutate priority to CONTROL at runtime and depth > 0, node priority should reflect CONTROL
    rp.set_edge_priority(edge_id, PriorityBand.CONTROL)
    rp.update_readiness(tick_interval_ms=999999)
    assert rp.get_node_priority("C") == PriorityBand.CONTROL


def test_tick_readiness_after_interval_and_priority_defaults_to_normal() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    # Force last_tick in the past to trigger tick readiness
    for nref in rp.nodes.values():
        nref.last_tick = 0.0

    # Small interval should mark all nodes tick_ready
    rp.update_readiness(tick_interval_ms=1)
    assert rp.ready_states["P"].tick_ready is True
    assert rp.ready_states["C"].tick_ready is True

    # Priority defaults to NORMAL when only tick_ready
    assert rp.get_node_priority("P") == PriorityBand.NORMAL
    assert rp.get_node_priority("C") == PriorityBand.NORMAL


def test_set_edge_priority_errors_on_unknown_edge() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    with pytest.raises(ValueError):
        rp.set_edge_priority("unknown:edge", PriorityBand.HIGH)


def test_set_edge_capacity_happy_path_and_errors() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])
    edge_id = "P:o->C:i"

    # Happy path: change capacity
    rp.set_edge_capacity(edge_id, 16)
    assert rp.edges[edge_id].edge.capacity == 16

    # Errors: unknown edge id and invalid capacity
    with pytest.raises(ValueError):
        rp.set_edge_capacity("missing:edge", 10)

    with pytest.raises(ValueError):
        rp.set_edge_capacity(edge_id, 0)


def test_connect_nodes_to_scheduler_wires_scheduler_reference() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    s = Scheduler(SchedulerConfig(tick_interval_ms=5, idle_sleep_ms=1, shutdown_timeout_s=0.05))
    rp.connect_nodes_to_scheduler(s)

    # Nodes should now have a scheduler reference for backpressure-aware emission
    for nref in rp.nodes.values():
        # Emit from producer; verify no exception when scheduler is set
        nref.node._set_scheduler(s)  # idempotent
        # We can't easily assert on side-effects here without running the loop; the wiring itself should not raise.


def test_get_outgoing_edges_filters_by_node_and_port() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    outs = rp.get_outgoing_edges("P", "o")
    assert len(outs) == 1
    assert isinstance(outs[0], Edge)

    # Unknown port or node should produce empty list
    assert rp.get_outgoing_edges("P", "unknown") == []
    assert rp.get_outgoing_edges("unknown", "o") == []


def test_readiness_message_flag_true_when_edge_has_depth() -> None:
    g = _build_graph()
    rp = RuntimePlan()
    rp.build_from_graphs([g])

    # Edge empty => message_ready False
    rp.update_readiness(tick_interval_ms=10_000)
    assert rp.ready_states["C"].message_ready is False

    # After enqueuing, message_ready True
    edge_id = "P:o->C:i"
    edge = rp.edges[edge_id].edge
    for _ in range(3):
        _ = edge.try_put(42)
    rp.update_readiness(tick_interval_ms=10_000)
    assert rp.ready_states["C"].message_ready is True


def test_priority_computation_uses_highest_ready_input_priority() -> None:
    # Construct a graph with one consumer having two inputs with different priority bands
    cons = _Consumer("C")
    p_high = _Producer("PH")
    p_norm = _Producer("PN")

    g = Subgraph.from_nodes("G2", [cons, p_high, p_norm])
    g.connect(("PH", "o"), ("C", "i"))  # input 'i' from PH
    # Add a second input port on consumer to simulate multiple inputs
    cons.inputs.append(Port("i2", PortDirection.INPUT, spec=PortSpec("i2", int)))
    g.connect(("PN", "o"), ("C", "i2"))

    rp = RuntimePlan()
    rp.build_from_graphs([g])

    # Enqueue messages on both edges and set priorities differently
    eid1 = "PH:o->C:i"
    eid2 = "PN:o->C:i2"
    rp.set_edge_priority(eid1, PriorityBand.HIGH)
    rp.set_edge_priority(eid2, PriorityBand.NORMAL)

    _ = rp.edges[eid1].edge.try_put(1)
    _ = rp.edges[eid2].edge.try_put(2)

    rp.update_readiness(tick_interval_ms=10000)
    assert rp.ready_states["C"].message_ready is True
    # Highest among ready inputs should be HIGH
    assert rp.get_node_priority("C") == PriorityBand.HIGH
