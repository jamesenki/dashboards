"""
Unit tests for the Cognitive Controller component of the Agent Framework.
Following TDD principles - these tests define the expected behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config.ai_config import AgentConfig


@pytest.fixture
def mock_planning_module():
    """Mock the planning module"""
    mock = MagicMock()
    mock.create_plan.return_value = [
        "Step 1: Analyze the query",
        "Step 2: Search knowledge base",
        "Step 3: Formulate response",
    ]
    return mock


@pytest.fixture
def mock_memory_manager():
    """Mock the memory manager"""
    mock = MagicMock()
    mock.get_relevant_memories.return_value = [
        "Previous interaction about water heaters",
        "User preference for concise answers",
    ]
    return mock


@pytest.fixture
def mock_tool_registry():
    """Mock the tool registry"""
    mock = MagicMock()
    mock.get_relevant_tools.return_value = ["knowledge_search", "calculator"]
    mock.execute_tool.return_value = "Tool execution result"
    return mock


@pytest.fixture
def mock_llm_interface():
    """Mock the LLM interface"""
    mock = MagicMock()
    mock.generate.return_value = "Generated LLM response"
    return mock


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return AgentConfig(
        planning_steps=3, max_iterations=5, reflection_enabled=True, memory_size=10
    )


def test_cognitive_controller_initialization(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test that the cognitive controller initializes correctly"""
    from src.ai.agent.cognitive_controller import CognitiveController

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    assert controller.config == test_config
    assert controller.planning_module == mock_planning_module
    assert controller.memory_manager == mock_memory_manager
    assert controller.tool_registry == mock_tool_registry
    assert controller.llm_interface == mock_llm_interface


def test_process_query_simple(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test processing a simple query that doesn't require tools"""
    from src.ai.agent.cognitive_controller import CognitiveController

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    # Setup mock to indicate no tools are needed
    mock_planning_module.should_use_tools.return_value = False

    result = controller.process_query("What is a water heater?")

    # Verify the right components were called
    mock_memory_manager.get_relevant_memories.assert_called_once()
    mock_planning_module.create_plan.assert_called_once()
    mock_llm_interface.generate.assert_called_once()

    # No tools should be used
    mock_tool_registry.execute_tool.assert_not_called()

    # The result should be the LLM response
    assert result == "Generated LLM response"


def test_process_query_with_tools(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test processing a query that requires tools"""
    from src.ai.agent.cognitive_controller import CognitiveController

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    # Setup mocks to indicate tools are needed
    mock_planning_module.should_use_tools.return_value = True
    mock_planning_module.get_required_tools.return_value = ["knowledge_search"]

    result = controller.process_query("What is the temperature of water heater #1234?")

    # Verify the right components were called
    mock_memory_manager.get_relevant_memories.assert_called_once()
    mock_planning_module.create_plan.assert_called_once()
    mock_tool_registry.get_relevant_tools.assert_called_once()
    mock_tool_registry.execute_tool.assert_called_once()
    mock_llm_interface.generate.assert_called_once()

    # The result should be the LLM response
    assert result == "Generated LLM response"


def test_iterative_refinement(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test that the controller can refine results over multiple iterations"""
    from src.ai.agent.cognitive_controller import CognitiveController

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    # Setup mock to simulate needing multiple iterations
    responses = ["Initial response", "Improved response", "Final detailed response"]
    mock_llm_interface.generate.side_effect = responses

    # Setup mock to indicate refinement is needed for first two calls
    mock_planning_module.needs_refinement.side_effect = [True, True, False]

    result = controller.process_query(
        "Give me detailed information about water heater efficiency",
        refine_results=True,
    )

    # Verify the LLM was called multiple times
    assert mock_llm_interface.generate.call_count == 3

    # The result should be the final LLM response
    assert result == "Final detailed response"


def test_reflection_when_enabled(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test that reflection happens when enabled in config"""
    from src.ai.agent.cognitive_controller import CognitiveController

    # Ensure reflection is enabled
    test_config.reflection_enabled = True

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    controller.process_query("How do I troubleshoot my water heater?")

    # Verify reflection was called
    mock_planning_module.reflect_on_response.assert_called_once()
    mock_memory_manager.store_reflection.assert_called_once()


def test_reflection_when_disabled(
    test_config,
    mock_planning_module,
    mock_memory_manager,
    mock_tool_registry,
    mock_llm_interface,
):
    """Test that reflection doesn't happen when disabled in config"""
    from src.ai.agent.cognitive_controller import CognitiveController

    # Disable reflection
    test_config.reflection_enabled = False

    controller = CognitiveController(
        config=test_config,
        planning_module=mock_planning_module,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
        llm_interface=mock_llm_interface,
    )

    controller.process_query("How do I troubleshoot my water heater?")

    # Verify reflection was not called
    mock_planning_module.reflect_on_response.assert_not_called()
    mock_memory_manager.store_reflection.assert_not_called()
