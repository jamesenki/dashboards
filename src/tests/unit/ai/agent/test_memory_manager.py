"""
Unit tests for the Memory Manager component of the Agent Framework.
Following TDD principles - these tests define the expected behavior.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.config.ai_config import AgentConfig


@pytest.fixture
def mock_vector_store():
    """Mock the vector store"""
    mock = MagicMock()
    mock.add_documents.return_value = ["memory1", "memory2", "memory3"]
    mock.query_by_text.return_value = [
        {
            "document": "Past conversation about water heater temperature",
            "metadata": {"timestamp": time.time() - 3600, "type": "conversation"},
            "score": 0.92,
        },
        {
            "document": "User prefers concise answers",
            "metadata": {"timestamp": time.time() - 7200, "type": "preference"},
            "score": 0.85,
        },
    ]
    return mock


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return AgentConfig(
        planning_steps=3, max_iterations=5, reflection_enabled=True, memory_size=10
    )


def test_memory_manager_initialization(test_config, mock_vector_store):
    """Test that the memory manager initializes correctly"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    assert memory_manager.config == test_config
    assert memory_manager.vector_store == mock_vector_store
    assert memory_manager.max_memories == test_config.memory_size


def test_store_interaction(test_config, mock_vector_store):
    """Test storing a user interaction"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    query = "How do I adjust the temperature on my water heater?"
    response = "You can adjust the temperature using the dial on the front panel."

    memory_manager.store_interaction(query, response)

    # Verify the vector store was called to add the interaction
    mock_vector_store.add_documents.assert_called_once()

    # Check that the document and metadata were properly constructed
    args, kwargs = mock_vector_store.add_documents.call_args
    documents, metadata = args

    # Document should combine query and response
    assert query in documents[0]
    assert response in documents[0]

    # Metadata should include timestamp and type
    assert metadata[0]["type"] == "interaction"
    assert "timestamp" in metadata[0]


def test_store_reflection(test_config, mock_vector_store):
    """Test storing a reflection"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    reflection = "User seems to be a homeowner with limited technical knowledge."

    memory_manager.store_reflection(reflection)

    # Verify the vector store was called to add the reflection
    mock_vector_store.add_documents.assert_called_once()

    # Check that the document and metadata were properly constructed
    args, kwargs = mock_vector_store.add_documents.call_args
    documents, metadata = args

    # Document should be the reflection
    assert reflection == documents[0]

    # Metadata should include timestamp and type
    assert metadata[0]["type"] == "reflection"
    assert "timestamp" in metadata[0]


def test_store_preference(test_config, mock_vector_store):
    """Test storing a user preference"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    preference = "User prefers detailed technical explanations."

    memory_manager.store_preference(preference)

    # Verify the vector store was called to add the preference
    mock_vector_store.add_documents.assert_called_once()

    # Check that the document and metadata were properly constructed
    args, kwargs = mock_vector_store.add_documents.call_args
    documents, metadata = args

    # Document should be the preference
    assert preference == documents[0]

    # Metadata should include timestamp and type
    assert metadata[0]["type"] == "preference"
    assert "timestamp" in metadata[0]


def test_get_relevant_memories(test_config, mock_vector_store):
    """Test retrieving relevant memories for a query"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    query = "What's the ideal temperature for a water heater?"

    memories = memory_manager.get_relevant_memories(query)

    # Verify the vector store was called to query for relevant memories
    mock_vector_store.query_by_text.assert_called_once_with(
        query, top_k=test_config.memory_size
    )

    # The result should be the documents from the query results
    assert isinstance(memories, list)
    assert len(memories) == 2
    assert "Past conversation about water heater temperature" in memories[0]
    assert "User prefers concise answers" in memories[1]


def test_get_relevant_memories_with_types(test_config, mock_vector_store):
    """Test retrieving memories of specific types"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    query = "What's the ideal temperature for a water heater?"
    memory_types = ["preference"]

    memories = memory_manager.get_relevant_memories(query, memory_types)

    # Verify the vector store was called with the right filter
    mock_vector_store.query_by_text.assert_called_once()
    args, kwargs = mock_vector_store.query_by_text.call_args

    # Check that the query and top_k were passed correctly
    assert args[0] == query
    assert kwargs["top_k"] == test_config.memory_size

    # Check that the filter includes the specified memory types
    filter_criteria = kwargs["filter_criteria"]
    assert filter_criteria["type"] == memory_types

    # The result should be the documents from the query results
    assert isinstance(memories, list)
    assert len(memories) == 2


def test_clear_older_than(test_config, mock_vector_store):
    """Test clearing memories older than a certain time"""
    from src.ai.agent.memory_manager import MemoryManager

    memory_manager = MemoryManager(config=test_config, vector_store=mock_vector_store)

    # Mock the vector store to return IDs of memories that match the filter
    mock_vector_store.query_by_text.return_value = [
        {"metadata": {"id": "old_memory1"}, "score": 1.0},
        {"metadata": {"id": "old_memory2"}, "score": 0.9},
    ]

    # Mock vector store delete method
    mock_vector_store.delete_documents = MagicMock()

    # Clear memories older than 24 hours
    timestamp = time.time() - (24 * 3600)  # 24 hours ago
    memory_manager.clear_older_than(timestamp)

    # Verify the vector store was called to find and delete old memories
    mock_vector_store.query_by_text.assert_called_once()

    # Verify delete was called with the right IDs
    if hasattr(mock_vector_store, "delete_documents"):
        mock_vector_store.delete_documents.assert_called_once_with(
            ["old_memory1", "old_memory2"]
        )
