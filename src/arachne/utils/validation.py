"""Validation utilities for Arachne graphs and components.

Provides validation helpers for ports, schemas, and graph wiring with
optional Pydantic adapter support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# Import core types - will need to check these exist
try:
    from arachne.core.node import Node
    from arachne.core.ports import PortSpec
    from arachne.core.subgraph import Subgraph
except ImportError:
    # Fallback for development/testing
    PortSpec = Any
    Node = Any
    Subgraph = Any


@dataclass
class Issue:
    """Validation issue with severity and location context."""

    severity: str  # "error" | "warning"
    message: str
    location: str | tuple[str, ...]  # node, port, edge identifier

    def is_error(self) -> bool:
        """Check if this is an error-level issue."""
        return self.severity == "error"

    def is_warning(self) -> bool:
        """Check if this is a warning-level issue."""
        return self.severity == "warning"


@runtime_checkable
class SchemaValidator(Protocol):
    """Protocol for optional schema validation adapters."""

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against model schema.

        Args:
            model: Schema model (e.g., Pydantic model)
            payload: Data to validate

        Returns:
            Issue if validation fails, None if valid
        """
        ...


def validate_ports(node: Node) -> list[Issue]:
    """Validate that node's declared ports are properly typed.

    Args:
        node: Node instance to validate

    Returns:
        List of validation issues found
    """
    issues = []

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
    """Validate schema compatibility between connected ports.

    Args:
        src_spec: Source port specification
        dst_spec: Destination port specification

    Returns:
        Issue if incompatible, None if compatible
    """
    # Basic type compatibility check
    # This is a simplified implementation - real validation would check
    # schema types, but we keep it minimal for M5

    if src_spec is None or dst_spec is None:
        return Issue(
            severity="error", message="Port specifications cannot be None", location="connection"
        )

    # For now, accept any non-None connections
    # More sophisticated schema checking would go here
    return None


def validate_graph(subgraph: Subgraph) -> list[Issue]:
    """Validate graph wiring and configuration.

    Args:
        subgraph: Subgraph to validate

    Returns:
        List of validation issues found
    """
    issues = []

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
            import pydantic

            self._pydantic = pydantic
        except ImportError:
            self._pydantic = None

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against Pydantic model.

        Args:
            model: Pydantic model class
            payload: Data to validate

        Returns:
            Issue if validation fails, None if valid
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
