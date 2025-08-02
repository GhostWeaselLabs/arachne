from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class PortDirection(str, Enum):
    """
    Direction of a port in a node.

    INPUT:
      Receives messages from upstream edges for processing by the node.

    OUTPUT:
      Emits messages produced by the node to downstream edges.
    """

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class SchemaValidator(Protocol):
    """Callable protocol for validating a value against a schema."""

    def __call__(self, value: Any) -> bool: ...


@dataclass(frozen=True, slots=True)
class PortSpec:
    """
    Specification for values flowing through a Port.

    Attributes:
      name:
        Logical identifier of the port/spec (typically matches the port name).
      schema:
        Optional Python type or tuple of types accepted by this port’s payloads.
        If None, any type is accepted by this spec.
      policy:
        Optional policy hint used by runtime/router layers (e.g., backpressure/routing).
        Interpretation is runtime-specific.

    Validation:
      - validate(value) returns True if:
        * schema is None, or
        * value is an instance of schema (or any of the types if a tuple was provided)

    Notes:
      - PortSpec validation is a lightweight type check and does not perform deep schema
        validation. For richer validation, adapt at the application boundary.
    """

    name: str
    schema: type[Any] | tuple[type[Any], ...] | None = None
    policy: str | None = None

    def validate(self, value: Any) -> bool:
        """Return True if value conforms to the configured schema (if any)."""
        if self.schema is None:
            return True
        if isinstance(self.schema, tuple):
            return isinstance(value, self.schema)
        return isinstance(value, self.schema)


@dataclass(frozen=True, slots=True)
class Port:
    """
    Connection point on a node for receiving or emitting messages.

    Attributes:
      name:
        Unique port name within the node.
      direction:
        INPUT or OUTPUT; determines whether the port receives or emits.
      index:
        Optional positional index; useful for stable ordering when needed.
      spec:
        Optional PortSpec describing expected payload types or policy hints.

    Semantics:
      - For INPUT ports, the scheduler delivers messages to the node’s handler.
      - For OUTPUT ports, nodes call emit() via the runtime to publish messages.
      - When provided, spec.validate(value) can be used to guard payload types.

    """

    name: str
    direction: PortDirection
    index: int | None = None
    spec: PortSpec | None = None

    def is_input(self) -> bool:
        """Return True if this is an INPUT port."""
        return self.direction == PortDirection.INPUT

    def is_output(self) -> bool:
        """Return True if this is an OUTPUT port."""
        return self.direction == PortDirection.OUTPUT
