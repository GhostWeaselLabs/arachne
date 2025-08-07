from __future__ import annotations

from .construction import Subgraph, ValidationIssue


def validate_subgraph_structure(g: Subgraph) -> list[ValidationIssue]:
    return g.validate()
