from __future__ import annotations

import gzip
import io
import os
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Deque

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class EvictionPolicy(str, Enum):
    LRU = "lru"
    FIFO = "fifo"


class PersistenceStrategy(str, Enum):
    MEMORY_ONLY = "memory"
    DISK_ONLY = "disk"


@dataclass(slots=True)
class _CacheEntry:
    value: Any
    expires_at: float | None


class CacheNode(FunctionNode):
    """In-memory caching with TTL and simple eviction policies.

    Expects DATA messages with payload dicts of the form:
      {"op": "set"|"get"|"delete", "key": str, "value"?: Any, "ttl_s"?: int}

    Emits DATA responses for get/set/delete with fields indicating status and value.
    """

    def __init__(
        self,
        name: str,
        max_size: int = 1000,
        ttl_seconds: int = 0,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._max = max(1, int(max_size))
        self._default_ttl = max(0, int(ttl_seconds))
        self._policy = eviction_policy
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()

    def _now(self) -> float:
        return time.time()

    def _evict_if_needed(self) -> None:
        while len(self._store) > self._max:
            if self._policy == EvictionPolicy.FIFO:
                self._store.popitem(last=False)
            else:
                # LRU default: pop least recently used (front)
                self._store.popitem(last=False)

    def _expire(self) -> None:
        now = self._now()
        to_delete = [k for k, v in self._store.items() if v.expires_at is not None and v.expires_at <= now]
        for k in to_delete:
            self._store.pop(k, None)

    def _touch(self, key: str) -> None:
        try:
            self._store.move_to_end(key)
        except KeyError:
            pass

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in or msg.type != MessageType.DATA:
            return
        payload = msg.payload if isinstance(msg.payload, dict) else {}
        op = payload.get("op")
        key = payload.get("key")
        if not isinstance(key, str):
            return
        if op == "set":
            ttl = int(payload.get("ttl_s", self._default_ttl))
            expires = self._now() + ttl if ttl > 0 else None
            self._store[key] = _CacheEntry(payload.get("value"), expires)
            self._touch(key)
            self._evict_if_needed()
            self.emit(self._out, Message(MessageType.DATA, {"op": "set", "key": key, "status": "ok"}))
        elif op == "get":
            self._expire()
            entry = self._store.get(key)
            hit = entry is not None
            if hit:
                self._touch(key)
            self.emit(
                self._out,
                Message(
                    MessageType.DATA,
                    {"op": "get", "key": key, "hit": hit, "value": (entry.value if entry else None)},
                ),
            )
        elif op == "delete":
            existed = key in self._store
            self._store.pop(key, None)
            self.emit(self._out, Message(MessageType.DATA, {"op": "delete", "key": key, "existed": existed}))

    def _handle_tick(self) -> None:
        self._expire()


class BufferNode(FunctionNode):
    """Temporary storage with periodic flush to output.

    For MEMORY_ONLY, accumulates payloads of DATA messages and emits a batch
    list when flush_interval_ms elapses or on CONTROL. For DISK_ONLY, appends
    JSON lines to a file path given at construction; here we implement only
    MEMORY_ONLY for simplicity in tests.
    """

    def __init__(
        self,
        name: str,
        buffer_size: int = 10000,
        persistence_strategy: PersistenceStrategy = PersistenceStrategy.MEMORY_ONLY,
        flush_interval_ms: int = 5000,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._capacity = max(1, int(buffer_size))
        self._strategy = persistence_strategy
        self._flush_ms = max(1, int(flush_interval_ms))
        self._buf: Deque[Any] = deque()
        self._last_flush_ms = 0.0

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _flush(self) -> None:
        if not self._buf:
            return
        batch = list(self._buf)
        self._buf.clear()
        self._last_flush_ms = self._now_ms()
        self.emit(self._out, Message(MessageType.DATA, batch))

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            self._buf.append(msg.payload)
            while len(self._buf) > self._capacity:
                self._buf.popleft()
        elif msg.type == MessageType.CONTROL:
            self._flush()
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if (now - self._last_flush_ms) >= self._flush_ms:
            self._flush()


class FileWriterNode(FunctionNode):
    """Write message payloads to file as lines (UTF-8)."""

    def __init__(
        self,
        name: str,
        file_path: str,
        input_port: str = "input",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], None)
        super().__init__(name, inputs=ins, outputs=outs or [], config=config)
        self._in = input_port
        self._path = file_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)

    def _write_line(self, text: str) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
            f.flush()

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in or msg.type != MessageType.DATA:
            return
        self._write_line(str(msg.payload))


class FileReaderNode(FunctionNode):
    """Read new lines from a file and emit as DATA messages.

    On each tick, reads new content appended to the file and emits each line
    (stripped of trailing newline) as a DATA message.
    """

    def __init__(
        self,
        name: str,
        file_path: str,
        polling_interval_ms: int = 1000,
        follow_mode: bool = True,
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._out = output_port
        self._path = file_path
        self._interval_ms = max(1, int(polling_interval_ms))
        self._last_poll_ms = 0.0
        self._offset = 0
        self._follow = follow_mode

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _handle_tick(self) -> None:
        now = self._now_ms()
        if self._last_poll_ms and (now - self._last_poll_ms) < self._interval_ms:
            return
        self._last_poll_ms = now
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                f.seek(self._offset)
                for line in f:
                    self.emit(self._out, Message(MessageType.DATA, line.rstrip("\n")))
                self._offset = f.tell()
        except FileNotFoundError:
            # No file yet; ignore until it appears
            return
