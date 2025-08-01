from arachne.core import Message, MessageType, Node


class Harness(Node):
    def __init__(self) -> None:
        super().__init__("H", inputs=[], outputs=[Node.with_ports("tmp", [], ["out"]).outputs[0]])
        self.calls: list[str] = []

    def on_start(self) -> None:
        self.calls.append("start")

    def on_message(self, port: str, msg: Message) -> None:
        self.calls.append(f"msg:{port}:{msg.type}")

    def on_tick(self) -> None:
        self.calls.append("tick")

    def on_stop(self) -> None:
        self.calls.append("stop")


def test_lifecycle_hook_order() -> None:
    h = Harness()
    h.on_start()
    h.on_message("out", Message(MessageType.DATA, 1))
    h.on_tick()
    h.on_stop()
    assert h.calls == ["start", "msg:out:MessageType.DATA", "tick", "stop"]


def test_emit_type_and_port_checks() -> None:
    n = Node.with_ports("N", [], ["out"])  # type: ignore[arg-type]
    msg = Message(MessageType.DATA, 1)
    assert n.emit("out", msg) is msg
    try:
        n.emit("nope", msg)
    except KeyError:
        pass
    else:
        raise AssertionError()
