"""Unit tests for SmokeTestNode node."""

import pytest

from smoke_test.smoke_test_node import SmokeTestNode
from arachne.core.message import Message


class TestSmokeTestNode:
    """Test suite for SmokeTestNode."""
    
    def test_node_creation(self):
        """Test basic node instantiation."""
        node = SmokeTestNode()
        assert node.name() == "smoke_test_node"
    
    def test_port_definitions(self):
        """Test input and output port definitions."""
        node = SmokeTestNode()
        
        inputs = node.inputs()
        outputs = node.outputs()
        
        assert isinstance(inputs, dict)
        assert isinstance(outputs, dict)
        
        # TODO: Add specific port validation tests
        # assert "expected_input" in inputs
        # assert "expected_output" in outputs
    
    @pytest.mark.asyncio
    async def test_lifecycle_hooks(self):
        """Test node lifecycle hooks can be called."""
        node = SmokeTestNode()
        
        # Should not raise exceptions
        await node.on_start()
        await node.on_tick()
        await node.on_stop()
    
    @pytest.mark.asyncio 
    async def test_message_processing(self):
        """Test basic message processing."""
        node = SmokeTestNode()
        
        # Create test message
        message = Message.create({"test": "data"})
        
        # Should not raise exceptions
        await node.on_message("test_port", message)
        
        # TODO: Add specific message processing tests
        # result = await node.process_data(message.payload)
        # assert result == expected_result
    
    def test_process_data(self):
        """Test main processing logic."""
        node = SmokeTestNode()
        
        # TODO: Add specific data processing tests
        test_data = {"test": "input"}
        result = node.process_data(test_data)
        
        # Currently just passes through - update based on actual logic
        assert result == test_data
