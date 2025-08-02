from meridian.core import Node, Subgraph


def test_subgraph_connect_and_expose() -> None:
    n1 = Node.with_ports("N1", ["in"], ["out"])
    n2 = Node.with_ports("N2", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    edge_id = sg.connect(("N1", "out"), ("N2", "in"), capacity=2)
    assert len(sg.edges) == 1 and edge_id == "N1:out->N2:in"
    sg.expose_input("ext_in", ("N2", "in"))
    sg.expose_output("ext_out", ("N1", "out"))
    issues = sg.validate()
    assert issues == []


def test_expose_duplicate_names() -> None:
    n = Node.with_ports("N", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n])
    sg.expose_input("x", ("N", "in"))
    try:
        sg.expose_input("x", ("N", "in"))
    except ValueError:
        pass
    else:
        raise AssertionError()


def test_port_existence_and_capacity() -> None:
    n1 = Node.with_ports("A", ["in"], ["out"])
    n2 = Node.with_ports("B", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    sg.connect(("A", "out"), ("B", "in"), capacity=1)
    issues = sg.validate()
    assert not issues
    # duplicate edge id
    sg.connect(("A", "out"), ("B", "in"), capacity=1)
    issues = sg.validate()
    assert any(i.code == "DUP_EDGE" for i in issues)
