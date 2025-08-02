"""Graph validation utilities."""

from __future__ import annotations

# Import core types - will need to check these exist
from typing import TYPE_CHECKING, Any as _Any, TypeAlias

from .issue import Issue

if TYPE_CHECKING:
    from meridian.core.subgraph import Subgraph as _Subgraph
else:
    _Subgraph = _Any  # type: ignore[assignment]

Subgraph: TypeAlias = _Subgraph


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
