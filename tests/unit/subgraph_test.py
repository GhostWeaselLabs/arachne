from meridian.core import Node, Subgraph


def test_add_connect_validate_ports_and_schemas() -> None:
    n1 = Node.with_ports("N1", ["in"], ["out"])
    n2 = Node.with_ports("N2", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    eid = sg.connect(("N1", "out"), ("N2", "in"), capacity=2)
    assert eid == "N1:out->N2:in"
    issues = sg.validate()
    assert not issues


def test_expose_input_output_map_correctly() -> None:
    n = Node.with_ports("N", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n])
    sg.expose_input("ext_in", ("N", "in"))
    sg.expose_output("ext_out", ("N", "out"))
    assert sg.exposed_inputs["ext_in"] == ("N", "in")
    assert sg.exposed_outputs["ext_out"] == ("N", "out")


def test_validate_returns_issues_for_bad_wiring() -> None:
    n = Node.with_ports("N", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n])
    sg.edges = []
    issues = sg.validate()
    assert isinstance(issues, list)
    sg.expose_input("x", ("NO", "in"))
    sg.expose_output("y", ("NO", "out"))
    issues = sg.validate()
    assert any(i.code == "BAD_EXPOSE_IN" for i in issues)
    assert any(i.code == "BAD_EXPOSE_OUT" for i in issues)


def test_validate_duplicate_edge_reporting() -> None:
    n1 = Node.with_ports("A", ["in"], ["out"])
    n2 = Node.with_ports("B", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    sg.connect(("A", "out"), ("B", "in"), capacity=1)
    sg.connect(("A", "out"), ("B", "in"), capacity=1)
    issues = sg.validate()
    assert any(i.code == "DUP_EDGE" for i in issues)
