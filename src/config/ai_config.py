"""
Configuration for the AI infrastructure components.
Optimized for Mac M1/M2 hardware.
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"


class LLMConfig(BaseModel):
    """Configuration for the LLM component"""

    model_path: str = Field(
        default=str(MODELS_DIR / "llm" / "llama-3-8b.Q4_K_M.gguf"),
        description="Path to the quantized LLM model",
    )
    context_size: int = Field(
        default=2048, description="Context window size for the LLM"
    )
    temperature: float = Field(default=0.7, description="Temperature for LLM sampling")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    max_tokens: int = Field(
        default=512, description="Maximum number of tokens to generate"
    )
    metal_enabled: bool = Field(
        default=True,
        description="Whether to enable Metal acceleration on Apple Silicon",
    )


class VectorDBConfig(BaseModel):
    """Configuration for the Vector Database component"""

    db_type: str = Field(default="chroma", description="Type of vector database to use")
    embedding_model: str = Field(
        default=str(MODELS_DIR / "embeddings" / "bge-small-en"),
        description="Path to the embedding model",
    )
    persist_directory: str = Field(
        default=str(DATA_DIR / "vectordb"),
        description="Directory to persist vector database",
    )
    collection_name: str = Field(
        default="iotsphere_knowledge",
        description="Name of the vector database collection",
    )


class AgentConfig(BaseModel):
    """Configuration for the Agent Framework"""

    planning_steps: int = Field(
        default=3, description="Number of planning steps for the agent"
    )
    max_iterations: int = Field(
        default=5, description="Maximum number of iterations for the agent"
    )
    reflection_enabled: bool = Field(
        default=True, description="Whether to enable agent reflection"
    )
    memory_size: int = Field(
        default=10, description="Number of past interactions to keep in memory"
    )


class SearchConfig(BaseModel):
    """Configuration for the Internet Search component"""

    provider: str = Field(default="duckduckgo", description="Search provider to use")
    cache_ttl: int = Field(
        default=86400,  # 24 hours
        description="Time-to-live for cached search results in seconds",
    )
    rate_limit: int = Field(default=10, description="Maximum requests per minute")
    max_results: int = Field(
        default=5, description="Maximum number of search results to return"
    )


class AIConfig(BaseModel):
    """Master configuration for all AI infrastructure components"""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)


# Default configuration
default_config = AIConfig()


def get_config() -> AIConfig:
    """Get the AI configuration, with potential environment overrides"""
    # TODO: Add environment variable overrides
    return default_config
