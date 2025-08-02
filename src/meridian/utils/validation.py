"""Validation utilities for Arachne graphs and components.

Provides validation helpers for ports, schemas, and graph wiring with
optional Pydantic adapter support.

Scope:
- Light structural checks for nodes, ports, and subgraph wiring.
- Optional schema validation via adapters (e.g., Pydantic) when available.

Notes:
- Prefer core runtime validations at enqueue time for payload/schema checks.
- These utilities aim to surface common configuration issues early, not to
  enforce deep schema semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

# Import core types with TYPE_CHECKING to avoid import cycles at runtime.
from typing import TYPE_CHECKING, Any, Any as _Any, Protocol, TypeAlias, runtime_checkable

if TYPE_CHECKING:
    from meridian.core.node import Node as _Node
    from meridian.core.ports import PortSpec as _PortSpec
    from meridian.core.subgraph import Subgraph as _Subgraph
else:
    _Node = _Any  # type: ignore[assignment]
    _PortSpec = _Any  # type: ignore[assignment]
    _Subgraph = _Any  # type: ignore[assignment]

Node: TypeAlias = _Node
PortSpec: TypeAlias = _PortSpec
Subgraph: TypeAlias = _Subgraph


@dataclass
class Issue:
    """Validation issue with severity and location context.

    Attributes:
        severity: "error" or "warning" to indicate impact.
        message: Human-readable description of the issue.
        location: Identifier where the issue was found (e.g., "node:Name",
                  "node:Name:input:port", "graph:Subgraph:edge").
    """

    severity: str  # "error" | "warning"
    message: str
    location: str | tuple[str, ...]  # node, port, edge identifier

    def is_error(self) -> bool:
        """Return True if this is an error-level issue."""
        return self.severity == "error"

    def is_warning(self) -> bool:
        """Return True if this is a warning-level issue."""
        return self.severity == "warning"


@runtime_checkable
class SchemaValidator(Protocol):
    """Protocol for optional schema validation adapters."""

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against a schema/model.

        Parameters:
            model: Schema model (e.g., a Pydantic BaseModel subclass).
            payload: Data to validate.

        Returns:
            Issue if validation fails, None when payload is valid.
        """
        ...


def validate_ports(node: Node) -> list[Issue]:
    """Validate that a node's declared ports are properly typed.

    Parameters:
        node: Node instance to validate.

    Returns:
        list[Issue]: Validation issues found (empty when none).

    Notes:
        - This utility targets nodes that expose callable inputs()/outputs()
          returning dicts of {port_name -> spec}. It does not enforce deep
          schema semantics—only basic structural checks.
    """
    issues: list[Issue] = []

    try:
        # Check if node has proper port declarations
        if hasattr(node, "inputs") and callable(node.inputs):
            inputs = node.inputs()
            if not isinstance(inputs, dict):
                issues.append(
                    Issue(
                        severity="error",
                        message="Node inputs() must return a dict",
                        location=f"node:{node.__class__.__name__}",
                    )
                )
            else:
                for port_name, _port_spec in inputs.items():
                    if not isinstance(port_name, str):
                        issues.append(
                            Issue(
                                severity="error",
                                message=f"Port name must be string, got {type(port_name)}",
                                location=f"node:{node.__class__.__name__}:input:{port_name}",
                            )
                        )
                    # Note: deeper schema checks should be delegated to runtime enqueue
                    # validation or explicit schema adapters.

        if hasattr(node, "outputs") and callable(node.outputs):
            outputs = node.outputs()
            if not isinstance(outputs, dict):
                issues.append(
                    Issue(
                        severity="error",
                        message="Node outputs() must return a dict",
                        location=f"node:{node.__class__.__name__}",
                    )
                )
            else:
                for port_name, _port_spec in outputs.items():
                    if not isinstance(port_name, str):
                        issues.append(
                            Issue(
                                severity="error",
                                message=f"Port name must be string, got {type(port_name)}",
                                location=f"node:{node.__class__.__name__}:output:{port_name}",
                            )
                        )
                    # Note: deeper schema checks should be delegated to runtime enqueue
                    # validation or explicit schema adapters.

    except Exception as e:
        issues.append(
            Issue(
                severity="error",
                message=f"Failed to validate ports: {e}",
                location=f"node:{node.__class__.__name__}",
            )
        )

    return issues


def validate_connection(src_spec: Any, dst_spec: Any) -> Issue | None:
    """Validate schema compatibility between connected ports (shallow check).

    Parameters:
        src_spec: Source port specification.
        dst_spec: Destination port specification.

    Returns:
        Issue if incompatible, None if compatible.

    Notes:
        - This is intentionally shallow and only guards against missing specs.
        - Deep schema compatibility should be enforced by runtime enqueue validation
          or explicit schema adapters (e.g., Pydantic).
    """
    if src_spec is None or dst_spec is None:
        return Issue(
            severity="error", message="Port specifications cannot be None", location="connection"
        )
    return None


def validate_graph(subgraph: Subgraph) -> list[Issue]:
    """Validate subgraph wiring and configuration (shallow checks).

    Parameters:
        subgraph: Subgraph instance to validate.

    Returns:
        list[Issue]: Validation issues found (empty when none).

    Checks:
        - Duplicate node names (if accessible via _nodes).
        - Edge capacities must be positive integers (if accessible via _edges).
        - Exposed input/output names should be non-empty strings (if accessible).
    """
    issues: list[Issue] = []

    try:
        # Check for unique node names
        node_names = set()
        if hasattr(subgraph, "_nodes"):
            for node in subgraph._nodes:
                name = getattr(node, "name", str(node.__class__.__name__))
                if name in node_names:
                    issues.append(
                        Issue(
                            severity="error",
                            message=f"Duplicate node name: {name}",
                            location=f"graph:{subgraph.__class__.__name__}:node:{name}",
                        )
                    )
                node_names.add(name)

        # Check edge capacities if accessible
        if hasattr(subgraph, "_edges"):
            for edge in subgraph._edges:
                if hasattr(edge, "capacity"):
                    capacity = edge.capacity
                    if not isinstance(capacity, int) or capacity <= 0:
                        issues.append(
                            Issue(
                                severity="error",
                                message=f"Edge capacity must be positive integer, got {capacity}",
                                location=f"graph:{subgraph.__class__.__name__}:edge",
                            )
                        )

        # Check for dangling exposed ports
        if hasattr(subgraph, "_exposed_inputs"):
            for port_name in subgraph._exposed_inputs:
                if not isinstance(port_name, str) or not port_name.strip():
                    issues.append(
                        Issue(
                            severity="warning",
                            message=f"Exposed input port has invalid name: {port_name}",
                            location=f"graph:{subgraph.__class__.__name__}:input:{port_name}",
                        )
                    )

        if hasattr(subgraph, "_exposed_outputs"):
            for port_name in subgraph._exposed_outputs:
                if not isinstance(port_name, str) or not port_name.strip():
                    issues.append(
                        Issue(
                            severity="warning",
                            message=f"Exposed output port has invalid name: {port_name}",
                            location=f"graph:{subgraph.__class__.__name__}:output:{port_name}",
                        )
                    )

    except Exception as e:
        issues.append(
            Issue(
                severity="error",
                message=f"Failed to validate graph: {e}",
                location=f"graph:{subgraph.__class__.__name__}",
            )
        )

    return issues


class PydanticAdapter:
    """Optional Pydantic adapter for schema validation.

    Only available if Pydantic is installed.
    """

    def __init__(self) -> None:
        try:
            import pydantic  # type: ignore[import-not-found]

            self._pydantic = pydantic
        except Exception:
            self._pydantic = None

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against a Pydantic model.

        Parameters:
            model: Pydantic model class (BaseModel subclass).
            payload: Data to validate.

        Returns:
            Issue if validation fails, None when valid.

        Behavior:
            - If Pydantic is not available, return a warning-level Issue.
            - Uses model.model_validate(payload) to check compatibility.
        """
        if self._pydantic is None:
            return Issue(
                severity="warning",
                message="Pydantic not available for schema validation",
                location="adapter:pydantic",
            )

        try:
            # Attempt validation
            model.model_validate(payload)
            return None
        except Exception as e:
            return Issue(
                severity="error",
                message=f"Schema validation failed: {e}",
                location=f"schema:{model.__name__}",
            )
