"""Unit tests for meridian.utils.validation module."""

from unittest.mock import Mock

import pytest

from meridian.utils.validation import (
    Issue,
    PydanticAdapter,
    SchemaValidator,
    validate_connection,
    validate_graph,
    validate_ports,
)


class TestIssue:
    """Test suite for Issue dataclass."""

    def test_issue_creation(self):
        """Test basic Issue creation."""
        issue = Issue(severity="error", message="Test error", location="test:location")

        assert issue.severity == "error"
        assert issue.message == "Test error"
        assert issue.location == "test:location"

    def test_is_error(self):
        """Test is_error method."""
        error_issue = Issue("error", "Error message", "location")
        warning_issue = Issue("warning", "Warning message", "location")

        assert error_issue.is_error() is True
        assert warning_issue.is_error() is False

    def test_is_warning(self):
        """Test is_warning method."""
        error_issue = Issue("error", "Error message", "location")
        warning_issue = Issue("warning", "Warning message", "location")

        assert error_issue.is_warning() is False
        assert warning_issue.is_warning() is True

    def test_tuple_location(self):
        """Test Issue with tuple location."""
        issue = Issue(severity="warning", message="Test warning", location=("node", "port", "edge"))

        assert issue.location == ("node", "port", "edge")


class TestSchemaValidator:
    """Test suite for SchemaValidator protocol."""

    def test_protocol_implementation(self):
        """Test that objects can implement SchemaValidator protocol."""

        class MockValidator:
            def validate_payload(self, model, payload):
                return None

        validator = MockValidator()
        assert isinstance(validator, SchemaValidator)

    def test_protocol_validation(self):
        """Test protocol validation behavior."""

        class MockValidator:
            def validate_payload(self, model, payload):
                if payload.get("invalid"):
                    return Issue("error", "Invalid payload", "test")
                return None

        validator = MockValidator()

        # Valid payload
        result = validator.validate_payload({}, {"valid": True})
        assert result is None

        # Invalid payload
        result = validator.validate_payload({}, {"invalid": True})
        assert isinstance(result, Issue)
        assert result.severity == "error"


class TestValidatePorts:
    """Test suite for validate_ports function."""

    def create_mock_node(
        self,
        inputs_dict=None,
        outputs_dict=None,
        inputs_callable=True,
        outputs_callable=True,
    ):
        """Create a mock node for testing."""
        node = Mock()
        node.__class__.__name__ = "TestNode"

        if inputs_callable:
            node.inputs = Mock(return_value=inputs_dict or {})
        else:
            node.inputs = inputs_dict

        if outputs_callable:
            node.outputs = Mock(return_value=outputs_dict or {})
        else:
            node.outputs = outputs_dict

        return node

    def test_valid_node_ports(self):
        """Test validation of valid node ports."""
        node = self.create_mock_node(
            inputs_dict={"input1": Mock(), "input2": Mock()}, outputs_dict={"output1": Mock()}
        )

        issues = validate_ports(node)
        assert len(issues) == 0

    def test_non_dict_inputs(self):
        """Test validation when inputs() returns non-dict."""
        node = self.create_mock_node(inputs_dict="not_a_dict")

        issues = validate_ports(node)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "inputs() must return a dict" in issues[0].message

    def test_non_dict_outputs(self):
        """Test validation when outputs() returns non-dict."""
        node = self.create_mock_node(outputs_dict="not_a_dict")

        issues = validate_ports(node)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "outputs() must return a dict" in issues[0].message

    def test_non_string_port_names(self):
        """Test validation when port names are not strings."""
        node = self.create_mock_node(
            inputs_dict={123: Mock(), "valid": Mock()},
            outputs_dict={"output1": Mock(), 456: Mock()},
        )

        issues = validate_ports(node)
        assert len(issues) == 2

        # Should have errors for both non-string port names
        error_messages = [issue.message for issue in issues]
        assert any("Port name must be string" in msg for msg in error_messages)

    def test_missing_inputs_method(self):
        """Test validation when node has no inputs method."""
        node = Mock()
        node.__class__.__name__ = "TestNode"
        # Remove inputs and outputs methods to simulate missing methods
        if hasattr(node, "inputs"):
            delattr(node, "inputs")
        if hasattr(node, "outputs"):
            delattr(node, "outputs")

        issues = validate_ports(node)
        assert len(issues) == 0  # Should handle gracefully

    def test_exception_handling(self):
        """Test that exceptions during validation are caught."""
        node = Mock()
        node.__class__.__name__ = "TestNode"
        node.inputs.side_effect = Exception("Test exception")

        issues = validate_ports(node)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "Failed to validate ports" in issues[0].message


class TestValidateConnection:
    """Test suite for validate_connection function."""

    def test_valid_connection(self):
        """Test validation of valid connection."""
        src_spec = Mock()
        dst_spec = Mock()

        issue = validate_connection(src_spec, dst_spec)
        assert issue is None

    def test_none_src_spec(self):
        """Test validation when source spec is None."""
        issue = validate_connection(None, Mock())

        assert isinstance(issue, Issue)
        assert issue.severity == "error"
        assert "Port specifications cannot be None" in issue.message

    def test_none_dst_spec(self):
        """Test validation when destination spec is None."""
        issue = validate_connection(Mock(), None)

        assert isinstance(issue, Issue)
        assert issue.severity == "error"
        assert "Port specifications cannot be None" in issue.message

    def test_both_none(self):
        """Test validation when both specs are None."""
        issue = validate_connection(None, None)

        assert isinstance(issue, Issue)
        assert issue.severity == "error"


class TestValidateGraph:
    """Test suite for validate_graph function."""

    def create_mock_subgraph(
        self,
        nodes=None,
        edges=None,
        exposed_inputs=None,
        exposed_outputs=None,
    ):
        """Create a mock subgraph for testing."""
        subgraph = Mock()
        subgraph.__class__.__name__ = "TestSubgraph"

        if nodes is not None:
            subgraph._nodes = nodes
        if edges is not None:
            subgraph._edges = edges
        if exposed_inputs is not None:
            subgraph._exposed_inputs = exposed_inputs
        if exposed_outputs is not None:
            subgraph._exposed_outputs = exposed_outputs

        return subgraph

    def test_valid_subgraph(self):
        """Test validation of valid subgraph."""
        node1 = Mock()
        node1.name = "node1"
        node2 = Mock()
        node2.name = "node2"

        subgraph = self.create_mock_subgraph(
            nodes=[node1, node2], exposed_inputs=["input1"], exposed_outputs=["output1"]
        )

        issues = validate_graph(subgraph)
        # May have some issues but should not crash
        assert isinstance(issues, list)

    def test_duplicate_node_names(self):
        """Test validation with duplicate node names."""
        node1 = Mock()
        node1.name = "duplicate"
        node2 = Mock()
        node2.name = "duplicate"

        subgraph = self.create_mock_subgraph(nodes=[node1, node2])

        issues = validate_graph(subgraph)

        # Should find duplicate name error
        error_issues = [issue for issue in issues if issue.is_error()]
        assert any("Duplicate node name" in issue.message for issue in error_issues)

    def test_invalid_edge_capacity(self):
        """Test validation with invalid edge capacity."""
        edge = Mock()
        edge.capacity = 0  # Invalid - should be positive

        subgraph = self.create_mock_subgraph(
            nodes=[], edges=[edge]  # Empty nodes list to avoid iteration issues
        )

        issues = validate_graph(subgraph)

        # Should find capacity error
        error_issues = [issue for issue in issues if issue.is_error()]
        assert any("capacity must be positive" in issue.message for issue in error_issues)

    def test_invalid_exposed_port_names(self):
        """Test validation with invalid exposed port names."""
        subgraph = self.create_mock_subgraph(
            nodes=[],  # Empty nodes list to avoid iteration issues
            edges=[],  # Empty edges list to avoid iteration issues
            exposed_inputs=["", "  ", "valid_input"],
            exposed_outputs=["valid_output", ""],
        )

        issues = validate_graph(subgraph)

        # Should find warning issues for invalid port names
        # "" and "  " should both trigger warnings (3 total: 2 inputs + 1 output)
        warning_issues = [issue for issue in issues if issue.is_warning()]
        assert len(warning_issues) == 3  # Exactly 3 invalid names

    def test_exception_handling(self):
        """Test that exceptions during validation are caught."""
        subgraph = Mock()
        subgraph.__class__.__name__ = "TestSubgraph"
        subgraph._nodes = Mock(side_effect=Exception("Test exception"))

        issues = validate_graph(subgraph)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "Failed to validate graph" in issues[0].message

    def test_missing_attributes(self):
        """Test validation when subgraph is missing expected attributes."""
        subgraph = Mock()
        subgraph.__class__.__name__ = "TestSubgraph"
        # No _nodes, _edges, etc.

        issues = validate_graph(subgraph)
        # Should handle gracefully
        assert isinstance(issues, list)


class TestPydanticAdapter:
    """Test suite for PydanticAdapter class."""

    def test_init_without_pydantic(self):
        """Test adapter initialization when Pydantic is not available."""
        # This will use the real PydanticAdapter which may or may not have pydantic
        adapter = PydanticAdapter()
        assert hasattr(adapter, "_pydantic")

    def test_validate_without_pydantic(self):
        """Test validation when Pydantic is not available."""
        adapter = PydanticAdapter()
        adapter._pydantic = None  # Simulate missing pydantic

        result = adapter.validate_payload(Mock(), {"test": "data"})

        assert isinstance(result, Issue)
        assert result.severity == "warning"
        assert "Pydantic not available" in result.message

    @pytest.mark.skipif(
        True,
        reason="Pydantic integration test - would require pydantic dependency",
    )
    def test_validate_with_pydantic(self):
        """Test validation with actual Pydantic model."""
        # This test would require pydantic to be installed
        # Skipped to avoid adding test dependencies
        pass

    def test_validation_exception_handling(self):
        """Test that validation exceptions are caught."""
        adapter = PydanticAdapter()

        # Mock pydantic to raise exception
        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        mock_model.model_validate.side_effect = Exception("Validation failed")

        # Mock that pydantic is available
        adapter._pydantic = Mock()

        result = adapter.validate_payload(mock_model, {"test": "data"})

        assert isinstance(result, Issue)
        assert result.severity == "error"
        assert "Schema validation failed" in result.message


class TestIntegration:
    """Integration tests for validation utilities."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Create a realistic mock setup
        node = Mock()
        node.__class__.__name__ = "ProcessorNode"
        node.inputs = Mock(return_value={"input": Mock()})
        node.outputs = Mock(return_value={"output": Mock()})

        edge = Mock()
        edge.capacity = 100

        subgraph = Mock()
        subgraph.__class__.__name__ = "TestPipeline"
        subgraph._nodes = [node]
        subgraph._edges = [edge]
        subgraph._exposed_inputs = ["pipeline_input"]
        subgraph._exposed_outputs = ["pipeline_output"]

        # Run all validations
        port_issues = validate_ports(node)
        connection_issue = validate_connection(Mock(), Mock())
        graph_issues = validate_graph(subgraph)

        # Should all succeed
        assert len(port_issues) == 0
        assert connection_issue is None
        assert isinstance(graph_issues, list)

    def test_issue_severity_filtering(self):
        """Test filtering issues by severity."""
        # Create issues of different severities
        issues = [
            Issue("error", "Error 1", "loc1"),
            Issue("warning", "Warning 1", "loc2"),
            Issue("error", "Error 2", "loc3"),
            Issue("warning", "Warning 2", "loc4"),
        ]

        errors = [issue for issue in issues if issue.is_error()]
        warnings = [issue for issue in issues if issue.is_warning()]

        assert len(errors) == 2
        assert len(warnings) == 2

        assert all(issue.severity == "error" for issue in errors)
        assert all(issue.severity == "warning" for issue in warnings)
