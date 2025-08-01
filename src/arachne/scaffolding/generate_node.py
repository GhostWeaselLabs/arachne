#!/usr/bin/env python3
"""Node generator CLI for Arachne.

Generates node class skeletons with proper typing, lifecycle hooks, and tests.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List


def snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def parse_ports(port_str: str) -> Dict[str, str]:
    """Parse port string like 'in:dict,out:int' into dict."""
    if not port_str.strip():
        return {}
    
    ports = {}
    # Handle complex types with nested brackets by being more careful about splitting
    port_defs = []
    current_def = ""
    bracket_depth = 0
    
    for char in port_str:
        if char in '[{(':
            bracket_depth += 1
        elif char in ']})':
            bracket_depth -= 1
        elif char == ',' and bracket_depth == 0:
            port_defs.append(current_def.strip())
            current_def = ""
            continue
        current_def += char
    
    if current_def.strip():
        port_defs.append(current_def.strip())
    
    for port_def in port_defs:
        port_def = port_def.strip()
        if ':' not in port_def:
            raise ValueError(f"Invalid port definition: {port_def}. Expected format: name:type")
        
        name, type_str = port_def.split(':', 1)
        ports[name.strip()] = type_str.strip()
    
    return ports


def generate_node_template(
    class_name: str,
    inputs: Dict[str, str],
    outputs: Dict[str, str],
    policy: str = "block"
) -> str:
    """Generate node class template."""
    
    # Generate input port specs
    input_specs = []
    for port_name, port_type in inputs.items():
        input_specs.append(f'        "{port_name}": PortSpec(name="{port_name}", schema={port_type})')
    
    # Generate output port specs  
    output_specs = []
    for port_name, port_type in outputs.items():
        output_specs.append(f'        "{port_name}": PortSpec(name="{port_name}", schema={port_type})')
    
    inputs_dict = "{\n" + ",\n".join(input_specs) + "\n    }" if input_specs else "{}"
    outputs_dict = "{\n" + ",\n".join(output_specs) + "\n    }" if output_specs else "{}"
    
    template = f'''"""Generated {class_name} node.

Purpose: TODO - Describe what this node does
Ports: TODO - Document input/output port behavior  
Policies: Default overflow policy is {policy}
Error handling: Exceptions logged and node continues by default
Observability: Lifecycle events and message processing automatically logged
"""

from __future__ import annotations

from typing import Any

from arachne.core.message import Message
from arachne.core.node import Node
from arachne.core.ports import Port, PortSpec


class {class_name}(Node):
    """TODO: Brief description of {class_name} functionality."""
    
    def __init__(self, name: str = "{snake_case(class_name)}") -> None:
        """Initialize the node with ports."""
        # TODO: Define input and output ports
        input_ports = []  # Add Port instances for inputs
        output_ports = []  # Add Port instances for outputs
        
        super().__init__(name=name, inputs=input_ports, outputs=output_ports)
    
    def on_start(self) -> None:
        """Initialize node when starting."""
        # TODO: Add initialization logic
        pass
    
    def on_message(self, port: str, message: Message) -> None:
        """Process incoming message."""
        # TODO: Add message processing logic
        # Example:
        # if port == "input_port":
        #     result = self.process_data(message.payload)
        #     self.emit("output_port", Message.create(result))
        pass
    
    def on_tick(self) -> None:
        """Handle periodic tick."""
        # TODO: Add tick processing logic if needed
        pass
    
    def on_stop(self) -> None:
        """Clean up when stopping."""
        # TODO: Add cleanup logic
        pass
    
    def process_data(self, data: Any) -> Any:
        """TODO: Implement main processing logic."""
        # Business logic goes here
        return data


# Example usage (disabled by default)
if __name__ == "__main__":
    # This is for development/testing only
    # In production, nodes are used within subgraphs and schedulers
    pass
'''
    
    return template


def generate_test_template(class_name: str, module_name: str) -> str:
    """Generate unit test template."""
    
    template = f'''"""Unit tests for {class_name} node."""

import pytest

from {module_name} import {class_name}
from arachne.core.message import Message


class Test{class_name}:
    """Test suite for {class_name}."""
    
    def test_node_creation(self):
        """Test basic node instantiation."""
        node = {class_name}()
        assert node.name == "{snake_case(class_name)}"
    
    def test_port_definitions(self):
        """Test input and output port definitions."""
        node = {class_name}()
        
        inputs = node.inputs
        outputs = node.outputs
        
        assert isinstance(inputs, list)
        assert isinstance(outputs, list)
        
        # TODO: Add specific port validation tests
        # assert any(p.name == "expected_input" for p in inputs)
        # assert any(p.name == "expected_output" for p in outputs)
    
    def test_lifecycle_hooks(self):
        """Test node lifecycle hooks can be called."""
        node = {class_name}()
        
        # Should not raise exceptions
        node.on_start()
        node.on_tick()
        node.on_stop()
    
    def test_message_processing(self):
        """Test basic message processing."""
        node = {class_name}()
        
        # Create test message
        message = Message.create({{"test": "data"}})
        
        # Should not raise exceptions
        node.on_message("test_port", message)
        
        # TODO: Add specific message processing tests
        # result = await node.process_data(message.payload)
        # assert result == expected_result
    
    def test_process_data(self):
        """Test main processing logic."""
        node = {class_name}()
        
        # TODO: Add specific data processing tests
        test_data = {{"test": "input"}}
        result = node.process_data(test_data)
        
        # Currently just passes through - update based on actual logic
        assert result == test_data
'''
    
    return template


def create_node_files(
    name: str,
    package: str, 
    inputs: Dict[str, str],
    outputs: Dict[str, str],
    base_dir: str,
    include_tests: bool,
    force: bool,
    policy: str
) -> None:
    """Create node files with templates."""
    
    # Convert package path to directory
    package_parts = package.split('.')
    src_dir = Path(base_dir) / '/'.join(package_parts)
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate file paths
    module_name = snake_case(name)
    node_file = src_dir / f"{module_name}.py"
    
    # Check if files exist
    if node_file.exists() and not force:
        print(f"Error: {node_file} already exists. Use --force to overwrite.")
        sys.exit(1)
    
    # Generate node file
    node_content = generate_node_template(name, inputs, outputs, policy)
    with open(node_file, 'w') as f:
        f.write(node_content)
    
    print(f"Created node: {node_file}")
    
    # Generate test file if requested
    if include_tests:
        test_dir = Path("tests/unit")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / f"test_{module_name}.py"
        
        if test_file.exists() and not force:
            print(f"Warning: {test_file} already exists. Skipping test creation.")
        else:
            test_content = generate_test_template(name, package + '.' + module_name)
            with open(test_file, 'w') as f:
                f.write(test_content)
            print(f"Created test: {test_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Arachne node skeleton with typing and tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic node with no ports
  python -m arachne.scaffolding.generate_node --name DataProcessor
  
  # Node with specific ports
  python -m arachne.scaffolding.generate_node --name PriceNormalizer \\
    --inputs "raw:dict,config:dict" --outputs "normalized:dict"
  
  # Custom package and directory
  python -m arachne.scaffolding.generate_node --name MyNode \\
    --package myapp.nodes --dir custom_src --include-tests
        """
    )
    
    parser.add_argument(
        "--name", 
        required=True,
        help="PascalCase class name for the node"
    )
    parser.add_argument(
        "--package",
        default="arachne.nodes", 
        help="Dot-separated package path (default: arachne.nodes)"
    )
    parser.add_argument(
        "--inputs",
        default="",
        help="Comma-separated input ports as name:type pairs (e.g., 'in:dict,config:str')"
    )
    parser.add_argument(
        "--outputs", 
        default="",
        help="Comma-separated output ports as name:type pairs (e.g., 'out:dict,status:str')"
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
        help="Generate unit test file"
    )
    parser.add_argument(
        "--policy",
        default="block",
        choices=["block", "drop", "latest", "coalesce"],
        help="Default edge overflow policy hint (default: block)"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse port specifications
        inputs = parse_ports(args.inputs)
        outputs = parse_ports(args.outputs)
        
        # Validate class name
        if not args.name.isidentifier() or not args.name[0].isupper():
            print("Error: Name must be a valid PascalCase identifier")
            sys.exit(1)
        
        # Create files
        create_node_files(
            args.name,
            args.package,
            inputs, 
            outputs,
            args.dir,
            args.include_tests,
            args.force,
            args.policy
        )
        
        print(f"Successfully generated {args.name} node")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 