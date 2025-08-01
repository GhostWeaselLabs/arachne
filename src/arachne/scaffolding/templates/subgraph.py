"""Subgraph template generator."""

from __future__ import annotations

from ..parsers.ports import snake_case


def generate_subgraph_template(class_name: str) -> str:
    """Generate subgraph class template."""

    template = f'''"""Generated {class_name} subgraph.

Purpose: TODO - Describe what this subgraph does
Composition: TODO - Document the nodes and their connections
Exposed Ports: TODO - Document input/output port behavior
"""

from __future__ import annotations

from typing import Any

from arachne.core.subgraph import Subgraph
from arachne.core.scheduler import Scheduler, SchedulerConfig
from arachne.core.ports import PortSpec
# TODO: Import your node classes here
# from arachne.nodes.your_node import YourNode


class {class_name}(Subgraph):
    """TODO: Brief description of {class_name} functionality."""
    
    def __init__(self, name: str = "{snake_case(class_name)}") -> None:
        """Initialize the subgraph."""
        super().__init__(name=name)
        self._setup_nodes()
        self._setup_wiring()
        self._setup_exposed_ports()
    
    def _setup_nodes(self) -> None:
        """Create and add nodes to the subgraph."""
        # TODO: Create your nodes here
        # Example:
        # self.processor = YourNode("processor")
        # self.add_node(self.processor)
        pass
    
    def _setup_wiring(self) -> None:
        """Wire nodes together."""
        # TODO: Connect your nodes here
        # Example:
        # self.connect(("input_node", "output_port"), ("target_node", "input_port"))
        pass
    
    def _setup_exposed_ports(self) -> None:
        """Expose internal ports as subgraph ports."""
        # TODO: Expose ports to make them available externally
        # Example:
        # self.expose_input("external_input", "internal_node", "internal_input")
        # self.expose_output("external_output", "internal_node", "internal_output")
        pass
'''

    return template


def generate_subgraph_test_template(class_name: str) -> str:
    """Generate test template for subgraph."""

    test_class = f"Test{class_name}"

    template = f'''"""Tests for {class_name} subgraph."""

import pytest

from {snake_case(class_name)} import {class_name}
from arachne.core.scheduler import Scheduler, SchedulerConfig


class {test_class}:
    """Test cases for {class_name}."""
    
    @pytest.fixture
    def subgraph(self):
        """Create a {class_name} instance for testing."""
        return {class_name}()
    
    def test_init(self, subgraph):
        """Test subgraph initialization."""
        assert subgraph.name == "{snake_case(class_name)}"
        # TODO: Add assertions for nodes, connections, and exposed ports
    
    def test_node_composition(self, subgraph):
        """Test that nodes are properly added."""
        # TODO: Verify that expected nodes are present
        # Example: assert "processor" in subgraph.node_names()
        # Minimal scheduler placeholder
        _ = Scheduler(SchedulerConfig())
        pass
    
    def test_wiring(self, subgraph):
        """Test that nodes are properly connected."""
        # TODO: Verify connections between nodes
        pass
    
    def test_exposed_ports(self, subgraph):
        """Test that ports are properly exposed."""
        # TODO: Verify that expected ports are exposed
        # Example: assert "input_port" in subgraph.inputs
        # Example: assert "output_port" in subgraph.outputs
        pass
'''

    return template
