from arachne.core import Node, Message, MessageType


def test_node_with_ports_and_handle() -> None:
    n = Node.with_ports("N", ["in"], ["out"])
    assert {"in", "out"} <= set(n.port_map().keys())
    msg = Message(MessageType.DATA, 123)
    assert n.emit("out", msg) is msg


def test_node_emit_unknown_port() -> None:
    n = Node.with_ports("N", [], ["out"])
    msg = Message(MessageType.DATA, 1)
    try:
        n.emit("nope", msg)
    except KeyError:
        pass
    else:
        assert False
