from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..observability.logging import get_logger, with_context
from ..observability.metrics import get_metrics, time_block
from ..observability.tracing import get_trace_id, set_trace_id, start_span
from .message import Message, MessageType
from .ports import Port, PortDirection, PortSpec

if TYPE_CHECKING:
    from .scheduler import Scheduler


@dataclass(slots=True)
class Node:
    name: str
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    _metrics = field(default_factory=lambda: get_metrics(), init=False, repr=False)
    _scheduler: Scheduler | None = field(default=None, init=False, repr=False)
    _messages_total = None
    _errors_total = None
    _tick_duration = None

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
        ins = [Port(n, PortDirection.INPUT, spec=PortSpec(n)) for n in input_names]
        outs = [Port(n, PortDirection.OUTPUT, spec=PortSpec(n)) for n in output_names]
        return cls(name=name, inputs=ins, outputs=outs)

    def port_map(self) -> dict[str, Port]:
        m: dict[str, Port] = {p.name: p for p in self.inputs + self.outputs}
        return m

    def on_start(self) -> None:
        """Node startup hook."""
        logger = get_logger()
        with with_context(node=self.name):
            logger.info("node.start", f"Node {self.name} starting")
        return None

    def on_message(self, port: str, msg: Message) -> None:
        """Node message processing hook."""
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
                    
                    logger.debug("node.message_processed", 
                               f"Message processed in {duration:.6f}s", 
                               duration=duration)
                    
                except Exception as e:
                    # Record error metrics and log
                    if self._errors_total:
                        self._errors_total.inc(1)
                    
                    logger.error("node.message_error", 
                               f"Error processing message: {e}",
                               error_type=type(e).__name__,
                               error_msg=str(e))
                    
                    # Re-raise to let scheduler handle according to error policy
                    raise

    def _handle_message(self, port: str, msg: Message) -> None:
        """Override this method in subclasses for actual message processing."""
        return None

    def on_tick(self) -> None:
        """Node tick processing hook."""
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
                    
                    logger.error("node.tick_error", 
                               f"Error processing tick: {e}",
                               error_type=type(e).__name__,
                               error_msg=str(e))
                    
                    # Re-raise to let scheduler handle according to error policy
                    raise

    def _handle_tick(self) -> None:
        """Override this method in subclasses for actual tick processing."""
        return None

    def on_stop(self) -> None:
        """Node shutdown hook."""
        logger = get_logger()
        with with_context(node=self.name):
            logger.info("node.stop", f"Node {self.name} stopping")
        return None

    def emit(self, port: str, msg: Message) -> Message:
        """Emit a message through an output port."""
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
            logger.debug("node.emit", f"Emitting {msg.type.value} message", 
                        message_type=msg.type.value)
        
        # If connected to scheduler, use backpressure-aware emission
        if self._scheduler is not None:
            self._scheduler._handle_node_emit(self, port, msg)
        
        return msg

    def _set_scheduler(self, scheduler: Scheduler) -> None:
        """Internal method used by scheduler to register itself."""
        self._scheduler = scheduler
