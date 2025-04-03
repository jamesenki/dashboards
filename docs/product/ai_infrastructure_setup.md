# AI Infrastructure Setup Guide

This guide will help you set up the AI infrastructure components for the IoTSphere-Refactor project, optimized for development on Mac M1/M2 hardware.

## Setup Process

### 1. Environment Preparation

We recommend using a dedicated virtual environment for AI development:

```bash
# Create and activate a virtual environment
python -m venv venv_ai
source venv_ai/bin/activate

# Install core requirements first
pip install -r requirements.txt

# Install AI-specific requirements
pip install -r requirements.ai.txt
```

### 2. Model Download

Create a script to download the required models:

```bash
mkdir -p scripts/ai
```

#### Create Model Download Script

Create the following script at `scripts/ai/download_models.py`:

```python
#!/usr/bin/env python
"""
Download required LLM and embedding models for the AI infrastructure.
Optimized for Mac M1/M2 hardware.
"""

import os
import sys
import logging
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("model_downloader")

# Define model paths
MODELS_DIR = Path("./models")
LLM_DIR = MODELS_DIR / "llm"
EMBEDDING_DIR = MODELS_DIR / "embeddings"

# Ensure directories exist
LLM_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)

def download_llm_model():
    """Download a quantized LLM model optimized for Mac M1/M2"""
    logger.info("Downloading LLM model (this may take a while)...")

    try:
        model_path = hf_hub_download(
            repo_id="TheBloke/Llama-3-8B-GGUF",
            filename="llama-3-8b.Q4_K_M.gguf",
            local_dir=LLM_DIR,
            local_dir_use_symlinks=False
        )
        logger.info(f"LLM model downloaded to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to download LLM model: {e}")
        logger.info("Attempting to download backup model...")
        try:
            model_path = hf_hub_download(
                repo_id="TheBloke/Mistral-7B-v0.1-GGUF",
                filename="mistral-7b-v0.1.Q4_K_M.gguf",
                local_dir=LLM_DIR,
                local_dir_use_symlinks=False
            )
            logger.info(f"Backup LLM model downloaded to {model_path}")
            return model_path
        except Exception as e2:
            logger.error(f"Failed to download backup model: {e2}")
            return None

def download_embedding_model():
    """Download a lightweight embedding model optimized for Mac M1/M2"""
    logger.info("Downloading embedding model...")

    try:
        model_dir = snapshot_download(
            repo_id="BAAI/bge-small-en-v1.5",
            local_dir=EMBEDDING_DIR / "bge-small-en",
            local_dir_use_symlinks=False,
            ignore_patterns=["*.safetensors", "*.bin", "*.pt"]
        )
        logger.info(f"Embedding model downloaded to {model_dir}")
        return model_dir
    except Exception as e:
        logger.error(f"Failed to download embedding model: {e}")
        logger.info("Attempting to download backup embedding model...")
        try:
            model_dir = snapshot_download(
                repo_id="sentence-transformers/all-MiniLM-L6-v2",
                local_dir=EMBEDDING_DIR / "all-MiniLM-L6-v2",
                local_dir_use_symlinks=False,
                ignore_patterns=["*.safetensors", "*.bin", "*.pt"]
            )
            logger.info(f"Backup embedding model downloaded to {model_dir}")
            return model_dir
        except Exception as e2:
            logger.error(f"Failed to download backup embedding model: {e2}")
            return None

def main():
    """Download all required models"""
    logger.info("Starting model downloads for AI infrastructure...")

    llm_path = download_llm_model()
    embedding_path = download_embedding_model()

    if llm_path and embedding_path:
        logger.info("All models downloaded successfully!")
        logger.info(f"LLM model: {llm_path}")
        logger.info(f"Embedding model: {embedding_path}")
        logger.info("\nYou're ready to use the AI infrastructure!")
    else:
        logger.error("Some models failed to download. Please check the logs above.")

if __name__ == "__main__":
    main()
```

### 3. AI Infrastructure Configuration

Create a configuration file for the AI infrastructure:

```bash
mkdir -p src/config
```

#### Create Configuration File

Create the file `src/config/ai_config.py`:

```python
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
        description="Path to the quantized LLM model"
    )
    context_size: int = Field(
        default=2048,
        description="Context window size for the LLM"
    )
    temperature: float = Field(
        default=0.7,
        description="Temperature for LLM sampling"
    )
    top_p: float = Field(
        default=0.9,
        description="Top-p sampling parameter"
    )
    max_tokens: int = Field(
        default=512,
        description="Maximum number of tokens to generate"
    )
    metal_enabled: bool = Field(
        default=True,
        description="Whether to enable Metal acceleration on Apple Silicon"
    )

class VectorDBConfig(BaseModel):
    """Configuration for the Vector Database component"""
    db_type: str = Field(
        default="chroma",
        description="Type of vector database to use"
    )
    embedding_model: str = Field(
        default=str(MODELS_DIR / "embeddings" / "bge-small-en"),
        description="Path to the embedding model"
    )
    persist_directory: str = Field(
        default=str(DATA_DIR / "vectordb"),
        description="Directory to persist vector database"
    )
    collection_name: str = Field(
        default="iotsphere_knowledge",
        description="Name of the vector database collection"
    )

class AgentConfig(BaseModel):
    """Configuration for the Agent Framework"""
    planning_steps: int = Field(
        default=3,
        description="Number of planning steps for the agent"
    )
    max_iterations: int = Field(
        default=5,
        description="Maximum number of iterations for the agent"
    )
    reflection_enabled: bool = Field(
        default=True,
        description="Whether to enable agent reflection"
    )
    memory_size: int = Field(
        default=10,
        description="Number of past interactions to keep in memory"
    )

class SearchConfig(BaseModel):
    """Configuration for the Internet Search component"""
    provider: str = Field(
        default="duckduckgo",
        description="Search provider to use"
    )
    cache_ttl: int = Field(
        default=86400,  # 24 hours
        description="Time-to-live for cached search results in seconds"
    )
    rate_limit: int = Field(
        default=10,
        description="Maximum requests per minute"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of search results to return"
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
```

### 4. Test Infrastructure

Following the TDD principles of the IoTSphere project, we'll create tests for the AI infrastructure:

```bash
mkdir -p src/tests/unit/ai/infrastructure
```

#### Create Test File

Create the file `src/tests/unit/ai/infrastructure/test_configuration.py`:

```python
"""
Tests for the AI infrastructure configuration.
"""

import os
import pytest
from pathlib import Path
from src.config.ai_config import get_config, AIConfig, LLMConfig, VectorDBConfig, AgentConfig, SearchConfig

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
    assert data_dir.exists() or not Path(config.vector_db.persist_directory).is_absolute()
```

### 5. Core Components

Now, let's create the core components for our AI infrastructure:

```bash
mkdir -p src/ai/llm
mkdir -p src/ai/vector_db
mkdir -p src/ai/agent
mkdir -p src/ai/search
```

#### LLM Component

Create the file `src/ai/llm/llm_interface.py`:

```python
"""
Interface for the LLM component of the AI infrastructure.
Optimized for Mac M1/M2 hardware using llama.cpp.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from src.config.ai_config import get_config, LLMConfig

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for the LLM component using llama.cpp"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM interface with the given configuration"""
        self.config = config or get_config().llm
        self._llm = None
        self._tokenizer = None

    def _load_model(self):
        """Load the LLM model lazily"""
        if self._llm is not None:
            return

        try:
            from llama_cpp import Llama

            logger.info(f"Loading LLM model from {self.config.model_path}")
            self._llm = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.context_size,
                n_batch=512,  # Adjust based on available memory
                n_gpu_layers=-1 if self.config.metal_enabled else 0,
                verbose=False
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
        stream: bool = False
    ) -> Union[str, Any]:
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
        stop: Optional[List[str]]
    ) -> str:
        """Generate a complete response"""
        result = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
            echo=False
        )

        if isinstance(result, dict) and "choices" in result:
            return result["choices"][0]["text"].strip()
        elif isinstance(result, list) and len(result) > 0:
            return result[0]["choices"][0]["text"].strip()
        else:
            return str(result).strip()

    def _stream_response(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[List[str]]
    ) -> Any:
        """Stream the response token by token"""
        stream = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
            echo=False,
            stream=True
        )

        return stream

    def tokenize(self, text: str) -> List[int]:
        """Tokenize the given text"""
        self._load_model()
        return self._llm.tokenize(text.encode('utf-8'))

    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the given text"""
        tokens = self.tokenize(text)
        return len(tokens)
```

## Running the Setup

1. Install required dependencies:
   ```bash
   pip install -r requirements.ai.txt
   ```

2. Run the model download script:
   ```bash
   python scripts/ai/download_models.py
   ```

3. Run the configuration tests:
   ```bash
   python -m pytest src/tests/unit/ai/infrastructure/test_configuration.py -v
   ```

4. Create basic directories for AI data:
   ```bash
   mkdir -p data/vectordb
   mkdir -p data/cache
   ```

## Next Steps

After setting up the infrastructure components, you can proceed with implementing the specific use cases defined in the AI integration strategy:

1. Knowledge-Powered Field Service
2. Intelligent Document Processing
3. Agentic Support Assistant

Each use case will use the infrastructure components we've set up here, with additional specialized modules for their specific functionality.

## Troubleshooting

### Common Issues on Mac M1/M2

1. **Metal Acceleration Issues**

   If you encounter errors related to Metal acceleration:
   ```
   Error loading library: dlopen(libMoltenVK.dylib, 0x0001): image not found
   ```

   Try installing MoltenVK:
   ```bash
   brew install molten-vk
   ```

2. **Memory Limitations**

   If you encounter memory issues with larger models:

   - Reduce the context window size in `src/config/ai_config.py`
   - Use a smaller model (e.g., 7B instead of 13B)
   - Close other memory-intensive applications

3. **Slow Model Loading**

   The first load of LLM models can be slow. Subsequent loads will be faster as the OS caches the file.

4. **Python Package Conflicts**

   If you encounter package conflicts:
   ```bash
   pip install -r requirements.ai.txt --ignore-installed
   ```

## References

- [llama.cpp GitHub Repository](https://github.com/ggerganov/llama.cpp)
- [Chroma DB Documentation](https://docs.trychroma.com/)
- [Hugging Face Hub](https://huggingface.co/models)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
