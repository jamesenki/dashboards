"""
Unit tests for the Tool Registry component of the Agent Framework.
Following TDD principles - these tests define the expected behavior.
"""

from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from src.config.ai_config import AgentConfig


# Define a simple calculator tool function for testing
def calculator_tool(a: int, b: int, operation: str = "add") -> int:
    """A simple calculator tool for testing"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")


@pytest.fixture
def mock_vector_store():
    """Mock the vector store for tool descriptions"""
    mock = MagicMock()
    mock.query_by_text.return_value = [
        {
            "document": "knowledge_search: Search the knowledge base for information",
            "metadata": {"tool_name": "knowledge_search", "requires_params": True},
            "score": 0.95,
        },
        {
            "document": "calculator: Perform mathematical calculations",
            "metadata": {"tool_name": "calculator", "requires_params": True},
            "score": 0.85,
        },
    ]
    return mock


@pytest.fixture
def mock_llm_interface():
    """Mock the LLM interface"""
    mock = MagicMock()

    # For parse_tool_params test
    mock.generate.return_value = """
    {
        "a": 5,
        "b": 3,
        "operation": "multiply"
    }
    """

    return mock


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return AgentConfig(
        planning_steps=3, max_iterations=5, reflection_enabled=True, memory_size=10
    )


def test_tool_registry_initialization(
    test_config, mock_vector_store, mock_llm_interface
):
    """Test that the tool registry initializes correctly"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    assert registry.config == test_config
    assert registry.vector_store == mock_vector_store
    assert registry.llm_interface == mock_llm_interface
    assert registry.tools == {}


def test_register_tool(test_config, mock_vector_store, mock_llm_interface):
    """Test registering a tool with the registry"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    tool_name = "calculator"
    tool_description = "Perform mathematical calculations with parameters: a, b, operation (add/subtract/multiply/divide)"

    registry.register_tool(
        name=tool_name, description=tool_description, func=calculator_tool
    )

    # Verify the tool was added to the registry
    assert tool_name in registry.tools
    assert registry.tools[tool_name]["func"] == calculator_tool
    assert registry.tools[tool_name]["description"] == tool_description

    # Verify the tool description was added to the vector store
    mock_vector_store.add_documents.assert_called_once()
    documents, metadatas = mock_vector_store.add_documents.call_args[0]

    assert documents[0] == f"{tool_name}: {tool_description}"
    assert metadatas[0]["tool_name"] == tool_name
    assert metadatas[0]["requires_params"] is True


def test_get_relevant_tools(test_config, mock_vector_store, mock_llm_interface):
    """Test getting relevant tools for a query"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    # Register a couple tools
    registry.register_tool(
        name="calculator",
        description="Perform mathematical calculations",
        func=calculator_tool,
    )

    query = "I need to calculate 5 plus 3"

    tools = registry.get_relevant_tools(query)

    # Verify the vector store was queried
    mock_vector_store.query_by_text.assert_called_once_with(query, top_k=5)

    # The result should be a list of tool names
    assert isinstance(tools, list)
    assert len(tools) == 2
    assert "knowledge_search" in tools
    assert "calculator" in tools


def test_execute_tool_with_params(test_config, mock_vector_store, mock_llm_interface):
    """Test executing a tool with parameters"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    # Register the calculator tool
    registry.register_tool(
        name="calculator",
        description="Perform mathematical calculations with parameters: a, b, operation (add/subtract/multiply/divide)",
        func=calculator_tool,
    )

    query = "What is 5 multiplied by 3?"
    tool_name = "calculator"

    result = registry.execute_tool(tool_name, query)

    # Verify the LLM was called to parse parameters
    mock_llm_interface.generate.assert_called_once()

    # The result should be the output of the calculator tool
    assert result == 15  # 5 * 3


def test_execute_tool_no_params(test_config, mock_vector_store, mock_llm_interface):
    """Test executing a tool that doesn't require parameters"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    # Define a simple no-parameter tool
    def current_time_tool():
        return "2025-04-03 10:00:00"

    # Register the tool
    registry.register_tool(
        name="current_time",
        description="Get the current time",
        func=current_time_tool,
        requires_params=False,
    )

    query = "What time is it?"
    tool_name = "current_time"

    result = registry.execute_tool(tool_name, query)

    # Verify the LLM was not called to parse parameters
    mock_llm_interface.generate.assert_not_called()

    # The result should be the output of the time tool
    assert result == "2025-04-03 10:00:00"


def test_parse_tool_params(test_config, mock_vector_store, mock_llm_interface):
    """Test parsing tool parameters from a query"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    query = "Multiply 5 by 3"
    tool_description = "Perform mathematical calculations with parameters: a, b, operation (add/subtract/multiply/divide)"

    params = registry._parse_tool_params(query, tool_description)

    # Verify the LLM was called with the right prompt
    mock_llm_interface.generate.assert_called_once()
    prompt = mock_llm_interface.generate.call_args[0][0]

    # The prompt should include the query and tool description
    assert query in prompt
    assert tool_description in prompt

    # The result should be the parsed parameters
    assert params["a"] == 5
    assert params["b"] == 3
    assert params["operation"] == "multiply"


def test_tool_error_handling(test_config, mock_vector_store, mock_llm_interface):
    """Test handling errors during tool execution"""
    from src.ai.agent.tool_registry import ToolRegistry

    registry = ToolRegistry(
        config=test_config,
        vector_store=mock_vector_store,
        llm_interface=mock_llm_interface,
    )

    # Define a tool that raises an exception
    def failing_tool():
        raise ValueError("Something went wrong")

    # Register the tool
    registry.register_tool(
        name="failing_tool",
        description="A tool that will fail",
        func=failing_tool,
        requires_params=False,
    )

    query = "Execute the failing tool"
    tool_name = "failing_tool"

    result = registry.execute_tool(tool_name, query)

    # The result should be an error message
    assert isinstance(result, str)
    assert "Error executing tool" in result
    assert "Something went wrong" in result
