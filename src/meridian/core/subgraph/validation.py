from __future__ import annotations

from .construction import Subgraph, ValidationIssue


def validate(g: Subgraph) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if len(g.nodes) != len(set(g.nodes.keys())):
        issues.append(ValidationIssue("error", "DUP_NODE", "duplicate node names"))
    seen_edge_ids: set[str] = set()
    for e in g.edges:
        if e.source_node not in g.nodes or e.target_node not in g.nodes:
            issues.append(ValidationIssue("error", "UNKNOWN_NODE", "edge references unknown node"))
            if e.capacity <= 0:
                issues.append(ValidationIssue("error", "BAD_CAP", "edge capacity must be > 0"))
            continue
        src = g.nodes[e.source_node]
        dst = g.nodes[e.target_node]
        if all(p.name != e.source_port.name for p in src.outputs):
            issues.append(ValidationIssue("error", "NO_SRC_PORT", "src node missing output port"))
        if all(p.name != e.target_port.name for p in dst.inputs):
            issues.append(ValidationIssue("error", "NO_DST_PORT", "dst node missing input port"))
        if e.capacity <= 0:
            issues.append(ValidationIssue("error", "BAD_CAP", "edge capacity must be > 0"))
        if e.spec is not None and e.target_port.spec is not None:
            if e.target_port.spec.schema is not None:
                sch = e.target_port.spec.schema
                _ = sch
        edge_id = f"{e.source_node}:{e.source_port.name}->{e.target_node}:{e.target_port.name}"
        if edge_id in seen_edge_ids:
            issues.append(ValidationIssue("error", "DUP_EDGE", "duplicate edge identifier"))
        seen_edge_ids.add(edge_id)
    if len(g.exposed_inputs) != len(set(g.exposed_inputs.keys())):
        issues.append(ValidationIssue("error", "DUP_EXPOSE_IN", "duplicate exposed input names"))
    if len(g.exposed_outputs) != len(set(g.exposed_outputs.keys())):
        issues.append(ValidationIssue("error", "DUP_EXPOSE_OUT", "duplicate exposed output names"))
    for _, (n, p) in g.exposed_inputs.items():
        if n not in g.nodes or all(port.name != p for port in g.nodes[n].inputs):
            issues.append(ValidationIssue("error", "BAD_EXPOSE_IN", "exposed input references unknown target"))
    for _, (n, p) in g.exposed_outputs.items():
        if n not in g.nodes or all(port.name != p for port in g.nodes[n].outputs):
            issues.append(ValidationIssue("error", "BAD_EXPOSE_OUT", "exposed output references unknown source"))
    return issues
