from __future__ import annotations

import os
import tempfile
import time

from meridian.core import Message, MessageType
from meridian.nodes import BufferNode, CacheNode, FileReaderNode, FileWriterNode, NodeTestHarness


def test_cache_node_set_get_delete_and_ttl() -> None:
    c = CacheNode("c", max_size=2, ttl_seconds=0)
    h = NodeTestHarness(c)
    # set
    h.send_message("input", {"op": "set", "key": "a", "value": 1})
    # get hit
    h.send_message("input", {"op": "get", "key": "a"})
    # delete
    h.send_message("input", {"op": "delete", "key": "a"})
    out = h.get_emitted_messages("output")
    assert out[0].payload["op"] == "set"
    assert out[1].payload["hit"] is True and out[1].payload["value"] == 1
    assert out[2].payload["existed"] is True

    # TTL expire
    c2 = CacheNode("c2", max_size=2, ttl_seconds=0)
    h2 = NodeTestHarness(c2)
    h2.send_message("input", {"op": "set", "key": "x", "value": 9, "ttl_s": 1})
    time.sleep(1.1)
    h2.trigger_tick()  # triggers expire
    h2.send_message("input", {"op": "get", "key": "x"})
    out2 = h2.get_emitted_messages("output")
    assert out2[-1].payload["hit"] is False


def test_buffer_node_flush_on_interval_and_control() -> None:
    b = BufferNode("b", buffer_size=10, flush_interval_ms=5)
    h = NodeTestHarness(b)
    for i in range(3):
        h.send_message("input", i)
    # Let flush interval pass
    time.sleep(0.01)
    h.trigger_tick()
    out = h.get_emitted_messages("output")
    assert out and out[0].type == MessageType.DATA and out[0].payload == [0, 1, 2]

    # New batch flushed by CONTROL
    for i in range(2):
        h.send_message("input", i)
    h.send_control("input", None)
    out2 = h.get_emitted_messages("output")
    assert any(m.type == MessageType.DATA and m.payload == [0, 1] for m in out2)


def test_file_writer_and_reader_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "log.txt")
        w = FileWriterNode("w", file_path=path)
        r = FileReaderNode("r", file_path=path, polling_interval_ms=1)
        hw = NodeTestHarness(w)
        hr = NodeTestHarness(r)
        for v in ["a", "b", "c"]:
            hw.node.on_message("input", Message(MessageType.DATA, v))
        time.sleep(0.01)
        hr.trigger_tick()
        out = hr.get_emitted_messages("output")
        assert [m.payload for m in out] == ["a", "b", "c"]
