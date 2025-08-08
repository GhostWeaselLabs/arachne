from __future__ import annotations

import json

from meridian.core import Message, MessageType
from meridian.nodes import (
    CompressionMode,
    CompressionNode,
    EncryptionMode,
    EncryptionNode,
    NodeTestHarness,
    SchemaType,
    SerializationNode,
    ValidationNode,
)


def test_validation_node_callable_schema() -> None:
    v = ValidationNode("v", schema=lambda x: isinstance(x, dict) and "a" in x, schema_type=SchemaType.CALLABLE)
    h = NodeTestHarness(v)
    h.send_message("input", {"a": 1})
    out = h.get_emitted_messages("output")
    assert out and out[0].payload == {"a": 1}


def test_serialization_json_roundtrip() -> None:
    s = SerializationNode("s")
    h = NodeTestHarness(s)
    obj = {"a": 1, "b": [1, 2]}
    # Serialize to text
    h.send_message("input", obj)
    text = h.get_emitted_messages("output")[0].payload
    assert isinstance(text, str)
    # Parse back
    h.send_message("input", text)
    obj2 = h.get_emitted_messages("output")[1].payload
    assert obj2 == obj


def test_compression_gzip_roundtrip() -> None:
    c = CompressionNode("c")
    h = NodeTestHarness(c)
    payload = {"hello": "world"}
    # Compress
    h.send_message("input", payload)
    comp = h.get_emitted_messages("output")[0].payload
    # Decompress
    d = CompressionNode("d", mode=CompressionMode.DECOMPRESS)
    hd = NodeTestHarness(d)
    hd.send_message("input", comp)
    raw = hd.get_emitted_messages("output")[0].payload
    assert json.loads(raw.decode("utf-8")) == payload


def test_encryption_aead_roundtrip_basic() -> None:
    key = b"k" * 32
    e = EncryptionNode("e", encryption_key=key)
    he = NodeTestHarness(e)
    plaintext = b"hello"
    he.send_message("input", plaintext)
    env = he.get_emitted_messages("output")[0].payload

    d = EncryptionNode("d", encryption_key=key, mode=EncryptionMode.DECRYPT)
    hd = NodeTestHarness(d)
    hd.send_message("input", env)
    out = hd.get_emitted_messages("output")[0].payload
    assert out == plaintext
