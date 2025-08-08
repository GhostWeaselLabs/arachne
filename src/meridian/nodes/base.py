from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable

from ..core.message import Message, MessageType
from ..core.node import Node
from ..core.ports import Port, PortDirection, PortSpec
from ..observability.logging import get_logger


class ErrorPolicy(str, Enum):
    LOG_AND_CONTINUE = "log_continue"
    EMIT_ERROR = "emit_error"
    RAISE_EXCEPTION = "raise"


class MergeStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    TIMESTAMP = "timestamp"


class DistributionStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    HASH_BASED = "hash"
    LOAD_BASED = "load"


@dataclass(slots=True)
class NodeConfig:
    error_policy: ErrorPolicy = ErrorPolicy.LOG_AND_CONTINUE
    enable_metrics: bool = True
    custom_labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TimingConfig:
    interval_ms: int = 100
    timeout_ms: int = 1000
    use_scheduler_ticks: bool = True


class FunctionNode(Node):
    """Base class for nodes that wrap user-provided functions.

    Provides helpers for safe function invocation and standard port setup.
    """

    def __init__(self, name: str, inputs: list[Port], outputs: list[Port], config: NodeConfig | None = None):
        super().__init__(name=name, inputs=inputs, outputs=outputs)
        self._config = config or NodeConfig()
        self._user_function: Callable[..., Any] | None = None

    def _safe_call_user_function(self, *args: Any, original_message: Message | None = None, **kwargs: Any) -> Any:
        logger = get_logger()
        try:
            if self._user_function is None:
                raise RuntimeError("user function not configured")
            return self._user_function(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            # Convert to ERROR according to policy
            if self._config.error_policy == ErrorPolicy.LOG_AND_CONTINUE:
                logger.error("function_node.error", f"Error in user function: {e}", error_type=type(e).__name__, error_msg=str(e))
                return None
            if self._config.error_policy == ErrorPolicy.EMIT_ERROR and original_message is not None:
                err = create_error_message(e, {"node": self.name}, original_message)
                # Choose first available output if present
                if self.outputs:
                    self.emit(self.outputs[0].name, err)
                return None
            # Default: raise
            raise


# Common utilities

def create_error_message(exception: Exception, context: dict[str, Any], original_message: Message | None = None) -> Message:
    """Create standardized error messages compatible with core.Message."""
    payload: dict[str, Any] = {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "context": context,
    }
    if original_message is not None:
        try:
            payload["original_payload"] = getattr(original_message, "payload", None)
        except Exception:  # noqa: BLE001
            payload["original_payload"] = None
    return Message(type=MessageType.ERROR, payload=payload, metadata={"error_source": "built_in_node"})


def validate_callable(func: Callable[..., Any] | None, expected_arity: int | None = None) -> None:
    """Runtime validation for callables.

    - If expected_arity is provided, ensure the callable accepts at least that many positional params.
    """
    if func is None:
        raise ValueError("callable cannot be None")
    import inspect

    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    if expected_arity is not None and len(params) < expected_arity:
        raise ValueError(f"callable arity {len(params)} < expected {expected_arity}")


def setup_standard_ports(input_names: Iterable[str] | None, output_names: Iterable[str] | None) -> tuple[list[Port], list[Port]]:
    ins = [Port(n, PortDirection.INPUT, spec=PortSpec(n)) for n in (input_names or [])]
    outs = [Port(n, PortDirection.OUTPUT, spec=PortSpec(n)) for n in (output_names or [])]
    return ins, outs
