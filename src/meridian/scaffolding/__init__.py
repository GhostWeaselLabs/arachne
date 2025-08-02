"""Scaffolding utilities for generating Arachne nodes and subgraphs."""

from .generate_node import (
    create_node_files,
    generate_node_template,
    generate_node_test_template,
)
from .parsers.ports import parse_ports, snake_case

# Backward-compatibility alias for older tests
from .templates.node import generate_node_test_template as generate_test_template
from .templates.subgraph import (
    generate_subgraph_template,
    generate_subgraph_test_template,
)

__all__ = [
    "create_node_files",
    "generate_node_template",
    "generate_node_test_template",
    "generate_test_template",
    "parse_ports",
    "snake_case",
    "generate_subgraph_template",
    "generate_subgraph_test_template",
]
