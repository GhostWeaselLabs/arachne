from arachne.core import Subgraph, Node


def test_subgraph_additions() -> None:
    n1 = Node.with_ports("N1", ["in"], ["out"])
    n2 = Node.with_ports("N2", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1, n2])
    assert "N1" in sg.node_names()
    sg.connect(("N1", "out"), ("N2", "in"), capacity=2)
    assert len(sg.edges) == 1
