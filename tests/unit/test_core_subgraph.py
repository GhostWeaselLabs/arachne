from arachne.core import Subgraph, Node, Edge, Port, PortDirection


def test_subgraph_additions() -> None:
    n1 = Node.with_ports("N1", ["in"], ["out"])
    sg = Subgraph.from_nodes("G", [n1])
    assert "N1" in sg.node_names()
    e = Edge("N1", Port("out", PortDirection.OUTPUT), "N1", Port("in", PortDirection.INPUT))
    sg.add_edge(e)
    assert sg.edges and sg.edges[0] == e
