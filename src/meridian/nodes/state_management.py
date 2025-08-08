from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Deque, Dict, Optional

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class WindowType(str, Enum):
    TUMBLING = "tumbling"


class StateMachineNode(FunctionNode):
    """Finite state machine coordinator with event emission on transitions."""

    def __init__(
        self,
        name: str,
        initial_state: str,
        transition_fn: Callable[[str, Any], str],
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._state = initial_state
        self._transition = transition_fn

    @property
    def state(self) -> str:
        return self._state

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            try:
                new_state = self._transition(self._state, msg.payload)
            except Exception:
                # Ignore transition errors
                return
            if new_state != self._state:
                prev = self._state
                self._state = new_state
                self.emit(
                    self._out,
                    Message(
                        MessageType.DATA,
                        {"event": "state_changed", "from": prev, "to": new_state},
                    ),
                )
        else:
            self.emit(self._out, msg)


@dataclass
class _Session:
    key: str
    last_seen_ms: float
    data: dict[str, Any]


class SessionNode(FunctionNode):
    """Manage stateful sessions with timeout and cleanup.

    Emits DATA events for session start and expiration.
    """

    def __init__(
        self,
        name: str,
        session_timeout_ms: int = 300000,
        max_sessions: int = 10000,
        session_key_fn: Callable[[Any], str] | None = None,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._timeout = max(1, int(session_timeout_ms))
        self._max = max(1, int(max_sessions))
        self._key_fn = session_key_fn or (lambda x: str(x))
        self._sessions: Dict[str, _Session] = {}
        self._order: Deque[str] = deque()

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _touch(self, key: str) -> None:
        if key in self._sessions:
            self._sessions[key].last_seen_ms = self._now_ms()
            try:
                self._order.remove(key)
            except ValueError:
                pass
            self._order.append(key)

    def _start(self, key: str) -> None:
        self._sessions[key] = _Session(key=key, last_seen_ms=self._now_ms(), data={})
        self._order.append(key)
        self.emit(self._out, Message(MessageType.DATA, {"event": "session_started", "key": key}))

    def _expire(self, key: str) -> None:
        self._sessions.pop(key, None)
        try:
            self._order.remove(key)
        except ValueError:
            pass
        self.emit(self._out, Message(MessageType.DATA, {"event": "session_expired", "key": key}))

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            key = self._key_fn(msg.payload)
            if key not in self._sessions:
                if len(self._sessions) >= self._max:
                    # Evict oldest
                    oldest = self._order.popleft()
                    self._expire(oldest)
                self._start(key)
            self._touch(key)
        else:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        # Expire from the left
        while self._order:
            k = self._order[0]
            sess = self._sessions.get(k)
            if not sess:
                self._order.popleft()
                continue
            if (now - sess.last_seen_ms) >= self._timeout:
                self._expire(k)
            else:
                break


class CounterNode(FunctionNode):
    """Maintain counters and emit periodic summaries."""

    def __init__(
        self,
        name: str,
        counter_keys: list[str],
        summary_interval_ms: int = 60000,
        reset_on_summary: bool = False,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._keys = counter_keys
        self._interval_ms = max(1, int(summary_interval_ms))
        self._reset = reset_on_summary
        self._counts: Dict[str, float] = {k: 0.0 for k in self._keys}
        self._last_emit_ms = 0.0

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            payload = msg.payload
            if isinstance(payload, dict):
                for k in self._keys:
                    v = payload.get(k)
                    if isinstance(v, (int, float)):
                        self._counts[k] += float(v)
            elif isinstance(payload, str) and payload in self._keys:
                self._counts[payload] += 1.0
        else:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if not self._last_emit_ms:
            self._last_emit_ms = now - self._interval_ms
        if (now - self._last_emit_ms) >= self._interval_ms:
            snapshot = {k: self._counts[k] for k in self._keys}
            self.emit(self._out, Message(MessageType.DATA, snapshot))
            self._last_emit_ms = now
            if self._reset:
                self._counts = {k: 0.0 for k in self._keys}


class WindowNode(FunctionNode):
    """Tumbling window processor with optional aggregation function."""

    def __init__(
        self,
        name: str,
        window_type: WindowType = WindowType.TUMBLING,
        window_size_ms: int = 60000,
        slide_interval_ms: int | None = None,
        aggregation_fn: Callable[[list[Any]], Any] | None = None,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._wtype = window_type
        self._wsize = max(1, int(window_size_ms))
        self._agg = aggregation_fn
        self._buf: list[Any] = []
        self._start_ms = 0.0

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _flush(self) -> None:
        if not self._buf:
            return
        payload = self._agg(self._buf) if self._agg is not None else list(self._buf)
        self.emit(self._out, Message(MessageType.DATA, payload))
        self._buf = []
        self._start_ms = self._now_ms()

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            if not self._buf:
                self._start_ms = self._now_ms()
            self._buf.append(msg.payload)
        else:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        if self._buf and (self._now_ms() - self._start_ms) >= self._wsize:
            self._flush()
