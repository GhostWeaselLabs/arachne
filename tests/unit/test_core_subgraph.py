from arachne.core import Node, Subgraph


def test_subgraph_connect_and_expose() -> None:
    n1 = Node.with_ports("N1", ["in"], ["out"])
    n2 = Node.with_ports("N2", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    sg.connect(("N1", "out"), ("N2", "in"), capacity=2)
    assert len(sg.edges) == 1
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
