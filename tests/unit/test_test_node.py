"""Unit tests for TestNode node."""

import pytest

from test.nodes.test_node import TestNode
from arachne.core.message import Message


class TestTestNode:
    """Test suite for TestNode."""
    
    def test_node_creation(self):
        """Test basic node instantiation."""
        node = TestNode()
        assert node.name == "test_node"
    
    def test_port_definitions(self):
        """Test input and output port definitions."""
        node = TestNode()
        
        inputs = node.inputs
        outputs = node.outputs
        
        assert isinstance(inputs, list)
        assert isinstance(outputs, list)
        
        # TODO: Add specific port validation tests
        # assert any(p.name == "expected_input" for p in inputs)
        # assert any(p.name == "expected_output" for p in outputs)
    
    def test_lifecycle_hooks(self):
        """Test node lifecycle hooks can be called."""
        node = TestNode()
        
        # Should not raise exceptions
        node.on_start()
        node.on_tick()
        node.on_stop()
    
    def test_message_processing(self):
        """Test basic message processing."""
        node = TestNode()
        
        # Create test message
        message = Message.create({"test": "data"})
        
        # Should not raise exceptions
        node.on_message("test_port", message)
        
        # TODO: Add specific message processing tests
        # result = await node.process_data(message.payload)
        # assert result == expected_result
    
    def test_process_data(self):
        """Test main processing logic."""
        node = TestNode()
        
        # TODO: Add specific data processing tests
        test_data = {"test": "input"}
        result = node.process_data(test_data)
        
        # Currently just passes through - update based on actual logic
        assert result == test_data
