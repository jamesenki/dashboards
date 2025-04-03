"""
Unit tests for the Planning Module component of the Agent Framework.
Following TDD principles - these tests define the expected behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config.ai_config import AgentConfig


@pytest.fixture
def mock_llm_interface():
    """Mock the LLM interface"""
    mock = MagicMock()

    # Setup mock for different LLM responses
    mock.generate.side_effect = [
        # For create_plan test
        "1. Understand the query\n2. Search knowledge base\n3. Formulate response",
        # For should_use_tools test - positive case
        "Yes, tools are needed to answer this query about specific device data.",
        # For should_use_tools test - negative case
        "No tools are needed for this general information query.",
        # For get_required_tools test
        "The tools needed are: knowledge_search, device_data_lookup",
        # For reflect_on_response test
        "The response was accurate but could provide more specific maintenance details.",
    ]

    return mock


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return AgentConfig(
        planning_steps=3, max_iterations=5, reflection_enabled=True, memory_size=10
    )


def test_planning_module_initialization(test_config, mock_llm_interface):
    """Test that the planning module initializes correctly"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    assert planner.config == test_config
    assert planner.llm_interface == mock_llm_interface


def test_create_plan(test_config, mock_llm_interface):
    """Test creating a plan for a given query"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    query = "How do water heaters work?"
    context = ["Previous discussion about heating efficiency", "User is a homeowner"]

    plan = planner.create_plan(query, context)

    # Verify the LLM was called to create a plan
    mock_llm_interface.generate.assert_called_once()
    args = mock_llm_interface.generate.call_args[0]

    # The prompt should include the query and context
    assert query in args[0]
    for ctx_item in context:
        assert ctx_item in args[0]

    # The result should be a list of steps
    assert isinstance(plan, list)
    assert len(plan) == 3
    assert plan[0] == "1. Understand the query"
    assert plan[1] == "2. Search knowledge base"
    assert plan[2] == "3. Formulate response"


def test_should_use_tools_positive(test_config, mock_llm_interface):
    """Test determining if tools should be used - positive case"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    query = "What is the current temperature of water heater #1234?"
    result = planner.should_use_tools(query)

    assert result is True


def test_should_use_tools_negative(test_config, mock_llm_interface):
    """Test determining if tools should be used - negative case"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    query = "What is a water heater?"
    result = planner.should_use_tools(query)

    assert result is False


def test_get_required_tools(test_config, mock_llm_interface):
    """Test identifying the specific tools needed for a query"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    query = "Check the temperature history for water heater #1234"
    available_tools = ["knowledge_search", "device_data_lookup", "maintenance_history"]

    tools = planner.get_required_tools(query, available_tools)

    # Verify the LLM was called
    mock_llm_interface.generate.assert_called()

    # The prompt should include the query and available tools
    args = mock_llm_interface.generate.call_args[0]
    assert query in args[0]
    for tool in available_tools:
        assert tool in args[0]

    # The result should be a list of tool names
    assert isinstance(tools, list)
    assert len(tools) == 2
    assert "knowledge_search" in tools
    assert "device_data_lookup" in tools


def test_needs_refinement(test_config, mock_llm_interface):
    """Test checking if a response needs further refinement"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    # Mock the LLM to indicate refinement is needed
    mock_llm_interface.generate.return_value = (
        "Yes, the response needs more detail about maintenance schedule."
    )

    query = "Tell me about water heater maintenance."
    response = "Water heaters should be maintained regularly."

    result = planner.needs_refinement(query, response)

    # Verify the LLM was called
    mock_llm_interface.generate.assert_called()

    # The prompt should include the query and response
    args = mock_llm_interface.generate.call_args[0]
    assert query in args[0]
    assert response in args[0]

    # The result should be a boolean
    assert result is True


def test_reflect_on_response(test_config, mock_llm_interface):
    """Test generating a reflection on the response"""
    from src.ai.agent.planning_module import PlanningModule

    planner = PlanningModule(config=test_config, llm_interface=mock_llm_interface)

    query = "How often should I maintain my water heater?"
    response = "You should flush your water heater annually."

    reflection = planner.reflect_on_response(query, response)

    # Verify the LLM was called
    mock_llm_interface.generate.assert_called()

    # The prompt should include the query and response
    args = mock_llm_interface.generate.call_args[0]
    assert query in args[0]
    assert response in args[0]

    # The result should be a string
    assert isinstance(reflection, str)
    assert "maintenance details" in reflection
