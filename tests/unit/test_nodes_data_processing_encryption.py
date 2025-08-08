from __future__ import annotations

import json

from meridian.core import Message, MessageType
from meridian.nodes import (
    EncryptionAlgorithm,
    EncryptionMode,
    EncryptionNode,
    NodeTestHarness,
)


def test_encryption_aes_gcm_roundtrip() -> None:
    key = b"0" * 32
    e = EncryptionNode("e", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM)
    d = EncryptionNode("d", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM, mode=EncryptionMode.DECRYPT)
    he = NodeTestHarness(e)
    hd = NodeTestHarness(d)

    payload = {"hello": "world"}
    he.send_message("input", payload)
    env = he.get_emitted_messages("output")[0].payload
    assert isinstance(env, dict) and "ciphertext" in env and "nonce" in env

    hd.send_message("input", env)
    out = hd.get_emitted_messages("output")[0].payload
    # Decrypted bytes; decode JSON
    obj = json.loads(out.decode("utf-8"))
    assert obj == payload


def test_encryption_chacha20_poly1305_roundtrip() -> None:
    key = b"1" * 32
    e = EncryptionNode("e", encryption_key=key, algorithm=EncryptionAlgorithm.CHACHA20_POLY1305)
    d = EncryptionNode(
        "d", encryption_key=key, algorithm=EncryptionAlgorithm.CHACHA20_POLY1305, mode=EncryptionMode.DECRYPT
    )
    he = NodeTestHarness(e)
    hd = NodeTestHarness(d)

    payload = b"hello"
    he.send_message("input", payload)
    env = he.get_emitted_messages("output")[0].payload
    hd.send_message("input", env)
    out = hd.get_emitted_messages("output")[0].payload
    assert out == payload
