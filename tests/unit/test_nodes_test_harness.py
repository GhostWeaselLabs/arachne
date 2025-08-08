from __future__ import annotations

from meridian.core import Message, MessageType
from meridian.nodes import FunctionNode, NodeConfig, NodeTestHarness, setup_standard_ports


class Echo(FunctionNode):
    def __init__(self) -> None:
        ins, outs = setup_standard_ports(["in"], ["out"])
        super().__init__("echo", inputs=ins, outputs=outs, config=NodeConfig())
        self._user_function = lambda x: x

    def _handle_message(self, port: str, msg: Message) -> None:
        if msg.type == MessageType.DATA:
            value = self._safe_call_user_function(msg.payload, original_message=msg)
            if value is not None:
                self.emit("out", Message(MessageType.DATA, value))


def test_harness_captures_emits() -> None:
    node = Echo()
    h = NodeTestHarness(node)
    h.send_message("in", 42)
    out = h.get_emitted_messages("out")
    assert len(out) == 1
    assert out[0].type == MessageType.DATA
    assert out[0].payload == 42


def test_harness_tick() -> None:
    node = Echo()
    h = NodeTestHarness(node)
    # Should not raise
    h.trigger_tick()
