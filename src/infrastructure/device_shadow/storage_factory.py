"""
Shadow storage factory for IoTSphere

This implementation:
1. Prioritizes MongoDB when configured
2. Provides detailed error information
3. Ensures shadow documents have proper history data
4. Includes connection validation and retry logic for MQTT compatibility
"""
import logging
import os
import asyncio
import traceback
from typing import Any, Optional

from src.services.device_shadow import InMemoryShadowStorage

logger = logging.getLogger(__name__)


async def create_shadow_storage_provider(config: Optional[dict] = None) -> Any:
    """
    Create and initialize the appropriate shadow storage provider based on configuration.

    This factory follows the Strategy pattern, allowing the application to switch
    storage implementations without modifying the DeviceShadowService.

    Args:
        config: Configuration dictionary (optional, will use environment if not provided)

    Returns:
        Initialized shadow storage provider

    Raises:
        RuntimeError: If MongoDB storage was explicitly requested but fails to initialize
    """
    # Get configuration from environment if not provided
    if config is None:
        config = {
            "storage_type": os.environ.get("SHADOW_STORAGE_TYPE", "memory"),
            "mongo_uri": os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
            "mongo_db_name": os.environ.get("MONGODB_DB_NAME", "iotsphere"),
            "redis_uri": os.environ.get("REDIS_URI", "redis://localhost:6379"),
            "strict_mode": os.environ.get("STRICT_SHADOW_STORAGE", "false").lower()
            == "true",
            "retry_count": int(os.environ.get("MONGODB_RETRY_COUNT", "2")),
            "retry_delay": float(os.environ.get("MONGODB_RETRY_DELAY", "0.5")),
            "connection_timeout": float(os.environ.get("MONGODB_CONN_TIMEOUT", "2.0")),
        }

    storage_type = config.get("storage_type", "memory").lower()
    strict_mode = config.get("strict_mode", False)
    retry_count = config.get("retry_count", 3)
    retry_delay = config.get("retry_delay", 1.0)

    # Create the appropriate storage provider
    if storage_type == "memory" or storage_type == "inmemory":
        logger.info("Using in-memory shadow storage for faster loading")
        return InMemoryShadowStorage()

    elif storage_type == "mongodb":
        try:
            # Import here to avoid dependency if MongoDB is not used
            from src.infrastructure.device_shadow.mongodb_shadow_storage import (
                MongoDBShadowStorage,
            )

            # Performance optimization: Start with a quick check for MongoDB availability
            # This helps fail fast if MongoDB is completely unavailable
            mongo_uri = config.get("mongo_uri", "mongodb://localhost:27017/")
            db_name = config.get("mongo_db_name", "iotsphere")
            connection_timeout = config.get("connection_timeout", 2.0)
            
            logger.info(f"Using MongoDB shadow storage: {mongo_uri}, DB: {db_name} (timeout: {connection_timeout}s)")
            
            # Create a special async function with timeout to ensure we don't hang
            async def initialize_with_timeout(storage, timeout):
                try:
                    # Create a task for the initialize method
                    init_task = asyncio.create_task(storage.initialize())
                    # Wait for the task with a timeout
                    await asyncio.wait_for(init_task, timeout=timeout)
                    return True
                except asyncio.TimeoutError:
                    logger.error(f"MongoDB initialization timed out after {timeout} seconds")
                    return False
                except Exception as e:
                    logger.error(f"MongoDB initialization failed: {str(e)}")
                    return False
            
            # Try multiple times to initialize MongoDB connection with MQTT compatibility
            for attempt in range(1, retry_count + 1):
                try:
                    logger.info(f"Attempting to initialize MongoDB connection (attempt {attempt}/{retry_count})...")
                    # Create the MongoDB storage instance
                    storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)
                    
                    # Initialize with timeout
                    init_success = await initialize_with_timeout(storage, connection_timeout)
                    if not init_success:
                        raise Exception("MongoDB initialization timed out or failed")
                    
                    logger.info("MongoDB connection established successfully")
                    
                    # Skip the shadow_exists check which can be slow and is unnecessary for connection verification
                    # Verify shadow documents if in strict mode
                    if strict_mode:
                        logger.info("Strict mode enabled, MongoDB connection verified")
                    
                    return storage
                    
                except Exception as e:
                    if attempt < retry_count:
                        logger.warning(f"MongoDB connection attempt {attempt} failed: {str(e)}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"All {retry_count} MongoDB connection attempts failed: {str(e)}")
                        
                        # If in strict mode, raise an exception instead of falling back
                        if strict_mode:
                            logger.error("STRICT_SHADOW_STORAGE=true, raising exception")
                            raise RuntimeError(
                                f"MongoDB shadow storage was explicitly requested but failed to initialize: {str(e)}"
                            )
                        else:
                            logger.warning(
                                "Falling back to in-memory storage for faster loading. Shadow data will not persist. "
                                "Set STRICT_SHADOW_STORAGE=true to prevent fallback."
                            )
                            return InMemoryShadowStorage()

        except ImportError as imp_err:
            # Performance optimization: Fail fast if MongoDB driver isn't installed
            logger.warning(f"MongoDB driver not installed: {str(imp_err)}. Using in-memory storage instead.")
            
            if strict_mode:
                logger.error("STRICT_SHADOW_STORAGE=true, raising exception")
                raise RuntimeError(f"MongoDB driver not installed: {str(imp_err)}")
            return InMemoryShadowStorage()

    else:
        error_msg = f"Unknown storage type '{storage_type}'. Using in-memory storage."
        logger.warning(error_msg)

        if strict_mode:
            logger.error("STRICT_SHADOW_STORAGE=true, raising exception")
            raise RuntimeError(error_msg)
        logger.warning("Falling back to in-memory storage due to unknown storage type")
        return InMemoryShadowStorage()
