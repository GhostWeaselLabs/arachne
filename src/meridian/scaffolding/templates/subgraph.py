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

from meridian.core.subgraph import Subgraph
# Placeholder imports for potential scheduler usage
from meridian.core.scheduler import Scheduler, SchedulerConfig
from meridian.core.ports import PortSpec
from meridian.utils.validation import validate_graph, Issue
# TODO: Import your node classes here
# from meridian-runtime.nodes.your_node import YourNode


class {class_name}(Subgraph):
    """TODO: Brief description of {class_name} functionality."""

    def __init__(self, name: str = "{snake_case(class_name)}") -> None:
        """Initialize the subgraph."""
        super().__init__(name=name)
        self._setup_nodes()
        self._setup_connections()
        self._setup_exposed_ports()

    def _setup_nodes(self) -> None:
        """Create and add nodes to the subgraph."""
        # TODO: Create your nodes here
        # Example:
        # self.processor = YourNode("processor")
        # self.add_node(self.processor)
        pass

    def _setup_connections(self) -> None:
        """Wire nodes together."""
        # TODO: Connect your nodes here
        # Example:
        # self.connect(("input_node", "output_port"), ("target_node", "input_port"))
        pass

    def validate_composition(self) -> None:
        """Validate graph composition using utility helpers."""
        issues = validate_graph(self)
        for issue in issues:
            if issue.is_error():
                raise ValueError(issue.message)
            if issue.is_warning():
                print(f"Warning: {{issue.message}}")

    def _setup_exposed_ports(self) -> None:
        """Expose internal ports as subgraph ports."""
        # TODO: Expose ports to make them available externally
        # Example:
        # self.expose_input("external_input", "internal_node", "internal_input")
        # self.expose_output("external_output", "internal_node", "internal_output")
        pass


if __name__ == "__main__":
    subgraph = {class_name}()
    subgraph.validate_composition()
'''

    return template


def generate_subgraph_test_template(class_name: str) -> str:
    """Generate test template for subgraph."""

    test_class = f"Test{class_name}"

    template = f'''"""Tests for {class_name} subgraph."""

import pytest

from {snake_case(class_name)} import {class_name}
from meridian.core.scheduler import Scheduler, SchedulerConfig


class {test_class}:
    """Test cases for {class_name}."""

    @pytest.fixture
    def subgraph(self):
        """Create a {class_name} instance for testing."""
        return {class_name}()

    def test_subgraph_creation(self, subgraph):
        """Basic creation test."""
        assert subgraph.name == "{snake_case(class_name)}"

    def test_subgraph_validation(self, subgraph):
        """Ensure validation method can run."""
        try:
            subgraph.validate_composition()
        except ValueError:
            # Expected if no nodes are added yet
            pass

    def test_node_composition(self, subgraph):
        """Test that nodes are properly added."""
        # TODO: Verify that expected nodes are present
        # Example: assert "processor" in subgraph.node_names()
        _ = Scheduler(SchedulerConfig())
        pass

    def test_edge_connections(self, subgraph):
        """Test that nodes are properly connected."""
        # TODO: Verify connections between nodes
        pass

    def test_port_exposure(self, subgraph):
        """Test that ports are properly exposed."""
        # TODO: Verify that expected ports are exposed
        # Example: assert "input_port" in subgraph.inputs
        # Example: assert "output_port" in subgraph.outputs
        pass

    # TODO: Add scheduler integration test (deferred to M6/M7)
    # async def test_scheduler_integration(self):
    #     scheduler = Scheduler(SchedulerConfig())
    #     ...
'''

    return template
