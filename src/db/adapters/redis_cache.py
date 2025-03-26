import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

import redis.asyncio as redis
from fastapi import Depends

from src.db.config import db_settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis_enabled = db_settings.REDIS_ENABLED
        self.client: Optional[redis.Redis] = None
        
    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.redis_enabled:
            logger.info("Redis caching is disabled")
            return
            
        if self.client is not None:
            return
            
        try:
            self.client = redis.Redis(
                host=db_settings.REDIS_HOST,
                port=db_settings.REDIS_PORT,
                db=db_settings.REDIS_DB,
                password=db_settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            await self.client.ping()
            logger.info(f"Connected to Redis at {db_settings.REDIS_HOST}:{db_settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.client:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration (seconds)."""
        if not self.client:
            return False
            
        try:
            serialized = json.dumps(value)
            if expire:
                return await self.client.setex(key, expire, serialized)
            else:
                return await self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.client:
            return False
            
        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to a Redis channel."""
        if not self.client:
            return 0
            
        try:
            serialized = json.dumps(message)
            return await self.client.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
            return 0
    
    # Device-specific methods for IoT data
    
    async def get_device_state(self, device_id: str) -> Optional[Dict]:
        """Get current device state from cache."""
        return await self.get(f"device:{device_id}")
    
    async def set_device_state(self, device_id: str, state: Dict) -> bool:
        """Cache current device state."""
        return await self.set(f"device:{device_id}", state)
    
    async def cache_latest_reading(self, device_id: str, reading: Dict) -> bool:
        """Cache the latest reading for a device."""
        metric = reading["metric_name"]
        key = f"device:{device_id}:latest:{metric}"
        return await self.set(key, reading, expire=3600)  # Expire after 1 hour
    
    async def get_latest_readings(self, device_id: str) -> Dict[str, Any]:
        """Get all latest readings for a device by scanning Redis keys."""
        if not self.client:
            return {}
            
        try:
            pattern = f"device:{device_id}:latest:*"
            keys = await self.client.keys(pattern)
            
            result = {}
            for key in keys:
                metric_name = key.split(":")[-1]
                reading = await self.get(key)
                if reading:
                    result[metric_name] = reading
                    
            return result
        except Exception as e:
            logger.error(f"Redis scan error: {e}")
            return {}


# Singleton instance
redis_cache = RedisCache()


async def get_redis_cache() -> RedisCache:
    """Dependency for getting Redis cache."""
    if redis_cache.client is None:
        await redis_cache.connect()
    return redis_cache
