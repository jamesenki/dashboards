"""
Tests for the LLM interface component using Transformers.
Following TDD principles - these tests define the expected behavior.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the configuration
from src.config.ai_config import LLMConfig

# Mock modules before importing the implementation
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["transformers.AutoTokenizer"] = MagicMock()
sys.modules["transformers.AutoModelForCausalLM"] = MagicMock()
sys.modules["transformers.TextIteratorStreamer"] = MagicMock()

# Now import our implementation
from src.ai.llm.llm_interface import LLMInterface


@pytest.fixture
def mock_transformers():
    """Mock the transformers module for testing"""
    # Create mock objects
    mock_tokenizer = MagicMock()
    # Make encode return a tensor-like object with a structure that matches what the implementation expects
    mock_tensor = MagicMock()
    mock_tensor.__getitem__.return_value = [1, 2, 3, 4, 5]  # This represents the tokens
    mock_tokenizer.encode.return_value = mock_tensor
    mock_tokenizer.decode.return_value = "This is a test response"
    mock_tokenizer.eos_token_id = 50256

    mock_model = MagicMock()
    mock_output = MagicMock()
    # Structure output to match what our interface expects
    mock_output.__getitem__.return_value = mock_output
    mock_output.__getitem__.return_value = [6, 7, 8, 9, 10]  # Generated token IDs
    mock_model.generate.return_value = mock_output

    # Set up mocks in the already-mocked modules
    transformers = sys.modules["transformers"]
    transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
    transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model

    # Setup torch mocks
    torch = sys.modules["torch"]
    torch.backends.mps.is_available.return_value = False
    torch.no_grad.return_value.__enter__.return_value = None
    torch.no_grad.return_value.__exit__.return_value = None
    torch.float16 = "float16"

    # Mock streamer
    mock_streamer = MagicMock()
    mock_streamer.__iter__.return_value = ["This", " is", " a", " test", " response"]
    transformers.TextIteratorStreamer.return_value = mock_streamer

    return {
        "tokenizer": mock_tokenizer,
        "model": mock_model,
        "torch": torch,
        "streamer": mock_streamer,
        "transformers": transformers,
    }


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return LLMConfig(
        model_path="gpt2",  # Using a HF model ID for testing
        context_size=1024,
        temperature=0.7,
        top_p=0.9,
        max_tokens=100,
        metal_enabled=False,
    )


def test_llm_initialization(test_config):
    """Test that the LLM interface initializes correctly"""
    llm = LLMInterface(config=test_config)
    assert llm.config == test_config
    assert llm._llm is None  # Should be lazy-loaded
    assert llm._tokenizer is None  # Should be lazy-loaded


def test_llm_model_loading(mock_transformers, test_config):
    """Test that the model is loaded correctly"""
    llm = LLMInterface(config=test_config)

    # Force model loading
    llm._load_model()

    # Check that the tokenizer was loaded with the correct model ID
    assert (
        mock_transformers["transformers"].AutoTokenizer.from_pretrained.call_count >= 1
    )
    # Verify at least one call was made with the correct model path
    model_path_calls = [
        call
        for call in mock_transformers[
            "transformers"
        ].AutoTokenizer.from_pretrained.call_args_list
        if call[0][0] == test_config.model_path
    ]
    assert len(model_path_calls) >= 1

    # Check that the model was loaded with the correct parameters
    assert (
        mock_transformers[
            "transformers"
        ].AutoModelForCausalLM.from_pretrained.call_count
        >= 1
    )
    # Get the most recent call for parameter verification
    args, kwargs = mock_transformers[
        "transformers"
    ].AutoModelForCausalLM.from_pretrained.call_args_list[-1]
    assert args[0] == test_config.model_path
    assert kwargs["torch_dtype"] == "float16"
    assert kwargs["low_cpu_mem_usage"] is True

    assert llm._llm is not None
    assert llm._tokenizer is not None


def test_llm_generate(mock_transformers, test_config):
    """Test that the generate method works correctly"""
    llm = LLMInterface(config=test_config)

    # We need to make sure our mocks properly handle the workflow in _generate_response
    result = llm.generate("Test prompt")

    # Check that the tokenizer was used to encode the prompt
    mock_transformers["tokenizer"].encode.assert_called_with(
        "Test prompt", return_tensors="pt"
    )

    # Check that the model's generate method was called
    mock_transformers["model"].generate.assert_called_once()

    # Check that the response was processed correctly
    assert isinstance(result, str)
    assert result == "This is a test response"


def test_llm_generate_with_params(mock_transformers, test_config):
    """Test generating with custom parameters"""
    llm = LLMInterface(config=test_config)

    result = llm.generate(
        "Test prompt", temperature=0.5, max_tokens=200, stop=["stop1", "stop2"]
    )

    # Check that the model's generate method was called with the right parameters
    _, kwargs = mock_transformers["model"].generate.call_args
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_new_tokens"] == 200
    assert kwargs["do_sample"] is True  # Because temperature > 0

    # Response handling with stop sequences is tested separately
    assert result == "This is a test response"


def test_llm_tokenize(mock_transformers, test_config):
    """Test that the tokenize method works correctly"""
    # Set up a specific return value for this test
    mock_transformers["tokenizer"].encode.return_value = [1, 2, 3, 4, 5]

    llm = LLMInterface(config=test_config)
    tokens = llm.tokenize("Test text")

    # Check that the tokenize method of the model was called
    mock_transformers["tokenizer"].encode.assert_called_with("Test text")

    # Check that the method returns what the model's tokenize method returns
    assert tokens == [1, 2, 3, 4, 5]


def test_llm_get_token_count(mock_transformers, test_config):
    """Test that the get_token_count method works correctly"""
    # Set up mock to return an array with 5 elements
    mock_transformers["tokenizer"].encode.return_value = [1, 2, 3, 4, 5]

    llm = LLMInterface(config=test_config)
    count = llm.get_token_count("Test text")

    # Check that the tokenize method of the model was called
    mock_transformers["tokenizer"].encode.assert_called_with("Test text")

    # Check that the method returns the correct count
    assert count == 5


def test_llm_streaming(mock_transformers, test_config):
    """Test that the streaming functionality works correctly"""
    llm = LLMInterface(config=test_config)

    stream = llm.generate("Test prompt", stream=True)

    # Check that a TextIteratorStreamer was created
    assert mock_transformers["transformers"].TextIteratorStreamer.called

    # Iterate through the stream to verify it works
    tokens = []
    for item in stream:
        tokens.append(item["choices"][0]["text"])
    assert len(tokens) > 0  # We should get some tokens

    # Check that our streamer was used in generate kwargs
    _, kwargs = mock_transformers["model"].generate.call_args
    assert "streamer" in kwargs
