from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
import time
from typing import TYPE_CHECKING, Any

from ..observability.logging import get_logger, with_context
from ..observability.metrics import get_metrics, time_block
from ..observability.tracing import get_trace_id, set_trace_id, start_span
from .message import Message, MessageType
from .ports import Port, PortDirection, PortSpec

if TYPE_CHECKING:
    from .scheduler import Scheduler


@dataclass(slots=True)
class Node:
    """
    Base processing unit in a graph.

    A Node consumes messages on its input ports and may emit messages on its output
    ports. Subclasses implement the behavior by overriding `_handle_message` and/or
    `_handle_tick`.

    Lifecycle hooks:
      - on_start(): called once when the scheduler starts the node
      - on_message(port, msg): called by the scheduler when a message arrives
      - on_tick(): called by the scheduler periodically or when scheduled
      - on_stop(): called once when the scheduler stops the node

    Observability:
      - Emits structured logs for start/stop, message/tick processing.
      - Increments counters for processed messages and errors.
      - Records tick duration in a histogram.
      - Propagates and uses trace IDs from incoming messages when present.

    Backpressure:
      - Emissions via `emit()` respect the scheduler’s backpressure strategy
        when the node is registered with a scheduler.

    Threading:
      - Nodes are expected to be used within the scheduler’s event loop. Avoid
        blocking operations; offload I/O if needed.

    """

    name: str
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    _metrics: Any = field(default_factory=lambda: get_metrics(), init=False, repr=False)
    _scheduler: Scheduler | None = field(default=None, init=False, repr=False)
    _messages_total: Any = None
    _errors_total: Any = None
    _tick_duration: Any = None

    def __post_init__(self) -> None:
        """Initialize metrics after construction."""
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize metric handles with proper labels."""
        node_labels = {"node": self.name}

        self._messages_total = self._metrics.counter("node_messages_total", node_labels)
        self._errors_total = self._metrics.counter("node_errors_total", node_labels)
        self._tick_duration = self._metrics.histogram("node_tick_duration_seconds", node_labels)

    @classmethod
    def with_ports(cls, name: str, input_names: Iterable[str], output_names: Iterable[str]) -> Node:
        """
        Construct a Node with simple named input/output ports.

        Parameters:
          name: Unique node name (used for logging/metrics labels).
          input_names: Iterable of input port names.
          output_names: Iterable of output port names.

        Returns:
          A Node instance with the requested ports.

        Notes:
          - Ports are created with default PortSpec using the port name as the spec id.
          - For richer port specs, construct the node with explicit Port objects.
        """
        ins = [Port(n, PortDirection.INPUT, spec=PortSpec(n)) for n in input_names]
        outs = [Port(n, PortDirection.OUTPUT, spec=PortSpec(n)) for n in output_names]
        return cls(name=name, inputs=ins, outputs=outs)

    def port_map(self) -> dict[str, Port]:
        """
        Return a mapping of port name to Port for all inputs and outputs.

        Returns:
          Dictionary keyed by port name with the corresponding Port instances.
        """
        m: dict[str, Port] = {p.name: p for p in self.inputs + self.outputs}
        return m

    def on_start(self) -> None:
        """
        Startup hook executed once when the scheduler starts this node.

        Side effects:
          - Logs a node.start event.
          - Initializes observability context for subsequent operations.
        """
        logger = get_logger()
        with with_context(node=self.name):
            logger.info("node.start", f"Node {self.name} starting")
        return None

    def on_message(self, port: str, msg: Message) -> None:
        """
        Message processing hook invoked by the scheduler.

        Parameters:
          port: Name of the input port that received the message.
          msg: The incoming Message instance.

        Behavior:
          - Propagates trace id from the message, if present.
          - Creates a tracing span and emits structured logs.
          - Times processing duration and increments message counters.
          - Exceptions are logged, error counter is incremented, then the exception is re-raised
            for the scheduler to handle per its error policy.

        Subclassing:
          - Override `_handle_message(port, msg)` to implement processing logic.
        """
        logger = get_logger()

        # Set trace context from message
        trace_id = msg.get_trace_id()
        if trace_id:
            set_trace_id(trace_id)

        # Create span for message processing
        with start_span("node.on_message", {"node": self.name, "port": port, "trace_id": trace_id}):
            with with_context(node=self.name, port=port, trace_id=trace_id):
                try:
                    # Time the message processing
                    start_time = time.perf_counter()

                    # Call the actual implementation (subclasses should override)
                    self._handle_message(port, msg)

                    # Record success metrics
                    duration = time.perf_counter() - start_time
                    if self._messages_total:
                        self._messages_total.inc(1)

                    logger.debug(
                        "node.message_processed",
                        f"Message processed in {duration:.6f}s",
                        duration=duration,
                    )

                except Exception as e:
                    # Record error metrics and log
                    if self._errors_total:
                        self._errors_total.inc(1)

                    logger.error(
                        "node.message_error",
                        f"Error processing message: {e}",
                        error_type=type(e).__name__,
                        error_msg=str(e),
                    )

                    # Re-raise to let scheduler handle according to error policy
                    raise

    def _handle_message(self, port: str, msg: Message) -> None:
        """
        Subclass hook with the actual message processing logic.

        Contract:
          - Must not block the event loop; offload I/O if needed.
          - May call `emit()` to publish messages on output ports.
          - Raise exceptions to signal processing failure; the scheduler will apply its policy.
        """
        return None

    def on_tick(self) -> None:
        """
        Periodic processing hook invoked by the scheduler.

        Behavior:
          - Records tick duration in a histogram.
          - Logs success or error events.
          - Exceptions are re-raised for the scheduler to handle.

        Subclassing:
          - Override `_handle_tick()` to implement periodic work (e.g., timers, maintenance).
        """
        logger = get_logger()

        with start_span("node.on_tick", {"node": self.name}):
            with with_context(node=self.name):
                try:
                    # Time the tick processing
                    with time_block("node_tick_duration_seconds", {"node": self.name}):
                        # Call the actual implementation (subclasses should override)
                        self._handle_tick()

                    logger.debug("node.tick_processed", "Tick processed successfully")

                except Exception as e:
                    # Record error metrics and log
                    if self._errors_total:
                        self._errors_total.inc(1)

                    logger.error(
                        "node.tick_error",
                        f"Error processing tick: {e}",
                        error_type=type(e).__name__,
                        error_msg=str(e),
                    )

                    # Re-raise to let scheduler handle according to error policy
                    raise

    def _handle_tick(self) -> None:
        """
        Subclass hook with the actual periodic/timer processing logic.

        Contract:
          - Keep work brief to avoid starving message processing.
          - Raise exceptions to indicate failure; the scheduler will apply its policy.
        """
        return None

    def on_stop(self) -> None:
        """
        Shutdown hook executed once when the scheduler stops this node.

        Side effects:
          - Logs a node.stop event.
        """
        logger = get_logger()
        with with_context(node=self.name):
            logger.info("node.stop", f"Node {self.name} stopping")
        return None

    def emit(self, port: str, msg: Message) -> Message:
        """
        Emit a message through an output port.

        Parameters:
          port: Output port name to emit on.
          msg: Message to emit. Must be of type DATA, CONTROL, or ERROR.

        Returns:
          The message (potentially augmented with a propagated trace id).

        Raises:
          KeyError: If the output port name is unknown.
          ValueError: If the message type is invalid.

        Side effects:
          - Logs an emit event with context.
          - Propagates current trace id if the message lacks one.
          - If attached to a scheduler, delegates to a backpressure-aware path.

        Notes:
          - Emission may be mediated by the scheduler; avoid unbounded production.
        """
        logger = get_logger()

        # Validate message type
        if msg.type not in (MessageType.DATA, MessageType.CONTROL, MessageType.ERROR):
            raise ValueError("invalid message type")

        # Validate port exists
        if port not in {p.name for p in self.outputs}:
            raise KeyError(f"unknown output port: {port}")

        # Ensure trace ID propagation
        current_trace_id = get_trace_id()
        if current_trace_id and not msg.get_trace_id():
            msg = msg.with_headers(trace_id=current_trace_id)

        with with_context(node=self.name, port=port, trace_id=msg.get_trace_id()):
            logger.debug(
                "node.emit", f"Emitting {msg.type.value} message", message_type=msg.type.value
            )

        # If connected to scheduler, use backpressure-aware emission
        if self._scheduler is not None:
            self._scheduler._handle_node_emit(self, port, msg)

        return msg

    def _set_scheduler(self, scheduler: Scheduler) -> None:
        """
        Internal: Register the scheduler instance with this node.

        Parameters:
          scheduler: The Scheduler that manages this node’s lifecycle.

        Notes:
          - Used by the runtime; not intended for application code.
        """
        self._scheduler = scheduler
