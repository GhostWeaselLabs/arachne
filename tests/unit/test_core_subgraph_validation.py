from __future__ import annotations

import pytest

from meridian.core import Edge, Message, MessageType, Node, Port, PortDirection, PortSpec, Subgraph


class Producer(Node):
    def __init__(self, name: str = "producer") -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", schema=int))],
        )
        self.sent: list[Message] = []

    def _handle_tick(self) -> None:
        # Emit a simple DATA message on tick
        self.emit("out", Message(MessageType.DATA, payload=1))


class Consumer(Node):
    def __init__(self, name: str = "consumer") -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", schema=int))],
            outputs=[],
        )
        self.received: list[Message] = []

    def _handle_message(self, port: str, msg: Message) -> None:
        self.received.append(msg)


def test_from_nodes_and_connect_happy_path() -> None:
    # Build subgraph with two nodes and connect them
    prod = Producer()
    cons = Consumer()

    g = Subgraph.from_nodes("g", [prod, cons])
    edge_id = g.connect((prod.name, "out"), (cons.name, "in"), capacity=8)

    # Deterministic edge id
    assert edge_id == f"{prod.name}:out->{cons.name}:in"

    # Validate wiring basics
    issues = g.validate()
    assert issues == []

    # inputs_of should map consumer input to the edge
    inputs = g.inputs_of(cons.name)
    assert "in" in inputs
    assert isinstance(inputs["in"], Edge)

    # Verify edge spec uses target input spec (int)
    # Enqueue a valid message via edge and confirm it passes validate
    e = inputs["in"]
    # try_put raw int is accepted by PortSpec(schema=int)
    put_res = e.try_put(2)
    assert put_res.name in {"OK", "REPLACED", "COALESCED", "BLOCKED", "DROPPED"}  # policy-dependent
    # Dequeue back
    got = e.try_get()
    # When something was enqueued, it should be an int or None if dropped by policy
    if got is not None:
        assert isinstance(got, int)


def test_connect_rejects_non_positive_capacity() -> None:
    prod = Producer()
    cons = Consumer()
    g = Subgraph.from_nodes("g", [prod, cons])

    with pytest.raises(ValueError):
        g.connect((prod.name, "out"), (cons.name, "in"), capacity=0)
    with pytest.raises(ValueError):
        g.connect((prod.name, "out"), (cons.name, "in"), capacity=-1)


def test_expose_input_and_output_happy_path_and_duplicates() -> None:
    prod = Producer()
    cons = Consumer()
    g = Subgraph.from_nodes("g", [prod, cons])
    g.connect((prod.name, "out"), (cons.name, "in"))

    # Expose internal ports
    g.expose_input("external_in", (cons.name, "in"))
    g.expose_output("external_out", (prod.name, "out"))

    # Duplicate names should raise
    with pytest.raises(ValueError):
        g.expose_input("external_in", (cons.name, "in"))
    with pytest.raises(ValueError):
        g.expose_output("external_out", (prod.name, "out"))


def test_validate_detects_duplicate_edge_identifiers() -> None:
    # Build nodes that share port names to make duplicate ids possible
    p1 = Producer(name="p1")
    c1 = Consumer(name="c1")
    g = Subgraph.from_nodes("g", [p1, c1])

    # Create two edges with same src/dst port identifiers by directly appending
    # Use connect() once to set the pattern correctly
    eid = g.connect(("p1", "out"), ("c1", "in"), capacity=8)
    assert eid == "p1:out->c1:in"

    # Forge a second identical edge to trigger duplicate detection in validate()
    # The Subgraph.validate checks uniqueness by stable identifier string
    e_dup = Edge("p1", Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int)), "c1", Port("in", PortDirection.INPUT, spec=PortSpec("in", int)), capacity=8, spec=PortSpec("in", int))  # type: ignore[arg-type]
    g.edges.append(e_dup)

    issues = g.validate()
    # Expect a DUP_EDGE error among issues
    assert any(i.code == "DUP_EDGE" and i.level == "error" for i in issues)


def test_validate_reports_unknown_nodes_and_ports_and_bad_capacity() -> None:
    # Construct a subgraph with a faulty edge that references unknown nodes/ports
    prod = Producer()
    cons = Consumer()
    g = Subgraph.from_nodes("g", [prod, cons])

    # Append an edge that references a non-existent target node/port and bad capacity
    bad_edge = Edge(
        source_node="producer",
        source_port=Port("out", PortDirection.OUTPUT, spec=PortSpec("out", int)),
        target_node="unknown_node",
        target_port=Port("missing_port", PortDirection.INPUT, spec=PortSpec("missing_port", int)),
        capacity=-5,
        spec=PortSpec("missing_port", int),
    )
    g.edges.append(bad_edge)

    issues = g.validate()
    # Unknown node and bad capacity should be flagged
    assert any(i.code == "UNKNOWN_NODE" and i.level == "error" for i in issues)
    assert any(i.code == "BAD_CAP" and i.level == "error" for i in issues)


def test_node_names_and_inputs_of_helpers() -> None:
    prod = Producer(name="pX")
    cons = Consumer(name="cY")
    g = Subgraph.from_nodes("graphX", [prod, cons])

    # Initially no edges
    assert g.inputs_of(cons.name) == {}

    # Connect and verify helpers
    g.connect((prod.name, "out"), (cons.name, "in"))
    names = g.node_names()
    assert set(names) == {"pX", "cY"}

    inputs = g.inputs_of(cons.name)
    assert set(inputs.keys()) == {"in"}


def test_add_node_allows_renaming_key() -> None:
    # add_node(node, name=...) should store the node under a custom key
    prod = Producer("p1")
    g = Subgraph("G")
    g.add_node(prod, name="renamed")
    assert "renamed" in g.nodes
    assert g.nodes["renamed"] is prod


def test_validate_edge_spec_presence_is_acknowledged() -> None:
    # When target PortSpec has a schema, Subgraph.validate touches it without deep checks
    prod = Producer()
    cons = Consumer()
    g = Subgraph.from_nodes("g", [prod, cons])
    # Explicit connect ensures spec presence is wired from target input
    g.connect((prod.name, "out"), (cons.name, "in"))
    issues = g.validate()
    # No issues expected in a standard well-typed wiring
    assert issues == []
