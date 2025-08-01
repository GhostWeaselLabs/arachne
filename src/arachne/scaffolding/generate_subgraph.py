#!/usr/bin/env python3
"""Subgraph generator CLI for Arachne.

Generates subgraph class skeletons with wiring stubs and tests.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def generate_subgraph_template(class_name: str) -> str:
    """Generate subgraph class template."""
    
    template = f'''"""Generated {class_name} subgraph.

Purpose: TODO - Describe what this subgraph does
Composition: TODO - Document the nodes and their connections
Exposed Ports: TODO - Document input/output port behavior
"""

from __future__ import annotations

from typing import Dict

from arachne.core.subgraph import Subgraph
from arachne.core.ports import PortSpec
# TODO: Import your node classes here
# from arachne.nodes.your_node import YourNode


class {class_name}(Subgraph):
    """TODO: Brief description of {class_name} functionality."""
    
    def __init__(self):
        """Initialize the subgraph."""
        super().__init__()
        self._setup_nodes()
        self._setup_connections()
        self._setup_exposed_ports()
    
    def _setup_nodes(self) -> None:
        """Add nodes to the subgraph."""
        # TODO: Add your nodes here
        # Example:
        # self.add_node("processor", YourNode())
        # self.add_node("validator", AnotherNode())
        pass
    
    def _setup_connections(self) -> None:
        """Connect nodes with edges."""
        # TODO: Wire your nodes together
        # Example:
        # self.connect(
        #     "processor", "output",
        #     "validator", "input",
        #     capacity=100,
        #     policy="block"
        # )
        pass
    
    def _setup_exposed_ports(self) -> None:
        """Expose input and output ports."""
        # TODO: Expose ports to make them available externally
        # Example:
        # self.expose_input("data_in", "processor", "input")
        # self.expose_output("results", "validator", "output")
        pass
    
    def name(self) -> str:
        """Return the subgraph name."""
        return "{snake_case(class_name)}"
    
    def validate_composition(self) -> None:
        """Validate the subgraph composition."""
        # Run basic validation
        from arachne.utils.validation import validate_graph
        issues = validate_graph(self)
        
        # Report any issues
        errors = [issue for issue in issues if issue.is_error()]
        warnings = [issue for issue in issues if issue.is_warning()]
        
        if warnings:
            print(f"Warnings in {{self.name()}}:")
            for warning in warnings:
                print(f"  - {{warning.message}} ({{warning.location}})")
        
        if errors:
            print(f"Errors in {{self.name()}}:")
            for error in errors:
                print(f"  - {{error.message}} ({{error.location}})")
            raise ValueError(f"Subgraph {{self.name()}} has validation errors")
        
        print(f"Subgraph {{self.name()}} validation passed")


# Example usage (disabled by default)
if __name__ == "__main__":
    # This is for development/testing only
    # In production, subgraphs are used within schedulers
    subgraph = {class_name}()
    subgraph.validate_composition()
    print(f"Created {{subgraph.name()}} subgraph")
'''
    
    return template


def generate_subgraph_test_template(class_name: str, module_name: str) -> str:
    """Generate integration test template."""
    
    template = f'''"""Integration tests for {class_name} subgraph."""

import pytest

from {module_name} import {class_name}


class Test{class_name}:
    """Test suite for {class_name}."""
    
    def test_subgraph_creation(self):
        """Test basic subgraph instantiation."""
        subgraph = {class_name}()
        assert subgraph.name() == "{snake_case(class_name)}"
    
    def test_subgraph_validation(self):
        """Test subgraph composition validation."""
        subgraph = {class_name}()
        
        # Should not raise exceptions for basic validation
        # TODO: Update this test once nodes are added
        try:
            subgraph.validate_composition()
        except ValueError:
            # Expected if no nodes are added yet
            pass
    
    def test_node_composition(self):
        """Test that nodes are properly added."""
        subgraph = {class_name}()
        
        # TODO: Add tests for specific nodes once they're added
        # assert "processor" in subgraph._nodes
        # assert "validator" in subgraph._nodes
        pass
    
    def test_port_exposure(self):
        """Test that ports are properly exposed.""" 
        subgraph = {class_name}()
        
        # TODO: Add tests for exposed ports once they're defined
        # inputs = subgraph.exposed_inputs()
        # outputs = subgraph.exposed_outputs()
        # assert "data_in" in inputs
        # assert "results" in outputs
        pass
    
    def test_edge_connections(self):
        """Test that edges are properly connected."""
        subgraph = {class_name}()
        
        # TODO: Add tests for edge connections once they're defined
        # edges = subgraph._edges
        # assert len(edges) > 0
        pass
    
    # TODO: Add scheduler integration test (deferred to M6/M7)
    # @pytest.mark.asyncio
    # async def test_scheduler_integration(self):
    #     """Test subgraph execution with scheduler.""" 
    #     from arachne.core.scheduler import Scheduler
    #     
    #     subgraph = {class_name}()
    #     scheduler = Scheduler()
    #     scheduler.add_subgraph(subgraph)
    #     
    #     # Run for a short time
    #     await scheduler.start()
    #     await asyncio.sleep(0.1)
    #     await scheduler.stop()
'''
    
    return template


def create_subgraph_files(
    name: str,
    package: str,
    base_dir: str,
    include_tests: bool,
    force: bool
) -> None:
    """Create subgraph files with templates."""
    
    # Convert package path to directory
    package_parts = package.split('.')
    src_dir = Path(base_dir) / '/'.join(package_parts)
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate file paths
    module_name = snake_case(name)
    subgraph_file = src_dir / f"{module_name}.py"
    
    # Check if files exist
    if subgraph_file.exists() and not force:
        print(f"Error: {subgraph_file} already exists. Use --force to overwrite.")
        sys.exit(1)
    
    # Generate subgraph file
    subgraph_content = generate_subgraph_template(name)
    with open(subgraph_file, 'w') as f:
        f.write(subgraph_content)
    
    print(f"Created subgraph: {subgraph_file}")
    
    # Generate test file if requested
    if include_tests:
        test_dir = Path("tests/integration")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / f"test_{module_name}.py"
        
        if test_file.exists() and not force:
            print(f"Warning: {test_file} already exists. Skipping test creation.")
        else:
            test_content = generate_subgraph_test_template(name, package + '.' + module_name)
            with open(test_file, 'w') as f:
                f.write(test_content)
            print(f"Created test: {test_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Arachne subgraph skeleton with wiring stubs and tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic subgraph
  python -m arachne.scaffolding.generate_subgraph --name DataPipeline
  
  # Custom package and directory with tests
  python -m arachne.scaffolding.generate_subgraph --name MarketPipeline \\
    --package myapp.subgraphs --dir custom_src --include-tests
        """
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="PascalCase class name for the subgraph"
    )
    parser.add_argument(
        "--package",
        default="arachne.subgraphs",
        help="Dot-separated package path (default: arachne.subgraphs)"
    )
    parser.add_argument(
        "--dir",
        default="src",
        help="Base directory for generated files (default: src)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Generate integration test file"
    )
    
    args = parser.parse_args()
    
    try:
        # Validate class name
        if not args.name.isidentifier() or not args.name[0].isupper():
            print("Error: Name must be a valid PascalCase identifier")
            sys.exit(1)
        
        # Create files
        create_subgraph_files(
            args.name,
            args.package,
            args.dir,
            args.include_tests,
            args.force
        )
        
        print(f"Successfully generated {args.name} subgraph")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 