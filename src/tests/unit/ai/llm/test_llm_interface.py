"""
Tests for the LLM interface component.
Following TDD principles - these tests define the expected behavior.

Note: This test file was originally designed for the llama.cpp implementation.
It has been superseded by test_transformers_interface.py which tests the current
HuggingFace Transformers-based implementation. These tests are kept for reference
but marked as skipped.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import configurations
from src.config.ai_config import LLMConfig


@pytest.fixture
def mock_llama_cpp():
    """Mock the llama_cpp module"""
    mock_module = MagicMock()
    mock_llama = MagicMock()
    mock_module.Llama.return_value = mock_llama

    # Set up the mock to return a valid response
    mock_response = {
        "choices": [{"text": "This is a test response", "finish_reason": "stop"}]
    }
    mock_llama.return_value = mock_response

    # Mock the tokenize method
    mock_llama.tokenize.return_value = [1, 2, 3, 4, 5]

    with patch.dict("sys.modules", {"llama_cpp": mock_module}):
        yield mock_module, mock_llama


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return LLMConfig(
        model_path="fake_model_path.gguf",
        context_size=1024,
        temperature=0.7,
        top_p=0.9,
        max_tokens=100,
        metal_enabled=False,
    )


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_initialization(mock_llama_cpp, test_config):
    """Test that the LLM interface initializes correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    llm = LLMInterface(config=test_config)
    assert llm.config == test_config
    assert llm._llm is None  # Should be lazy-loaded


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_model_loading(mock_llama_cpp, test_config):
    """Test that the model is loaded correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    # Force model loading
    llm._load_model()

    # Check that the model was loaded with the correct parameters
    mock_module.Llama.assert_called_once_with(
        model_path=test_config.model_path,
        n_ctx=test_config.context_size,
        n_batch=512,
        n_gpu_layers=0,  # Metal is disabled in test_config
        verbose=False,
    )

    assert llm._llm is not None


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_generate(mock_llama_cpp, test_config):
    """Test that the generate method works correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    result = llm.generate("Test prompt")

    # Check that the model was called with the correct parameters
    mock_llama.assert_called_once()

    # Check that the response was processed correctly
    assert isinstance(result, str)
    assert result == "This is a test response"


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_generate_with_params(mock_llama_cpp, test_config):
    """Test generating with custom parameters"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    result = llm.generate(
        "Test prompt", temperature=0.5, max_tokens=200, stop=["stop1", "stop2"]
    )

    # Using a list for args would match any positional arguments
    # For the first positional arg (prompt), we expect "Test prompt"
    prompt_arg = mock_llama.call_args[0][0]
    assert prompt_arg == "Test prompt"

    # Check the keyword arguments
    kwargs = mock_llama.call_args[1]
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_tokens"] == 200
    assert kwargs["stop"] == ["stop1", "stop2"]


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_tokenize(mock_llama_cpp, test_config):
    """Test that the tokenize method works correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    tokens = llm.tokenize("Test text")

    # Check that the tokenize method of the model was called
    mock_llama.tokenize.assert_called_once()

    # Check that the method returns what the model's tokenize method returns
    assert tokens == [1, 2, 3, 4, 5]


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_get_token_count(mock_llama_cpp, test_config):
    """Test that the get_token_count method works correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    count = llm.get_token_count("Test text")

    # Check that the tokenize method of the model was called
    mock_llama.tokenize.assert_called_once()

    # Check that the method returns the correct count
    assert count == 5


@pytest.mark.skip(
    reason="Implementation migrated from llama.cpp to HuggingFace Transformers"
)
def test_llm_streaming(mock_llama_cpp, test_config):
    """Test that the streaming functionality works correctly"""
    from src.ai.llm.llm_interface import LLMInterface

    mock_module, mock_llama = mock_llama_cpp
    llm = LLMInterface(config=test_config)

    # Mock a streaming response
    mock_stream = [
        {"choices": [{"text": "This"}]},
        {"choices": [{"text": " is"}]},
        {"choices": [{"text": " a"}]},
        {"choices": [{"text": " test"}]},
    ]
    mock_llama.return_value = mock_stream

    stream = llm.generate("Test prompt", stream=True)

    # Check that the model was called with the stream parameter
    assert mock_llama.call_args[1]["stream"] is True

    # Check that the stream is returned as is
    assert stream == mock_stream
