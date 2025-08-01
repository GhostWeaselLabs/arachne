from arachne.core import Message, MessageType


def test_header_normalization_and_helpers() -> None:
    m = Message(MessageType.DATA, {"x": 1}, metadata={"Trace_ID": "abc", "TIMESTAMP": 123})
    assert m.is_data() and not m.is_error() and not m.is_control()


def test_message_immutability() -> None:
    m = Message(MessageType.CONTROL, "go", metadata={"k": "v"})
    try:
        m.payload = "stop"  # type: ignore[attr-defined]
    except Exception:
        pass
    else:
        raise AssertionError("expected frozen dataclass to prevent mutation")
