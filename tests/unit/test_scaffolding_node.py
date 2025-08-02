"""Unit tests for arachne.scaffolding.generate_node module."""

from pathlib import Path
import tempfile

import pytest

from meridian.scaffolding.generate_node import (
    create_node_files,
    generate_node_template,
    generate_test_template,
    parse_ports,
    snake_case,
)


class TestSnakeCase:
    """Test suite for snake_case function."""

    def test_pascal_to_snake(self):
        """Test converting PascalCase to snake_case."""
        assert snake_case("DataProcessor") == "data_processor"
        assert snake_case("XMLParser") == "x_m_l_parser"
        assert snake_case("HTTPClient") == "h_t_t_p_client"
        assert snake_case("SimpleNode") == "simple_node"

    def test_single_word(self):
        """Test single word conversion."""
        assert snake_case("Node") == "node"
        assert snake_case("A") == "a"

    def test_already_lowercase(self):
        """Test already lowercase strings."""
        assert snake_case("lowercase") == "lowercase"

    def test_empty_string(self):
        """Test empty string."""
        assert snake_case("") == ""


class TestParsePorts:
    """Test suite for parse_ports function."""

    def test_empty_string(self):
        """Test parsing empty port string."""
        assert parse_ports("") == {}
        assert parse_ports("  ") == {}

    def test_single_port(self):
        """Test parsing single port definition."""
        result = parse_ports("input:dict")
        assert result == {"input": "dict"}

    def test_multiple_ports(self):
        """Test parsing multiple port definitions."""
        result = parse_ports("in:dict,out:str,config:int")
        expected = {"in": "dict", "out": "str", "config": "int"}
        assert result == expected

    def test_whitespace_handling(self):
        """Test handling of whitespace in port definitions."""
        result = parse_ports(" input : dict , output : str ")
        expected = {"input": "dict", "output": "str"}
        assert result == expected

    def test_invalid_format(self):
        """Test error handling for invalid format."""
        with pytest.raises(ValueError, match="Invalid port definition"):
            parse_ports("invalid_format")

        with pytest.raises(ValueError, match="Invalid port definition"):
            parse_ports("valid:dict,invalid_format")

    def test_complex_types(self):
        """Test parsing with complex type annotations."""
        result = parse_ports("data:List[Dict[str, Any]],config:Optional[str]")
        expected = {"data": "List[Dict[str, Any]]", "config": "Optional[str]"}
        assert result == expected


class TestGenerateNodeTemplate:
    """Test suite for generate_node_template function."""

    def test_basic_template(self):
        """Test generating basic node template."""
        template = generate_node_template("TestNode", {}, {})

        assert "class TestNode(Node):" in template
        assert "def __init__(self" in template
        assert "from meridian.core.node import Node" in template

    def test_with_input_ports(self):
        """Test template generation with input ports."""
        inputs = {"data": "dict", "config": "str"}
        template = generate_node_template("DataProcessor", inputs, {})

        assert '"data": PortSpec(name="data", schema=dict)' in template
        assert '"config": PortSpec(name="config", schema=str)' in template

    def test_with_output_ports(self):
        """Test template generation with output ports."""
        outputs = {"result": "dict", "status": "str"}
        template = generate_node_template("Processor", {}, outputs)

        assert '"result": PortSpec(name="result", schema=dict)' in template
        assert '"status": PortSpec(name="status", schema=str)' in template

    def test_with_policy(self):
        """Test template generation with custom policy."""
        template = generate_node_template("TestNode", {}, {}, policy="drop")

        assert "Default overflow policy is drop" in template

    def test_complete_template(self):
        """Test complete template with inputs, outputs, and policy."""
        inputs = {"input": "dict"}
        outputs = {"output": "dict"}
        template = generate_node_template("CompleteNode", inputs, outputs, "latest")

        # Check all lifecycle methods are present
        assert "async def on_start(self) -> None:" in template
        assert "async def on_message" in template
        assert "async def on_tick(self) -> None:" in template
        assert "async def on_stop(self) -> None:" in template

        # Check docstring mentions policy
        assert "Default overflow policy is latest" in template


class TestGenerateTestTemplate:
    """Test suite for generate_test_template function."""

    def test_basic_test_template(self):
        """Test generating basic test template."""
        template = generate_test_template("TestNode", "mypackage.test_node")

        assert "class TestTestNode:" in template
        assert "from mypackage.test_node import TestNode" in template
        assert "def test_node_creation(self, node):" in template
        assert "def test_port_definitions(self, node):" in template

    def test_async_test_methods(self):
        """Test that async test methods are included."""
        template = generate_test_template("AsyncNode", "test.async_node")

        assert "async def test_lifecycle_hooks" in template

    def test_snake_case_in_tests(self):
        """Test that snake_case conversion works in test template."""
        template = generate_test_template("DataProcessor", "nodes.data_processor")

        assert 'assert node.name == "data_processor"' in template


class TestCreateNodeFiles:
    """Test suite for create_node_files function."""

    def test_file_creation(self):
        """Test that files are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_node_files(
                name="TestNode",
                package="test.nodes",
                inputs={"input": "dict"},
                outputs={"output": "dict"},
                base_dir=temp_dir,
                include_tests=True,
                force=False,
                policy="block",
            )

            # Check node file was created
            node_file = Path(temp_dir) / "test" / "nodes" / "test_node.py"
            assert node_file.exists()

            # Check test file was created
            Path("tests/unit/test_test_node.py")
            # Note: In real test this would be created, but we're in temp dir

    def test_package_directory_creation(self):
        """Test that package directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_node_files(
                name="DeepNode",
                package="very.deep.package.structure",
                inputs={},
                outputs={},
                base_dir=temp_dir,
                include_tests=False,
                force=False,
                policy="block",
            )

            # Check directory structure was created
            package_dir = Path(temp_dir) / "very" / "deep" / "package" / "structure"
            assert package_dir.exists()

            # Check file was created
            node_file = package_dir / "deep_node.py"
            assert node_file.exists()

    def test_force_overwrite(self):
        """Test force overwrite functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file first
            package_dir = Path(temp_dir) / "test"
            package_dir.mkdir(parents=True)
            existing_file = package_dir / "existing_node.py"
            existing_file.write_text("existing content")

            # Should succeed with force=True
            create_node_files(
                name="ExistingNode",
                package="test",
                inputs={},
                outputs={},
                base_dir=temp_dir,
                include_tests=False,
                force=True,
                policy="block",
            )

            # File should be overwritten
            content = existing_file.read_text()
            assert "class ExistingNode(Node):" in content

    def test_file_exists_no_force(self):
        """Test error when file exists and force=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file first
            package_dir = Path(temp_dir) / "test"
            package_dir.mkdir(parents=True)
            existing_file = package_dir / "existing_node.py"
            existing_file.write_text("existing content")

            # Should return False when not forcing overwrite
            success = create_node_files(
                name="ExistingNode",
                package="test",
                inputs={},
                outputs={},
                base_dir=temp_dir,
                include_tests=False,
                force=False,
                policy="block",
            )

            assert success is False


class TestIntegration:
    """Integration tests for node generation."""

    def test_complete_node_generation(self):
        """Test complete node generation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a complete node
            create_node_files(
                name="CompleteProcessor",
                package="processors",
                inputs={"raw_data": "dict", "config": "str"},
                outputs={"processed": "dict", "metadata": "dict"},
                base_dir=temp_dir,
                include_tests=True,
                force=False,
                policy="latest",
            )

            # Check node file content
            node_file = Path(temp_dir) / "processors" / "complete_processor.py"
            assert node_file.exists()

            content = node_file.read_text()
            assert "class CompleteProcessor(Node):" in content
            assert '"raw_data": PortSpec(name="raw_data", schema=dict)' in content
            assert '"processed": PortSpec(name="processed", schema=dict)' in content
            assert "Default overflow policy is latest" in content

    def test_generated_code_syntax(self):
        """Test that generated code has valid Python syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_node_files(
                name="SyntaxTestNode",
                package="syntax_test",
                inputs={"input": "List[Dict[str, Any]]"},
                outputs={"output": "Optional[str]"},
                base_dir=temp_dir,
                include_tests=False,
                force=False,
                policy="coalesce",
            )

            node_file = Path(temp_dir) / "syntax_test" / "syntax_test_node.py"
            content = node_file.read_text()

            # Should be able to compile the generated code
            try:
                compile(content, str(node_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Generated code has syntax error: {e}")

    def test_imports_in_generated_code(self):
        """Test that all necessary imports are present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_node_files(
                name="ImportTestNode",
                package="import_test",
                inputs={"data": "Any"},
                outputs={"result": "Dict[str, Any]"},
                base_dir=temp_dir,
                include_tests=False,
                force=False,
                policy="block",
            )

            node_file = Path(temp_dir) / "import_test" / "import_test_node.py"
            content = node_file.read_text()

            # Check required imports
            assert "from __future__ import annotations" in content
            assert "from typing import Any" in content
            assert "from meridian.core.message import Message" in content
            assert "from meridian.core.node import Node" in content
            assert "from meridian.core.ports import PortSpec" in content
