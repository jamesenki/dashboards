"""
Unit tests for integrating Water Heater tools with the Agent Framework Tool Registry.
Following TDD principles - these tests define the expected behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.agent.tool_registry import ToolRegistry
from src.ai.llm.llm_interface import LLMInterface
from src.ai.vector_db.vector_store import VectorStore
from src.config.ai_config import AgentConfig


@pytest.fixture
def mock_vector_store():
    """Mock the vector store."""
    store = MagicMock(spec=VectorStore)
    store.add_documents.return_value = ["doc1"]
    store.query_by_text.return_value = [
        {
            "document": "Tool description",
            "metadata": {"tool_name": "get_water_heater_info"},
        }
    ]
    return store


@pytest.fixture
def mock_llm_interface():
    """Mock the LLM interface."""
    llm = MagicMock(spec=LLMInterface)
    llm.generate.return_value = '{"device_id": "wh-123456"}'
    return llm


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return AgentConfig(
        model_name="test-model",
        embedding_model="test-embeddings",
        temperature=0.7,
        max_tokens=500,
        memory_size=10,
    )


def test_register_water_heater_tools():
    """Test that all water heater tools are registered in the Tool Registry."""
    # Import the function to register water heater tools
    from src.ai.agent.tools.register_tools import register_water_heater_tools
    from src.ai.agent.tools.water_heater_tools import (
        get_water_heater_info,
        get_water_heater_list,
        get_water_heater_maintenance_info,
        get_water_heater_telemetry,
        set_water_heater_mode,
        set_water_heater_temperature,
    )

    # Create mock objects
    mock_registry = MagicMock(spec=ToolRegistry)

    # Call the function to register tools
    register_water_heater_tools(mock_registry)

    # Verify that all tools were registered
    assert mock_registry.register_tool.call_count == 6

    # Check for specific calls to register each tool
    registered_tools = set()
    for call_args in mock_registry.register_tool.call_args_list:
        args, kwargs = call_args
        tool_name = kwargs.get("name") or args[0]
        registered_tools.add(tool_name)

    # Verify all tools are registered
    expected_tools = {
        "get_water_heater_info",
        "get_water_heater_list",
        "get_water_heater_telemetry",
        "set_water_heater_temperature",
        "set_water_heater_mode",
        "get_water_heater_maintenance_info",
    }

    assert registered_tools == expected_tools


def test_water_heater_tool_discovery():
    """Test that water heater tools can be discovered based on relevant queries."""
    # Import the function to register water heater tools
    from src.ai.agent.tools.register_tools import register_water_heater_tools

    # Create a real ToolRegistry with mocked dependencies
    registry = ToolRegistry(
        config=test_config(),
        vector_store=mock_vector_store(),
        llm_interface=mock_llm_interface(),
    )

    # Mock the register_tool method to avoid actual implementation
    with patch.object(registry, "register_tool") as mock_register:
        # Register the tools
        register_water_heater_tools(registry)

        # Mock has been called multiple times, restore it for testing
        registry.register_tool = MagicMock()

    # Test discovering tools with a relevant query
    relevant_tools = registry.get_relevant_tools(
        "What is the current temperature of my water heater?"
    )

    # Should find at least the info tool
    assert "get_water_heater_info" in relevant_tools


def test_water_heater_tool_execution():
    """Test that water heater tools can be executed through the Tool Registry."""
    from src.ai.agent.tools.water_heater_tools import get_water_heater_info

    # Create a real ToolRegistry with mocked dependencies
    registry = ToolRegistry(
        config=test_config(),
        vector_store=mock_vector_store(),
        llm_interface=mock_llm_interface(),
    )

    # Register a real tool
    registry.register_tool(
        name="get_water_heater_info",
        description="Get information about a water heater by ID",
        func=get_water_heater_info,
    )

    # Mock the water heater service for execution testing
    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_water_heater.return_value = {
            "id": "wh-123456",
            "name": "Master Bath Water Heater",
            "current_temperature": 48.5,
            "target_temperature": 50.0,
            "status": "active",
        }
        mock_get_service.return_value = mock_service

        # Execute the tool through the registry
        result = registry.execute_tool(
            "get_water_heater_info", "What is the status of water heater wh-123456?"
        )

        # Verify the tool was executed and returned expected results
        assert "Master Bath Water Heater" in result
        assert "48.5" in result
        assert "50.0" in result
