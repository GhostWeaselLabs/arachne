from __future__ import annotations

import base64
import gzip
import io
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .base import ErrorPolicy, FunctionNode, NodeConfig, create_error_message, setup_standard_ports
from ..core.message import Message, MessageType


class SchemaType(str, Enum):
    JSON_SCHEMA = "json_schema"
    CALLABLE = "callable"


class SerializationFormat(str, Enum):
    JSON = "json"


class CompressionType(str, Enum):
    GZIP = "gzip"


class CompressionMode(str, Enum):
    COMPRESS = "compress"
    DECOMPRESS = "decompress"


class EncryptionAlgorithm(str, Enum):
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class EncryptionMode(str, Enum):
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


class ValidationNode(FunctionNode):
    """Validate message payloads against schemas.

    - schema_type JSON_SCHEMA: uses jsonschema if available; otherwise fails closed.
    - schema_type CALLABLE: expects schema to be Callable[[Any], bool].
    On success, forwards DATA payload unchanged to output; on failure, behavior depends on error policy.
    """

    def __init__(
        self,
        name: str,
        schema: Any,
        schema_type: SchemaType = SchemaType.CALLABLE,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._schema = schema
        self._stype = schema_type
        self._in = input_port
        self._out = output_port

    def _validate(self, value: Any) -> bool:
        if self._stype == SchemaType.CALLABLE and callable(self._schema):
            try:
                return bool(self._schema(value))
            except Exception:
                return False
        if self._stype == SchemaType.JSON_SCHEMA:
            try:
                import jsonschema  # type: ignore

                jsonschema.validate(instance=value, schema=self._schema)
                return True
            except Exception:
                return False
        return False

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            ok = self._validate(msg.payload)
            if ok:
                self.emit(self._out, msg)
            else:
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    self.emit(self._out, create_error_message(ValueError("validation_failed"), {"node": self.name}, msg))
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
                else:
                    raise ValueError("validation_failed")
        else:
            self.emit(self._out, msg)


class SerializationNode(FunctionNode):
    """Convert between different data formats.

    Currently supports JSON <-> str conversions:
      - If payload is a str and format is JSON, it is parsed to Python object.
      - If payload is not a str, it is serialized to JSON text.
    """

    def __init__(
        self,
        name: str,
        input_format: SerializationFormat = SerializationFormat.JSON,
        output_format: SerializationFormat = SerializationFormat.JSON,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._iformat = input_format
        self._oformat = output_format

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            payload = msg.payload
            try:
                if isinstance(payload, str):
                    # Parse JSON text -> object
                    value = json.loads(payload)
                else:
                    # Serialize object -> JSON text
                    value = json.dumps(payload)
                self.emit(self._out, Message(MessageType.DATA, value))
            except Exception as e:  # noqa: BLE001
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    self.emit(self._out, create_error_message(e, {"node": self.name}, msg))
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
                else:
                    raise
        else:
            self.emit(self._out, msg)


class CompressionNode(FunctionNode):
    """Compress and decompress message payloads using gzip."""

    def __init__(
        self,
        name: str,
        compression_type: CompressionType = CompressionType.GZIP,
        compression_level: int = 6,
        mode: CompressionMode = CompressionMode.COMPRESS,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._ctype = compression_type
        self._level = int(compression_level)
        self._mode = mode

    def _to_bytes(self, payload: Any) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        if isinstance(payload, str):
            return payload.encode("utf-8")
        return json.dumps(payload).encode("utf-8")

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            try:
                if self._ctype == CompressionType.GZIP:
                    if self._mode == CompressionMode.COMPRESS:
                        data = self._to_bytes(msg.payload)
                        out = gzip.compress(data, compresslevel=self._level)
                        self.emit(self._out, Message(MessageType.DATA, out))
                    else:
                        raw = msg.payload if isinstance(msg.payload, (bytes, bytearray)) else base64.b64decode(msg.payload) if isinstance(msg.payload, str) else bytes(msg.payload)
                        out = gzip.decompress(raw)
                        self.emit(self._out, Message(MessageType.DATA, out))
                else:
                    self.emit(self._out, msg)
            except Exception as e:  # noqa: BLE001
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    self.emit(self._out, create_error_message(e, {"node": self.name}, msg))
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
                else:
                    raise
        else:
            self.emit(self._out, msg)


class EncryptionNode(FunctionNode):
    """Encrypt and decrypt payloads using modern AEAD ciphers (AES-GCM/ChaCha20-Poly1305)."""

    def __init__(
        self,
        name: str,
        encryption_key: bytes,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        mode: EncryptionMode = EncryptionMode.ENCRYPT,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._key = bytes(encryption_key)
        self._alg = algorithm
        self._mode = mode

    def _to_bytes(self, payload: Any) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        if isinstance(payload, str):
            return payload.encode("utf-8")
        return json.dumps(payload).encode("utf-8")

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
                import os

                aad = json.dumps(msg.headers or {}, sort_keys=True).encode("utf-8")
                if self._mode == EncryptionMode.ENCRYPT:
                    raw = self._to_bytes(msg.payload)
                    if self._alg == EncryptionAlgorithm.AES_256_GCM:
                        if len(self._key) not in (16, 24, 32):
                            raise ValueError("AES key must be 128/192/256 bits")
                        cipher = AESGCM(self._key)
                        nonce = os.urandom(12)
                        ct = cipher.encrypt(nonce, raw, aad)
                        # AESGCM includes tag at end of ciphertext; expose envelope
                        env = {"alg": self._alg.value, "nonce": nonce, "ciphertext": ct, "aad": aad}
                        self.emit(self._out, Message(MessageType.DATA, env))
                    else:
                        cipher = ChaCha20Poly1305(self._key)
                        nonce = os.urandom(12)
                        ct = cipher.encrypt(nonce, raw, aad)
                        env = {"alg": self._alg.value, "nonce": nonce, "ciphertext": ct, "aad": aad}
                        self.emit(self._out, Message(MessageType.DATA, env))
                else:
                    env = msg.payload
                    if not isinstance(env, dict) or "nonce" not in env or "ciphertext" not in env:
                        raise ValueError("invalid encryption envelope")
                    aad = env.get("aad", b"")
                    if self._alg == EncryptionAlgorithm.AES_256_GCM:
                        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

                        cipher = AESGCM(self._key)
                        out = cipher.decrypt(env["nonce"], env["ciphertext"], aad)
                        self.emit(self._out, Message(MessageType.DATA, out))
                    else:
                        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

                        cipher = ChaCha20Poly1305(self._key)
                        out = cipher.decrypt(env["nonce"], env["ciphertext"], aad)
                        self.emit(self._out, Message(MessageType.DATA, out))
            except Exception as e:  # noqa: BLE001
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    self.emit(self._out, create_error_message(e, {"node": self.name}, msg))
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
                else:
                    raise
        else:
            self.emit(self._out, msg)
