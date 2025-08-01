from arachne.core import Message, MessageType

essage: Message


def test_message_basic() -> None:
    m = Message(type=MessageType.DATA, payload={"x": 1})
    assert m.is_data()
    assert not m.is_error()
    assert not m.is_control()
