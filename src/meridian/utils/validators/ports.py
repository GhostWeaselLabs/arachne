"""Port validation utilities."""

from __future__ import annotations

# Import core types - will need to check these exist
from typing import TYPE_CHECKING, Any, Any as _Any, TypeAlias

from .issue import Issue

if TYPE_CHECKING:
    from meridian.core.node import Node as _Node
else:
    _Node = _Any  # type: ignore[assignment]

Node: TypeAlias = _Node


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
