from __future__ import annotations

from meridian.nodes import (
    FunctionNode,
    ErrorPolicy,
    MergeStrategy,
    DistributionStrategy,
    NodeConfig,
    TimingConfig,
    create_error_message,
    validate_callable,
    setup_standard_ports,
)
from meridian.core import Message, MessageType


class Dummy(FunctionNode):
    def __init__(self) -> None:
        ins, outs = setup_standard_ports(["in"], ["out"])
        super().__init__("dummy", inputs=ins, outputs=outs)
        self._user_function = lambda x: x

    def _handle_message(self, port: str, msg: Message) -> None:
        if msg.type == MessageType.DATA:
            result = self._safe_call_user_function(msg.payload, original_message=msg)
            if result is not None:
                self.emit("out", Message(MessageType.DATA, result))


def test_module_exports_importable() -> None:
    assert ErrorPolicy.LOG_AND_CONTINUE
    assert MergeStrategy.ROUND_ROBIN
    assert DistributionStrategy.ROUND_ROBIN
    assert NodeConfig().error_policy == ErrorPolicy.LOG_AND_CONTINUE
    assert TimingConfig().interval_ms == 100


def test_dummy_node_handles_data() -> None:
    d = Dummy()
    d.on_message("in", Message(MessageType.DATA, 1))
