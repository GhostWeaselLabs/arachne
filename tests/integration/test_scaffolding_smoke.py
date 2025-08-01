"""Integration smoke tests for scaffolding generators.

Tests end-to-end generation and basic functionality of generated code.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest


class TestScaffoldingSmoke:
    """Smoke tests for scaffolding generators."""

    def test_node_generator_cli(self):
        """Test node generator CLI end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run node generator CLI
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "SmokeTestNode",
                    "--package",
                    "smoke_test",
                    "--inputs",
                    "data:dict,config:str",
                    "--outputs",
                    "result:dict",
                    "--dir",
                    temp_dir,
                    "--include-tests",
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Should succeed
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check output messages
            assert "Created node:" in result.stdout
            assert "Created test:" in result.stdout

            # Check files were created
            node_file = Path(temp_dir) / "smoke_test" / "smoke_test_node.py"
            assert node_file.exists()

            # Check content
            content = node_file.read_text()
            assert "class SmokeTestNode(Node):" in content
            assert '"data": PortSpec(name="data", schema=dict)' in content
            assert '"result": PortSpec(name="result", schema=dict)' in content

    def test_subgraph_generator_cli(self):
        """Test subgraph generator CLI end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run subgraph generator CLI
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_subgraph",
                    "--name",
                    "SmokeTestPipeline",
                    "--package",
                    "smoke_test",
                    "--dir",
                    temp_dir,
                    "--include-tests",
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Should succeed
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check output messages
            assert "Created subgraph:" in result.stdout
            assert "Created test:" in result.stdout

            # Check files were created
            subgraph_file = Path(temp_dir) / "smoke_test" / "smoke_test_pipeline.py"
            assert subgraph_file.exists()

            # Check content
            content = subgraph_file.read_text()
            assert "class SmokeTestPipeline(Subgraph):" in content
            assert "def validate_composition(self) -> None:" in content

    def test_generated_node_imports(self):
        """Test that generated node can be imported and instantiated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate node
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "ImportTestNode",
                    "--package",
                    "import_test",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            # Add to Python path and try to import
            sys.path.insert(0, temp_dir)
            try:
                # This will test that the generated code has valid syntax
                # and all imports work
                from import_test.import_test_node import ImportTestNode

                # Should be able to instantiate
                node = ImportTestNode()
                assert node.name == "import_test_node"

                # Should have proper port attributes
                assert hasattr(node, "inputs")
                assert hasattr(node, "outputs")
                assert isinstance(node.inputs, list)
                assert isinstance(node.outputs, list)

            finally:
                sys.path.remove(temp_dir)

    def test_generated_subgraph_imports(self):
        """Test that generated subgraph can be imported and instantiated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate subgraph
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_subgraph",
                    "--name",
                    "ImportTestPipeline",
                    "--package",
                    "import_test",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            # Add to Python path and try to import
            sys.path.insert(0, temp_dir)
            try:
                # This will test that the generated code has valid syntax
                # and all imports work
                from import_test.import_test_pipeline import ImportTestPipeline

                # Should be able to instantiate
                subgraph = ImportTestPipeline()
                assert subgraph.name == "import_test_pipeline"

                # Should have validation method
                assert hasattr(subgraph, "validate_composition")
                assert callable(subgraph.validate_composition)

            finally:
                sys.path.remove(temp_dir)

    def test_cli_error_handling(self):
        """Test CLI error handling for invalid inputs."""
        # Test invalid node name
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "arachne.scaffolding.generate_node",
                "--name",
                "invalid-name",  # Invalid: contains dash
                "--package",
                "test",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        assert result.returncode != 0
        assert "Error:" in result.stdout

    def test_file_overwrite_protection(self):
        """Test that files are protected from accidental overwrite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first node
            result1 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "OverwriteTest",
                    "--package",
                    "overwrite",
                    "--dir",
                    temp_dir,
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result1.returncode == 0

            # Try to create same node without --force
            result2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "OverwriteTest",
                    "--package",
                    "overwrite",
                    "--dir",
                    temp_dir,
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Should fail
            assert result2.returncode != 0
            assert "already exists" in result2.stdout

    def test_complex_port_types(self):
        """Test generation with complex port type annotations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate node with complex types
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "ComplexTypeNode",
                    "--package",
                    "complex",
                    "--inputs",
                    "data:List[Dict[str, Any]],config:Optional[str]",
                    "--outputs",
                    "results:Dict[str, List[int]]",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check generated content
            node_file = Path(temp_dir) / "complex" / "complex_type_node.py"
            content = node_file.read_text()

            assert "List[Dict[str, Any]]" in content
            assert "Optional[str]" in content
            assert "Dict[str, List[int]]" in content

    def test_package_creation(self):
        """Test that deep package structures are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate with deep package structure
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "DeepPackageNode",
                    "--package",
                    "very.deep.package.structure",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check directory structure
            deep_dir = Path(temp_dir) / "very" / "deep" / "package" / "structure"
            assert deep_dir.exists()

            node_file = deep_dir / "deep_package_node.py"
            assert node_file.exists()


class TestGeneratedCodeQuality:
    """Tests for quality of generated code."""

    def test_generated_node_linting(self):
        """Test that generated node code passes basic linting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a node
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "LintTestNode",
                    "--package",
                    "lint_test",
                    "--inputs",
                    "data:dict",
                    "--outputs",
                    "result:dict",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            node_file = Path(temp_dir) / "lint_test" / "lint_test_node.py"

            # Try to run ruff on generated file (if available)
            try:
                result = subprocess.run(
                    ["ruff", "check", str(node_file)], capture_output=True, text=True, timeout=10
                )

                # If ruff is available, generated code should pass
                if result.returncode == 127:  # Command not found
                    pytest.skip("ruff not available")
                else:
                    # Should have no major linting errors
                    assert result.returncode == 0, f"Linting failed: {result.stdout}"

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pytest.skip("ruff not available or timeout")

    def test_generated_node_type_checking(self):
        """Test that generated node code passes basic type checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a node
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "TypeTestNode",
                    "--package",
                    "type_test",
                    "--inputs",
                    "data:dict",
                    "--outputs",
                    "result:dict",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            node_file = Path(temp_dir) / "type_test" / "type_test_node.py"

            # Try to run mypy on generated file (if available)
            try:
                result = subprocess.run(
                    ["mypy", str(node_file), "--ignore-missing-imports"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                # If mypy is available, generated code should pass
                if result.returncode == 127:  # Command not found
                    pytest.skip("mypy not available")
                else:
                    # Should have no type errors
                    assert result.returncode == 0, f"Type checking failed: {result.stdout}"

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pytest.skip("mypy not available or timeout")

    def test_generated_code_line_count(self):
        """Test that generated code adheres to ~200 LOC guideline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a complex node
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_node",
                    "--name",
                    "ComplexNode",
                    "--package",
                    "complex",
                    "--inputs",
                    "in1:dict,in2:str,in3:int",
                    "--outputs",
                    "out1:dict,out2:str,out3:int",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            node_file = Path(temp_dir) / "complex" / "complex_node.py"
            content = node_file.read_text()
            line_count = len(content.splitlines())

            # Should be well under 200 lines
            assert line_count < 200, f"Generated node has {line_count} lines, should be under 200"

            # Generate a complex subgraph
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arachne.scaffolding.generate_subgraph",
                    "--name",
                    "ComplexPipeline",
                    "--package",
                    "complex",
                    "--dir",
                    temp_dir,
                    "--force",
                ],
                check=True,
                capture_output=True,
                cwd=os.getcwd(),
            )

            subgraph_file = Path(temp_dir) / "complex" / "complex_pipeline.py"
            content = subgraph_file.read_text()
            line_count = len(content.splitlines())

            # Should be well under 200 lines
            assert (
                line_count < 200
            ), f"Generated subgraph has {line_count} lines, should be under 200"
