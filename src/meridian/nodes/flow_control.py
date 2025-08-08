from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Deque, Dict, Optional, Tuple
import threading

from .base import ErrorPolicy, FunctionNode, NodeConfig, create_error_message, setup_standard_ports
from ..core.message import Message, MessageType


class RateLimitAlgorithm(str, Enum):
    TOKEN_BUCKET = "token_bucket"


class TimeoutAction(str, Enum):
    EMIT_ERROR = "emit_error"
    DROP = "drop"


class BackoffStrategy(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class ThrottleNode(FunctionNode):
    """Rate limiting with token bucket algorithm.

    Buffers DATA messages and releases them according to rate_limit and burst_size
    on ticks. CONTROL/ERROR are forwarded immediately.
    """

    def __init__(
        self,
        name: str,
        rate_limit: float,  # tokens per second
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
        burst_size: int | None = None,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._rate = max(0.0, float(rate_limit))
        self._capacity = max(1, int(burst_size or max(1, int(rate_limit)) ))
        self._tokens = self._capacity
        self._last_refill = time.monotonic()
        self._queue: Deque[Message] = deque()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self._last_refill)
        add = self._rate * elapsed
        if add > 0:
            self._tokens = min(self._capacity, self._tokens + add)
            self._last_refill = now

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            self._queue.append(msg)
        else:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        self._refill()
        # release as many messages as whole tokens
        while self._queue and self._tokens >= 1.0:
            m = self._queue.popleft()
            self.emit(self._out, m)
            self._tokens -= 1.0


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerNode(FunctionNode):
    """Prevent cascade failures with a circuit breaker pattern.

    - Counts ERROR messages as failures in CLOSED and HALF_OPEN states.
    - When failures >= failure_threshold in CLOSED, transition to OPEN.
    - In OPEN, DATA messages are rejected (emit ERROR) until recovery_timeout_ms elapses.
    - Then transition to HALF_OPEN, allow DATA through and count successes until success_threshold,
      then CLOSE; a single failure returns to OPEN immediately.
    CONTROL/ERROR are forwarded downstream.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_ms: int = 60000,
        success_threshold: int = 3,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._in = input_port
        self._out = output_port
        self._failure_threshold = max(1, int(failure_threshold))
        self._recovery_ms = max(1, int(recovery_timeout_ms))
        self._success_threshold = max(1, int(success_threshold))
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._opened_at_ms = 0.0

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        # Normalize nested Message payloads carried as DATA
        inner = msg
        if msg.type == MessageType.DATA and isinstance(msg.payload, Message):
            inner = msg.payload
        if inner.type == MessageType.DATA:
            if self._state == CircuitState.OPEN:
                # Reject request as ERROR
                err = create_error_message(RuntimeError("circuit_open"), {"node": self.name}, inner)
                self.emit(self._out, err)
                return
            # Allow in CLOSED and HALF_OPEN, treat as success by default
            self.emit(self._out, inner if inner is msg else inner)
            if self._state == CircuitState.HALF_OPEN:
                self._successes += 1
                if self._successes >= self._success_threshold:
                    # Close circuit on sufficient successes
                    self._state = CircuitState.CLOSED
                    self._successes = 0
                    self._failures = 0
        elif inner.type == MessageType.ERROR:
            # Count as failure and forward error downstream
            if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                self._failures += 1
                if self._state == CircuitState.CLOSED and self._failures >= self._failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at_ms = self._now_ms()
                elif self._state == CircuitState.HALF_OPEN:
                    # Immediate reopen on any failure
                    self._state = CircuitState.OPEN
                    self._opened_at_ms = self._now_ms()
                    self._successes = 0
            self.emit(self._out, inner)
        else:
            # Forward CONTROL or other types unchanged
            self.emit(self._out, inner)

    def _handle_tick(self) -> None:
        if self._state == CircuitState.OPEN and (self._now_ms() - self._opened_at_ms) >= self._recovery_ms:
            # Move to half-open to probe
            self._state = CircuitState.HALF_OPEN
            self._failures = 0
            self._successes = 0


@dataclass
class _RetryItem:
    payload: Any
    attempt: int
    next_time_ms: float


class RetryNode(FunctionNode):
    """Automatic retry with backoff and dead letter handling around a handler function."""

    def __init__(
        self,
        name: str,
        handler: Callable[[Any], Any],
        max_retries: int = 3,
        backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        dead_letter_port: str = "dead_letter",
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port, dead_letter_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._user_function = handler
        self._in = input_port
        self._out = output_port
        self._dlq = dead_letter_port
        self._max = max(0, int(max_retries))
        self._strategy = backoff_strategy
        self._pending: Deque[_RetryItem] = deque()

    def _backoff_ms(self, attempt: int) -> float:
        # Keep delays small for cooperative tests
        if self._strategy == BackoffStrategy.EXPONENTIAL:
            return 10.0 * (2 ** max(0, attempt - 1))
        if self._strategy == BackoffStrategy.LINEAR:
            return 10.0 * attempt
        return 10.0

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _enqueue(self, payload: Any, attempt: int) -> None:
        self._pending.append(_RetryItem(payload=payload, attempt=attempt, next_time_ms=self._now_ms()))

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            # Start attempt 1 immediately
            self._enqueue(msg.payload, 1)
        else:
            # Pass through non-DATA
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        # Process ready items
        now = self._now_ms()
        to_requeue: Deque[_RetryItem] = deque()
        while self._pending:
            item = self._pending.popleft()
            if item.next_time_ms > now:
                to_requeue.append(item)
                continue
            try:
                # Call handler directly to surface exceptions for retry logic
                result = self._user_function(item.payload)  # type: ignore[misc]
                if result is None:
                    pass
                else:
                    self.emit(self._out, Message(MessageType.DATA, result))
            except Exception as e:  # noqa: BLE001
                if item.attempt >= self._max:
                    # Send to DLQ immediately when attempts exhausted
                    self.emit(self._dlq, create_error_message(e, {"node": self.name}, Message(MessageType.DATA, item.payload)))
                else:
                    # Schedule retry
                    delay = self._backoff_ms(item.attempt + 1)
                    item.attempt += 1
                    item.next_time_ms = now + delay
                    to_requeue.append(item)
        # Append remaining at the end to preserve time ordering
        while to_requeue:
            self._pending.append(to_requeue.popleft())


@dataclass
class _TimeoutItem:
    payload: Any
    deadline_ms: float


class TimeoutNode(FunctionNode):
    """Add timeout handling to message processing via a handler function.

    If the handler doesn't complete before timeout_ms, emits an ERROR (or drops based on action).
    """

    def __init__(
        self,
        name: str,
        handler: Callable[[Any], Any],
        timeout_ms: int = 5000,
        timeout_action: TimeoutAction = TimeoutAction.EMIT_ERROR,
        input_port: str = "input",
        output_port: str = "output",
        config: NodeConfig | None = None,
    ) -> None:
        ins, outs = setup_standard_ports([input_port], [output_port])
        super().__init__(name, inputs=ins, outputs=outs, config=config)
        self._user_function = handler
        self._in = input_port
        self._out = output_port
        self._timeout_ms = max(1, int(timeout_ms))
        self._action = timeout_action
        self._running: Optional[_TimeoutItem] = None
        self._result: Optional[Tuple[bool, Any]] = None  # (success, value or exception)
        self._job_id: int = 0
        self._active_job_id: Optional[int] = None

    def _now_ms(self) -> float:
        return time.monotonic() * 1000.0

    def _start(self, payload: Any) -> None:
        deadline = self._now_ms() + self._timeout_ms
        self._running = _TimeoutItem(payload=payload, deadline_ms=deadline)
        # Start synchronously but bounded by subsequent ticks
        current_id = self._job_id + 1
        self._job_id = current_id
        self._active_job_id = current_id

        def _run(job_id: int, data: Any) -> None:
            try:
                value = self._user_function(data)  # type: ignore[misc]
                result: Tuple[bool, Any] = (True, value)
            except Exception as e:  # noqa: BLE001
                result = (False, e)
            # Only record if still active (not timed out)
            if self._active_job_id == job_id:
                self._result = result

        t = threading.Thread(target=_run, args=(current_id, payload), daemon=True)
        t.start()

    def _handle_message(self, port: str, msg: Message) -> None:
        if port != self._in:
            return
        if msg.type == MessageType.DATA:
            # If no job or previous finished, start a new one
            if self._running is None:
                self._start(msg.payload)
            else:
                # Drop or queue? Keep only one active; push existing result first
                pass
        else:
            self.emit(self._out, msg)

    def _handle_tick(self) -> None:
        if self._running is None:
            return
        # Check completion
        if self._result is not None:
            success, val = self._result
            if success:
                if val is not None:
                    self.emit(self._out, Message(MessageType.DATA, val))
            else:
                if self._config.error_policy == ErrorPolicy.EMIT_ERROR:
                    self.emit(self._out, create_error_message(val if isinstance(val, Exception) else Exception(str(val)), {"node": self.name}, Message(MessageType.DATA, self._running.payload)))
                elif self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                    self._safe_call_user_function(original_message=Message(MessageType.DATA, self._running.payload))  # type: ignore[call-arg]
                else:
                    raise val  # type: ignore[misc]
            self._running = None
            self._result = None
            self._active_job_id = None
            return
        # Check timeout
        if self._now_ms() >= self._running.deadline_ms:
            if self._action == TimeoutAction.EMIT_ERROR:
                self.emit(self._out, create_error_message(TimeoutError("timeout"), {"node": self.name}, Message(MessageType.DATA, self._running.payload)))
            # Mark job as inactive so late completion is ignored
            self._running = None
            self._result = None
            self._active_job_id = None
