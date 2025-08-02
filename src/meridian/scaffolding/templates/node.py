"""Node template generator."""

from __future__ import annotations

from ..parsers.ports import snake_case


def generate_node_template(
    class_name: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
    policy: str | None = None,
) -> str:
    """Generate node class template."""

    # Build port specs
    input_specs = []
    for port_name, port_type in inputs.items():
        input_specs.append(
            f'        "{port_name}": PortSpec(name="{port_name}", schema={port_type})'
        )

    output_specs = []
    for port_name, port_type in outputs.items():
        output_specs.append(
            f'        "{port_name}": PortSpec(name="{port_name}", schema={port_type})'
        )

    input_specs_str = ",\n".join(input_specs) if input_specs else "        # No input ports"
    output_specs_str = ",\n".join(output_specs) if output_specs else "        # No output ports"
    port_import = "from meridian.core.ports import PortSpec" if inputs or outputs else ""

    template = f'''"""Generated {class_name} node.

Purpose: TODO - Describe what this node does
Inputs: {list(inputs.keys()) if inputs else "None"}
Outputs: {list(outputs.keys()) if outputs else "None"}
{f"Default overflow policy is {policy}" if policy else ""}
"""

from __future__ import annotations

from typing import Any

from meridian.core.message import Message
from meridian.core.node import Node
{port_import}


class {class_name}(Node):
    """TODO: Brief description of {class_name} functionality."""

    def __init__(self, name: str = "{snake_case(class_name)}"):
        """Initialize the node with input and output port specifications."""
        inputs = {{
{input_specs_str}
        }}
        outputs = {{
{output_specs_str}
        }}
        super().__init__(name=name)
        self.inputs = inputs  # type: ignore[assignment]
        self.outputs = outputs  # type: ignore[assignment]

    async def on_start(self) -> None:
        """Called when the node starts. Override for initialization logic."""
        # TODO: Add initialization logic here
        pass

    async def on_message(self, port: str, message: Message[Any]) -> None:
        """Process incoming messages and produce outputs."""
        # TODO: Implement your processing logic here

        # Example: Forward data to output port
        # await self.send("output_port", message.payload)

        # Example: Transform data before sending
        # result = transform(message.payload)
        # await self.send("output_port", result)

        pass

    async def on_tick(self) -> None:
        """Periodic tick handler."""
        pass

    async def on_stop(self) -> None:
        """Called when the node stops. Override for cleanup logic."""
        # TODO: Add cleanup logic here
        pass
'''

    return template


def generate_node_test_template(
    class_name: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
) -> str:
    """Generate test template for node."""

    test_class = f"Test{class_name}"

    template = f'''"""Tests for {class_name} node."""

import pytest
from unittest.mock import AsyncMock

from {snake_case(class_name)} import {class_name}
from meridian.core.message import Message


class {test_class}:
    """Test cases for {class_name}."""

    @pytest.fixture
    def node(self):
        """Create a {class_name} instance for testing."""
        return {class_name}()

    def test_init(self, node):
        """Test node initialization."""
        assert node.name == "{snake_case(class_name)}"
        assert len(node.inputs) == {len(inputs)}
        assert len(node.outputs) == {len(outputs)}

    async def test_lifecycle(self, node):
        """Test node lifecycle methods."""
        await node.on_start()
        await node.on_stop()

    async def test_process_message(self, node):
        """Test message processing."""
        # TODO: Add specific test cases for your processing logic
        message = Message(payload="test_data", metadata={{}})

        # Mock the send method to capture outputs
        node.send = AsyncMock()

        # Test processing
        await node.on_message("input_port", message)

        # TODO: Add assertions based on expected behavior
        # Example: node.send.assert_called_once_with("output_port", expected_result)
'''

    return template


def generate_test_template(class_name: str, module_path: str) -> str:
    """Generate test template for node (legacy API)."""

    test_class = f"Test{class_name}"

    template = f'''"""Tests for {class_name} node."""

import pytest
from unittest.mock import AsyncMock

from {module_path} import {class_name}
from meridian.core.message import Message


class {test_class}:
    """Test cases for {class_name}."""

    @pytest.fixture
    def node(self):
        """Create a {class_name} instance for testing."""
        return {class_name}()

    def test_node_creation(self, node):
        """Basic instantiation test."""
        assert node.name == "{snake_case(class_name)}"

    def test_port_definitions(self, node):
        """Ensure ports are defined."""
        assert isinstance(node.inputs, dict)
        assert isinstance(node.outputs, dict)

    async def test_lifecycle_hooks(self, node):
        """Exercise lifecycle hooks."""
        await node.on_start()
        await node.on_message("input_port", Message(payload="", metadata={{}}))
        await node.on_tick()
        await node.on_stop()
'''

    return template
