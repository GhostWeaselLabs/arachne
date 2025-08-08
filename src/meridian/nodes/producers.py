from __future__ import annotations

import time
from typing import Any, Callable, Iterator

from .base import FunctionNode, NodeConfig, setup_standard_ports
from ..core.message import Message, MessageType


class DataProducer(FunctionNode):
    """Produces data messages using a user-provided generator function.

    Emits one item per scheduler tick, respecting a minimum interval in milliseconds.
    When the iterator is exhausted, emits a CONTROL completion message once.
    """

    def __init__(
        self,
        name: str,
        data_source: Callable[[], Iterator[Any]],
        interval_ms: int = 100,
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._make_iter = data_source
        self._it = iter(data_source())
        self._interval_ms = max(0, int(interval_ms))
        self._last_emit_ms = 0.0
        self._done = False
        self._out = output_port

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _handle_tick(self) -> None:
        if self._done:
            return
        now = self._now_ms()
        if self._last_emit_ms and (now - self._last_emit_ms) < self._interval_ms:
            return
        try:
            item = next(self._it)
            self.emit(self._out, Message(MessageType.DATA, item))
            self._last_emit_ms = now
        except StopIteration:
            # Completion: emit a single CONTROL and mark done
            self.emit(self._out, Message(MessageType.CONTROL, {"event": "completed"}))
            self._done = True

    def on_start(self) -> None:  # reset iterator on start
        self._it = iter(self._make_iter())
        self._done = False
        self._last_emit_ms = 0.0


class BatchProducer(FunctionNode):
    """Produces batched data messages with configurable batch sizes and timeout.

    Pulls from the provided iterator on ticks and emits a batch when either
    batch_size is reached or batch_timeout_ms elapses since the first item in
    the current batch. Emits CONTROL on iterator exhaustion, flushing any
    partial batch first.
    """

    def __init__(
        self,
        name: str,
        data_source: Callable[[], Iterator[Any]],
        batch_size: int = 10,
        batch_timeout_ms: int = 1000,
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports(None, [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._make_iter = data_source
        self._it = iter(data_source())
        self._batch_size = max(1, int(batch_size))
        self._timeout_ms = max(1, int(batch_timeout_ms))
        self._batch: list[Any] = []
        self._batch_start_ms = 0.0
        self._done = False
        self._out = output_port

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _flush(self) -> None:
        if self._batch:
            self.emit(self._out, Message(MessageType.DATA, list(self._batch)))
            self._batch.clear()
            self._batch_start_ms = 0.0

    def _handle_tick(self) -> None:
        if self._done:
            return
        # Pull up to batch_size per tick
        try:
            while len(self._batch) < self._batch_size:
                item = next(self._it)
                if not self._batch:
                    self._batch_start_ms = self._now_ms()
                self._batch.append(item)
            # If we filled a batch this tick, emit immediately
            if len(self._batch) >= self._batch_size:
                self._flush()
        except StopIteration:
            # End of stream: flush and emit CONTROL
            self._flush()
            self.emit(self._out, Message(MessageType.CONTROL, {"event": "completed"}))
            self._done = True
        except Exception:
            # Any other iterator error: flush what we have and re-raise via base policy
            self._flush()
            raise

        # Timeout check
        if self._batch and self._batch_start_ms:
            if (self._now_ms() - self._batch_start_ms) >= self._timeout_ms:
                self._flush()

    def on_start(self) -> None:
        self._it = iter(self._make_iter())
        self._batch.clear()
        self._batch_start_ms = 0.0
        self._done = False
