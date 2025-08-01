from arachne.core import Node, Message, MessageType


def test_node_with_ports_and_handle() -> None:
    n = Node.with_ports("N", ["in"], ["out"])
    assert {"in", "out"} <= set(n.port_map().keys())
    msg = Message(MessageType.DATA, 123)
    assert n.handle(msg) is msg
