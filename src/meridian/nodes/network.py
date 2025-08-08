from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict
from urllib import request, error as urlerror
from collections import deque

from .base import ErrorPolicy, FunctionNode, NodeConfig, create_error_message, setup_standard_ports
from ..core.message import Message, MessageType


class HttpClientNode(FunctionNode):
    """Make simple HTTP requests using urllib.

    Expects DATA payloads as dicts: {"method", "url", "headers"?, "body"?}.
    Emits DATA with {"status", "body", "headers"}.
    """

    def __init__(
        self,
        name: str,
        base_url: str | None = None,
        input_port: str = "input",
        output_port: str = "output",
        timeout_seconds: int = 30,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._base = base_url or ""
        self._in = input_port
        self._out = output_port
        self._timeout = float(timeout_seconds)

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in or msg.type != MessageType.DATA:
            if port == self._in and msg.type in (MessageType.ERROR, MessageType.CONTROL):
                self.emit(self._out, msg)
            return
        payload = msg.payload if isinstance(msg.payload, dict) else {}
        method = str(payload.get("method", "GET")).upper()
        url = str(payload.get("url", ""))
        if self._base and url and not url.startswith("http"):
            url = self._base.rstrip("/") + "/" + url.lstrip("/")
        headers = dict(payload.get("headers", {}))
        body = payload.get("body")
        data_bytes = None
        if body is not None:
            if isinstance(body, (bytes, bytearray)):
                data_bytes = bytes(body)
            else:
                # Encode JSON by default
                data_bytes = json.dumps(body).encode("utf-8")
                headers.setdefault("Content-Type", "application/json")
        req = request.Request(url, data=data_bytes, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310 (trusted test env)
                status = getattr(resp, "status", 200)
                resp_headers = dict(resp.headers.items()) if getattr(resp, "headers", None) else {}
                charset = resp_headers.get("content-type", "").split("charset=")[-1] if "charset=" in resp_headers.get("content-type", "") else "utf-8"
                body_text = resp.read().decode(charset or "utf-8")
                self.emit(self._out, Message(MessageType.DATA, {"status": status, "body": body_text, "headers": resp_headers}))
        except Exception as e:  # noqa: BLE001
            if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                self.emit(self._out, create_error_message(e, {"node": self.name, "url": url}, msg))
            elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                self._safe_call_user_function(original_message=msg)  # type: ignore[call-arg]
            else:
                raise


class HttpServerNode(FunctionNode):
    """Test-friendly HTTP server adapter that can be simulated in tests.

    Provides a simulate_request(...) helper to convert an HTTP request shape
    into an output DATA message without running a real server.
    """

    def __init__(self, name: str, output_port: str = "output", config: NodeConfig | None = None) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._out = output_port

    def simulate_request(self, method: str, path: str, body: Any | None = None, headers: dict[str, str] | None = None) -> None:
        payload = {"method": method.upper(), "path": path, "body": body, "headers": dict(headers or {})}
        self.emit(self._out, Message(MessageType.DATA, payload))


class WebSocketNode(FunctionNode):
    """Bidirectional WebSocket node (test-simulated).

    Input port accepts DATA to represent outbound sends. Incoming messages can
    be injected via simulate_incoming(), which emits them to the output port.
    """

    def __init__(self, name: str, url: str, input_port: str = "input", output_port: str = "output", config: NodeConfig | None = None) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._url = url
        self._in = input_port
        self._out = output_port
        self._outbound: list[Any] = []

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            # Record outbound messages (simulated send)
            self._outbound.append(msg.payload)
        elif msg.type in (MessageType.ERROR, MessageType.CONTROL):
            self.emit(self._out, msg)

    def simulate_incoming(self, payload: Any) -> None:
        self.emit(self._out, Message(MessageType.DATA, payload))


# Simple in-memory message queue registry for tests
_QUEUES: Dict[str, Deque[Any]] = {}


class MessageQueueNode(FunctionNode):
    """Integration with an in-memory queue to simulate external MQs.

    Modes:
      - mode="producer": push DATA payloads into a named queue on input.
      - mode="consumer": on tick, pop from queue and emit as DATA.
    """

    def __init__(
        self,
        name: str,
        queue_type: str,
        connection_config: dict,
        queue_name: str,
        mode: str = "producer",
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port] if mode == "producer" else None, [output_port] if mode == "consumer" else None)
        super().__init__(name, inputs=ins, outputs=outs or [], config=config)
        self._queue_key = f"{queue_type}:{queue_name}"
        if self._queue_key not in _QUEUES:
            _QUEUES[self._queue_key] = deque()
        self._mode = mode
        self._in = input_port
        self._out = output_port

    def _handle_message(self, port: str, msg: Message) -> None:
        if self._mode != "producer" or port != self._in or msg.type != MessageType.DATA:
            return
        _QUEUES[self._queue_key].append(msg.payload)

    def _handle_tick(self) -> None:
        if self._mode != "consumer":
            return
        q = _QUEUES[self._queue_key]
        if q:
            item = q.popleft()
            self.emit(self._out, Message(MessageType.DATA, item))
