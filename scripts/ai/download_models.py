#!/usr/bin/env python
"""
Download required LLM and embedding models for the AI infrastructure.
Optimized for Mac M1/M2 hardware.
"""

import logging
import os
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
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
            local_dir_use_symlinks=False,
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
                local_dir_use_symlinks=False,
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
            ignore_patterns=["*.safetensors", "*.bin", "*.pt"],
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
                ignore_patterns=["*.safetensors", "*.bin", "*.pt"],
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
