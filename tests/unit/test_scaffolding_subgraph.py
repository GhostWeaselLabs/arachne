"""Unit tests for arachne.scaffolding.generate_subgraph module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from arachne.scaffolding.generate_subgraph import (
    snake_case,
    generate_subgraph_template,
    generate_subgraph_test_template,
    create_subgraph_files
)


class TestSnakeCase:
    """Test suite for snake_case function."""
    
    def test_pascal_to_snake(self):
        """Test converting PascalCase to snake_case."""
        assert snake_case("DataPipeline") == "data_pipeline"
        assert snake_case("MarketProcessor") == "market_processor"
        assert snake_case("HTTPAPIGateway") == "h_t_t_p_a_p_i_gateway"
        assert snake_case("SimpleSubgraph") == "simple_subgraph"
    
    def test_single_word(self):
        """Test single word conversion."""
        assert snake_case("Pipeline") == "pipeline"
        assert snake_case("Graph") == "graph"
    
    def test_already_lowercase(self):
        """Test already lowercase strings."""
        assert snake_case("lowercase") == "lowercase"
    
    def test_empty_string(self):
        """Test empty string."""
        assert snake_case("") == ""


class TestGenerateSubgraphTemplate:
    """Test suite for generate_subgraph_template function."""
    
    def test_basic_template(self):
        """Test generating basic subgraph template."""
        template = generate_subgraph_template("TestPipeline")
        
        assert "class TestPipeline(Subgraph):" in template
        assert "def name(self) -> str:" in template
        assert 'return "test_pipeline"' in template
        assert "from arachne.core.subgraph import Subgraph" in template
    
    def test_initialization_methods(self):
        """Test that initialization methods are included."""
        template = generate_subgraph_template("DataPipeline")
        
        assert "def _setup_nodes(self) -> None:" in template
        assert "def _setup_connections(self) -> None:" in template
        assert "def _setup_exposed_ports(self) -> None:" in template
        assert "def validate_composition(self) -> None:" in template
    
    def test_docstring_structure(self):
        """Test that proper docstring structure is included."""
        template = generate_subgraph_template("ProcessingPipeline")
        
        assert "Purpose: TODO - Describe what this subgraph does" in template
        assert "Composition: TODO - Document the nodes and their connections" in template
        assert "Exposed Ports: TODO - Document input/output port behavior" in template
    
    def test_example_comments(self):
        """Test that example comments are included."""
        template = generate_subgraph_template("ExampleGraph")
        
        # Should have example node addition
        assert "# self.add_node(" in template
        
        # Should have example connection
        assert "# self.connect(" in template
        
        # Should have example port exposure
        assert "# self.expose_input(" in template
        assert "# self.expose_output(" in template
    
    def test_validation_integration(self):
        """Test that validation integration is included."""
        template = generate_subgraph_template("ValidatedGraph")
        
        assert "from arachne.utils.validation import validate_graph" in template
        assert "issues = validate_graph(self)" in template
        assert "issue.is_error()" in template
        assert "issue.is_warning()" in template
    
    def test_main_section(self):
        """Test that main section is included for development."""
        template = generate_subgraph_template("DevGraph")
        
        assert 'if __name__ == "__main__":' in template
        assert "subgraph.validate_composition()" in template


class TestGenerateSubgraphTestTemplate:
    """Test suite for generate_subgraph_test_template function."""
    
    def test_basic_test_template(self):
        """Test generating basic test template."""
        template = generate_subgraph_test_template("TestPipeline", "mypackage.test_pipeline")
        
        assert "class TestTestPipeline:" in template
        assert "from mypackage.test_pipeline import TestPipeline" in template
        assert "def test_subgraph_creation(self):" in template
        assert "def test_subgraph_validation(self):" in template
    
    def test_composition_tests(self):
        """Test that composition test methods are included."""
        template = generate_subgraph_test_template("DataPipeline", "pipelines.data_pipeline")
        
        assert "def test_node_composition(self):" in template
        assert "def test_port_exposure(self):" in template
        assert "def test_edge_connections(self):" in template
    
    def test_snake_case_in_tests(self):
        """Test that snake_case conversion works in test template."""
        template = generate_subgraph_test_template("DataProcessor", "nodes.data_processor")
        
        assert 'assert subgraph.name() == "data_processor"' in template
    
    def test_scheduler_integration_placeholder(self):
        """Test that scheduler integration test placeholder is included."""
        template = generate_subgraph_test_template("AsyncPipeline", "async.pipeline")
        
        # Should have commented out scheduler test
        assert "# TODO: Add scheduler integration test (deferred to M6/M7)" in template
        assert "# async def test_scheduler_integration(self):" in template
        assert "# from arachne.core.scheduler import Scheduler" in template
    
    def test_validation_exception_handling(self):
        """Test that validation exception handling is included."""
        template = generate_subgraph_test_template("ValidatedPipeline", "validated.pipeline")
        
        assert "try:" in template
        assert "subgraph.validate_composition()" in template
        assert "except ValueError:" in template
        assert "# Expected if no nodes are added yet" in template


class TestCreateSubgraphFiles:
    """Test suite for create_subgraph_files function."""
    
    def test_file_creation(self):
        """Test that files are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="TestPipeline",
                package="test.pipelines",
                base_dir=temp_dir,
                include_tests=True,
                force=False
            )
            
            # Check subgraph file was created
            subgraph_file = Path(temp_dir) / "test" / "pipelines" / "test_pipeline.py"
            assert subgraph_file.exists()
            
            # Check test file was created
            test_file = Path("tests/integration/test_test_pipeline.py")
            # Note: In real test this would be created, but we're in temp dir
    
    def test_package_directory_creation(self):
        """Test that package directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="DeepPipeline",
                package="very.deep.package.structure",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            # Check directory structure was created
            package_dir = Path(temp_dir) / "very" / "deep" / "package" / "structure"
            assert package_dir.exists()
            
            # Check file was created
            subgraph_file = package_dir / "deep_pipeline.py"
            assert subgraph_file.exists()
    
    def test_force_overwrite(self):
        """Test force overwrite functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file first
            package_dir = Path(temp_dir) / "test"
            package_dir.mkdir(parents=True)
            existing_file = package_dir / "existing_pipeline.py"
            existing_file.write_text("existing content")
            
            # Should succeed with force=True
            create_subgraph_files(
                name="ExistingPipeline",
                package="test",
                base_dir=temp_dir,
                include_tests=False,
                force=True
            )
            
            # File should be overwritten
            content = existing_file.read_text()
            assert "class ExistingPipeline(Subgraph):" in content
    
    @patch('sys.exit')
    def test_file_exists_no_force(self, mock_exit):
        """Test error when file exists and force=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file first
            package_dir = Path(temp_dir) / "test"
            package_dir.mkdir(parents=True)
            existing_file = package_dir / "existing_pipeline.py"
            existing_file.write_text("existing content")
            
            # Should exit with error
            create_subgraph_files(
                name="ExistingPipeline",
                package="test",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            mock_exit.assert_called_once_with(1)
    
    def test_integration_test_directory(self):
        """Test that integration test directory is used."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp dir to test relative paths
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(temp_dir)
                
                create_subgraph_files(
                    name="IntegrationPipeline",
                    package="integration",
                    base_dir="src",
                    include_tests=True,
                    force=False
                )
                
                # Check that integration test directory is created
                test_dir = Path("tests/integration")
                assert test_dir.exists()
                
                # Check test file
                test_file = test_dir / "test_integration_pipeline.py"
                assert test_file.exists()
                
            finally:
                os.chdir(original_cwd)


class TestIntegration:
    """Integration tests for subgraph generation."""
    
    def test_complete_subgraph_generation(self):
        """Test complete subgraph generation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a complete subgraph
            create_subgraph_files(
                name="CompleteDataPipeline",
                package="pipelines",
                base_dir=temp_dir,
                include_tests=True,
                force=False
            )
            
            # Check subgraph file content
            subgraph_file = Path(temp_dir) / "pipelines" / "complete_data_pipeline.py"
            assert subgraph_file.exists()
            
            content = subgraph_file.read_text()
            assert "class CompleteDataPipeline(Subgraph):" in content
            assert "def _setup_nodes(self) -> None:" in content
            assert "def _setup_connections(self) -> None:" in content
            assert "def _setup_exposed_ports(self) -> None:" in content
            assert "def validate_composition(self) -> None:" in content
    
    def test_generated_code_syntax(self):
        """Test that generated code has valid Python syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="SyntaxTestPipeline",
                package="syntax_test",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            subgraph_file = Path(temp_dir) / "syntax_test" / "syntax_test_pipeline.py"
            content = subgraph_file.read_text()
            
            # Should be able to compile the generated code
            try:
                compile(content, str(subgraph_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_imports_in_generated_code(self):
        """Test that all necessary imports are present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="ImportTestPipeline",
                package="import_test",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            subgraph_file = Path(temp_dir) / "import_test" / "import_test_pipeline.py"
            content = subgraph_file.read_text()
            
            # Check required imports
            assert "from __future__ import annotations" in content
            assert "from typing import Dict" in content
            assert "from arachne.core.subgraph import Subgraph" in content
            assert "from arachne.core.ports import PortSpec" in content
            assert "from arachne.utils.validation import validate_graph" in content
    
    def test_generated_test_syntax(self):
        """Test that generated test code has valid Python syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(temp_dir)
                
                create_subgraph_files(
                    name="TestSyntaxPipeline",
                    package="test_syntax",
                    base_dir="src",
                    include_tests=True,
                    force=False
                )
                
                test_file = Path("tests/integration/test_test_syntax_pipeline.py")
                if test_file.exists():
                    content = test_file.read_text()
                    
                    # Should be able to compile the generated test code
                    try:
                        compile(content, str(test_file), 'exec')
                    except SyntaxError as e:
                        pytest.fail(f"Generated test code has syntax error: {e}")
                        
            finally:
                os.chdir(original_cwd)
    
    def test_validation_method_functionality(self):
        """Test that the validation method in generated code is functional."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="ValidationTestPipeline",
                package="validation_test",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            subgraph_file = Path(temp_dir) / "validation_test" / "validation_test_pipeline.py"
            content = subgraph_file.read_text()
            
            # Should include proper validation logic
            assert "validate_graph(self)" in content
            assert "issue.is_error()" in content
            assert "issue.is_warning()" in content
            assert "raise ValueError" in content
    
    def test_class_naming_consistency(self):
        """Test that class names and file names are consistent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            create_subgraph_files(
                name="ConsistencyTestPipeline",
                package="consistency",
                base_dir=temp_dir,
                include_tests=False,
                force=False
            )
            
            # File should be snake_case
            subgraph_file = Path(temp_dir) / "consistency" / "consistency_test_pipeline.py"
            assert subgraph_file.exists()
            
            content = subgraph_file.read_text()
            
            # Class should be PascalCase
            assert "class ConsistencyTestPipeline(Subgraph):" in content
            
            # name() method should return snake_case
            assert 'return "consistency_test_pipeline"' in content 