"""
Tests for the AI infrastructure configuration.
Following TDD principles - these tests define the expected behavior.
"""

import os
from pathlib import Path

import pytest

from src.config.ai_config import (
    AgentConfig,
    AIConfig,
    LLMConfig,
    SearchConfig,
    VectorDBConfig,
    get_config,
)


def test_config_initialization():
    """Test that the configuration initializes correctly"""
    config = get_config()
    assert isinstance(config, AIConfig)
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.vector_db, VectorDBConfig)
    assert isinstance(config.agent, AgentConfig)
    assert isinstance(config.search, SearchConfig)


def test_llm_config_values():
    """Test that the LLM configuration has expected values"""
    config = get_config()
    assert config.llm.context_size == 2048
    assert 0.0 <= config.llm.temperature <= 1.0
    assert 0.0 <= config.llm.top_p <= 1.0
    assert config.llm.max_tokens > 0


def test_vector_db_config_values():
    """Test that the vector database configuration has expected values"""
    config = get_config()
    assert config.vector_db.db_type in ["chroma", "qdrant"]
    assert "embeddings" in config.vector_db.embedding_model
    assert "vectordb" in config.vector_db.persist_directory


def test_agent_config_values():
    """Test that the agent configuration has expected values"""
    config = get_config()
    assert config.agent.planning_steps > 0
    assert config.agent.max_iterations > 0
    assert isinstance(config.agent.reflection_enabled, bool)
    assert config.agent.memory_size > 0


def test_search_config_values():
    """Test that the search configuration has expected values"""
    config = get_config()
    assert config.search.provider in ["duckduckgo", "serpapi", "bing"]
    assert config.search.cache_ttl > 0
    assert config.search.rate_limit > 0
    assert config.search.max_results > 0


def test_config_paths_exist():
    """Test that the paths in the configuration will exist after setup"""
    # Note: This test will pass after running the model download script
    config = get_config()
    base_dir = Path(__file__).parent.parent.parent.parent.parent

    models_dir = base_dir / "models"
    data_dir = base_dir / "data"

    assert models_dir.exists() or not Path(config.llm.model_path).is_absolute()
    assert (
        data_dir.exists() or not Path(config.vector_db.persist_directory).is_absolute()
    )
