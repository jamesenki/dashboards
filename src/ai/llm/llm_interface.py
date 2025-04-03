"""
Interface for the LLM component of the AI infrastructure.
Optimized for Mac M1/M2 hardware using HuggingFace Transformers.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from src.config.ai_config import LLMConfig, get_config

logger = logging.getLogger(__name__)


class LLMInterface:
    """Interface for the LLM component using HuggingFace Transformers"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM interface with the given configuration"""
        self.config = config or get_config().llm
        self._llm = None
        self._tokenizer = None

    def _load_model(self):
        """Load the LLM model lazily"""
        if self._llm is not None and self._tokenizer is not None:
            return

        try:
            # Set environment variables for optimal performance on Mac M1/M2
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Determine if MPS (Metal Performance Shaders) is available
            device = (
                "mps"
                if torch.backends.mps.is_available() and self.config.metal_enabled
                else "cpu"
            )
            logger.info(f"Using device: {device}")

            # For testing purposes, we'll use a small model if the configured model isn't available
            model_id = self.config.model_path
            if not os.path.exists(model_id) and not model_id.startswith("huggingface/"):
                logger.info(
                    f"Model {model_id} not found locally, using a small test model instead"
                )
                model_id = "gpt2"  # Small model for testing

            logger.info(f"Loading LLM model: {model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)

            # Load in 8-bit for memory efficiency on Mac
            self._llm = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                device_map=device if device == "mps" else "auto",
            )

            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        stream: bool = False,
    ) -> Union[str, Iterator[str]]:
        """Generate text from the LLM based on the given prompt"""
        self._load_model()

        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens if max_tokens is not None else self.config.max_tokens

        logger.debug(f"Generating with prompt: {prompt[:50]}...")

        if stream:
            return self._stream_response(prompt, temp, max_tok, stop)
        else:
            return self._generate_response(prompt, temp, max_tok, stop)

    def _generate_response(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[List[str]],
    ) -> str:
        """Generate a complete response"""
        import torch

        input_ids = self._tokenizer.encode(prompt, return_tensors="pt")
        if torch.backends.mps.is_available() and self.config.metal_enabled:
            input_ids = input_ids.to("mps")

        # Set up generation parameters
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "pad_token_id": self._tokenizer.eos_token_id,
        }

        # Add top_p if it's in the config
        if hasattr(self.config, "top_p") and self.config.top_p < 1.0:
            gen_kwargs["top_p"] = self.config.top_p

        # Generate
        with torch.no_grad():
            output = self._llm.generate(input_ids, **gen_kwargs)

        # Decode the output, removing the prompt
        prompt_length = len(input_ids[0])
        response = self._tokenizer.decode(
            output[0][prompt_length:], skip_special_tokens=True
        )

        # Handle stop sequences if provided
        if stop:
            for stop_seq in stop:
                if stop_seq in response:
                    response = response[: response.find(stop_seq)]

        return response.strip()

    def _stream_response(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[List[str]],
    ) -> Iterator[str]:
        """Stream the response token by token"""
        from threading import Thread

        import torch
        from transformers import TextIteratorStreamer

        input_ids = self._tokenizer.encode(prompt, return_tensors="pt")
        if torch.backends.mps.is_available() and self.config.metal_enabled:
            input_ids = input_ids.to("mps")

        # Create a streamer
        streamer = TextIteratorStreamer(
            self._tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        # Set up generation parameters
        gen_kwargs = {
            "input_ids": input_ids,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "streamer": streamer,
            "pad_token_id": self._tokenizer.eos_token_id,
        }

        # Add top_p if it's in the config
        if hasattr(self.config, "top_p") and self.config.top_p < 1.0:
            gen_kwargs["top_p"] = self.config.top_p

        # Start generation in a separate thread
        thread = Thread(target=self._llm.generate, kwargs=gen_kwargs)
        thread.start()

        # Create streamer response structure to match expected format
        class StreamResponse:
            def __init__(self, streamer, stop_sequences=None):
                self.streamer = streamer
                self.stop_sequences = stop_sequences or []
                self.buffer = ""

            def __iter__(self):
                for token in self.streamer:
                    self.buffer += token
                    for stop_seq in self.stop_sequences:
                        if stop_seq in self.buffer:
                            # Return everything up to the stop sequence
                            yield {
                                "choices": [
                                    {"text": self.buffer[: self.buffer.find(stop_seq)]}
                                ]
                            }
                            return
                    yield {"choices": [{"text": token}]}

        return StreamResponse(streamer, stop)

    def tokenize(self, text: str) -> List[int]:
        """Tokenize the given text"""
        self._load_model()
        return self._tokenizer.encode(text)

    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the given text"""
        tokens = self.tokenize(text)
        return len(tokens)
