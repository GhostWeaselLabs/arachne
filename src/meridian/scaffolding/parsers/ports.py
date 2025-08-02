"""Port parsing utilities for scaffolding."""

from __future__ import annotations


def parse_ports(port_str: str) -> dict[str, str]:
    """Parse port string like 'in:dict,out:int' into dict."""
    if not port_str.strip():
        return {}

    ports = {}
    # Handle complex types with nested brackets by being more careful about splitting
    port_defs = []
    current_def = ""
    bracket_depth = 0

    for char in port_str:
        if char in "[{(":
            bracket_depth += 1
        elif char in "]})":
            bracket_depth -= 1
        elif char == "," and bracket_depth == 0:
            port_defs.append(current_def.strip())
            current_def = ""
            continue
        current_def += char

    if current_def.strip():
        port_defs.append(current_def.strip())

    for port_def in port_defs:
        if ":" not in port_def:
            raise ValueError("Invalid port definition")
        port_name, port_type = port_def.split(":", 1)
        ports[port_name.strip()] = port_type.strip()

    return ports


def snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)
