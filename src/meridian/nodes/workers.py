from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from concurrent.futures import Future
from typing import Any, Awaitable, Callable, Deque, Dict, Tuple

from .base import (
    DistributionStrategy,
    ErrorPolicy,
    FunctionNode,
    NodeConfig,
    create_error_message,
    setup_standard_ports,
)
from ..core.message import Message, MessageType


class WorkerPool(FunctionNode):
    """Distributes work across multiple processing functions.

    Within the cooperative model, distribution selects a logical worker index,
    but execution remains synchronous in the node context. Results are emitted
    as DATA messages; CONTROL/ERROR messages are forwarded unchanged.
    """

    def __init__(
        self,
        name: str,
        worker_fn: Callable[[Any], Any],
        pool_size: int = 4,
        input_port: str = "input",
        output_port: str = "output",
        distribution_strategy: DistributionStrategy = DistributionStrategy.ROUND_ROBIN,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._user_function = worker_fn
        self._pool_size = max(1, int(pool_size))
        self._in = input_port
        self._out = output_port
        self._strategy = distribution_strategy
        self._rr_counter = 0

    def _select_worker(self, payload: Any) -> int:
        if self._strategy == DistributionStrategy.ROUND_ROBIN:
            idx = self._rr_counter % self._pool_size
            self._rr_counter += 1
            return idx
        if self._strategy == DistributionStrategy.HASH_BASED:
            try:
                return hash(payload) % self._pool_size
            except Exception:
                # Fallback to rr
                idx = self._rr_counter % self._pool_size
                self._rr_counter += 1
                return idx
        # LOAD_BASED not modeled; default rr
        idx = self._rr_counter % self._pool_size
        self._rr_counter += 1
        return idx

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            _ = self._select_worker(msg.payload)
            result = self._safe_call_user_function(msg.payload, original_message=msg)
            if result is not None:
                self.emit(self._out, Message(MessageType.DATA, result))
        else:
            # Forward control/error
            self.emit(self._out, msg)


class AsyncWorker(FunctionNode):
    """Handles async processing functions with ordering and concurrency limits.

    Messages are assigned monotonically increasing sequence numbers. Completed
    results are emitted in input order to maintain ordering guarantees.
    """

    def __init__(
        self,
        name: str,
        async_fn: Callable[[Any], Awaitable[Any]],
        input_port: str = "input",
        output_port: str = "output",
        max_concurrent: int = 10,
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._async_fn = async_fn
        self._in = input_port
        self._out = output_port
        self._max_concurrent = max(1, int(max_concurrent))

        # Sequencing and queues
        self._next_seq: int = 0
        self._next_emit: int = 0
        self._waiting: Deque[Tuple[int, Message]] = deque()
        self._pending: int = 0
        self._completed: Dict[int, Tuple[bool, Any, Message]] = {}

        # Async loop management
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def on_start(self) -> None:
        # Spawn a background event loop for async execution
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name=f"{self.name}-loop", daemon=True)
        self._thread.start()

    def on_stop(self) -> None:
        # Shutdown background loop
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)

    def _submit(self, seq: int, msg: Message) -> None:
        if not self._loop:
            return
        self._pending += 1
        # Schedule coroutine on background loop
        fut: Future = asyncio.run_coroutine_threadsafe(self._async_fn(msg.payload), self._loop)

        def _done_callback(f: Future) -> None:
            try:
                res = f.result()
                success = True
                val = res
            except Exception as e:  # noqa: BLE001
                success = False
                val = e
            finally:
                # Record completion; emit will occur on tick respecting order
                self._completed[seq] = (success, val, msg)
                self._pending -= 1

        fut.add_done_callback(_done_callback)

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            seq = self._next_seq
            self._next_seq += 1
            if self._pending < self._max_concurrent:
                self._submit(seq, msg)
            else:
                self._waiting.append((seq, msg))
        else:
            # Forward control/error as-is
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        # Fill available slots
        while self._pending < self._max_concurrent and self._waiting:
            seq, msg = self._waiting.popleft()
            self._submit(seq, msg)

        # Emit in order for any completed results
        while self._next_emit in self._completed:
            success, val, orig = self._completed.pop(self._next_emit)
            if success:
                self.emit(self._out, Message(MessageType.DATA, val))
            else:
                # Error policy handling
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    err = create_error_message(val if isinstance(val, Exception) else Exception(str(val)), {"node": self.name}, orig)
                    self.emit(self._out, err)
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    # Swallow after logging via base policy
                    self._safe_call_user_function(original_message=orig)  # type: ignore[call-arg]
                else:
                    raise val  # type: ignore[misc]
            self._next_emit += 1
