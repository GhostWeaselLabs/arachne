from meridian.core import Message, MessageType, Node
from meridian.observability.metrics import get_metrics
import pytest


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


class ErrorNode(Node):
    """Node that raises exceptions to test error handling."""

    def __init__(self, raise_in_message: bool = False, raise_in_tick: bool = False) -> None:
        super().__init__("ErrorNode", inputs=[], outputs=[])
        self.raise_in_message = raise_in_message
        self.raise_in_tick = raise_in_tick

    def _handle_message(self, port: str, msg: Message) -> None:
        if self.raise_in_message:
            raise RuntimeError("Test message error")

    def _handle_tick(self) -> None:
        if self.raise_in_tick:
            raise RuntimeError("Test tick error")


class MetricsNode(Node):
    """Node with custom metrics to test edge cases."""

    def __init__(self) -> None:
        super().__init__("MetricsNode", inputs=[], outputs=[])
        # Override metrics to test None scenarios
        self._messages_total = None
        self._errors_total = None


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


def test_node_with_ports_construction() -> None:
    """Test the with_ports class method."""
    node = Node.with_ports("test", ["in1", "in2"], ["out1", "out2"])
    assert node.name == "test"
    assert len(node.inputs) == 2
    assert len(node.outputs) == 2
    assert node.inputs[0].name == "in1"
    assert node.inputs[1].name == "in2"
    assert node.outputs[0].name == "out1"
    assert node.outputs[1].name == "out2"


def test_port_map() -> None:
    """Test port_map method returns correct mapping."""
    node = Node.with_ports("test", ["in1"], ["out1"])
    port_map = node.port_map()
    assert "in1" in port_map
    assert "out1" in port_map
    assert port_map["in1"] == node.inputs[0]
    assert port_map["out1"] == node.outputs[0]


def test_message_error_handling() -> None:
    """Test error handling in on_message method."""
    error_node = ErrorNode(raise_in_message=True)

    # Should raise the exception after recording metrics
    with pytest.raises(RuntimeError, match="Test message error"):
        error_node.on_message("test_port", Message(MessageType.DATA, 1))


def test_tick_error_handling() -> None:
    """Test error handling in on_tick method."""
    error_node = ErrorNode(raise_in_tick=True)

    # Should raise the exception after recording metrics
    with pytest.raises(RuntimeError, match="Test tick error"):
        error_node.on_tick()


def test_metrics_none_handling() -> None:
    """Test behavior when metrics are None (edge case)."""
    metrics_node = MetricsNode()

    # Should not crash when metrics are None
    metrics_node.on_message("test_port", Message(MessageType.DATA, 1))
    metrics_node.on_tick()

    # Error handling should also work with None metrics
    error_metrics_node = ErrorNode(raise_in_message=True)
    error_metrics_node._messages_total = None
    error_metrics_node._errors_total = None

    with pytest.raises(RuntimeError, match="Test message error"):
        error_metrics_node.on_message("test_port", Message(MessageType.DATA, 1))


def test_tick_error_handling_with_none_metrics() -> None:
    """Test tick error handling when metrics are None."""
    error_metrics_node = ErrorNode(raise_in_tick=True)
    error_metrics_node._errors_total = None

    with pytest.raises(RuntimeError, match="Test tick error"):
        error_metrics_node.on_tick()


def test_on_stop_logging() -> None:
    """Test on_stop method logs correctly."""
    node = Node("test")
    # Should not raise any exceptions
    node.on_stop()


def test_handle_message_default_implementation() -> None:
    """Test default _handle_message implementation."""
    node = Node("test")
    # Should return None by default
    result = node._handle_message("test_port", Message(MessageType.DATA, 1))
    assert result is None


def test_handle_tick_default_implementation() -> None:
    """Test default _handle_tick implementation."""
    node = Node("test")
    # Should return None by default
    result = node._handle_tick()
    assert result is None
