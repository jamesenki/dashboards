import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set, Union

import redis
import redis.asyncio as redis_async
from fastapi import Depends
from redis.asyncio import Redis

from src.db.config import db_settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis_enabled = db_settings.REDIS_ENABLED
        self.client: Optional[redis.Redis] = None

        # Default TTL values in seconds
        self.default_ttl = 3600  # 1 hour
        self.device_state_ttl = 7200  # 2 hours
        self.dashboard_data_ttl = 300  # 5 minutes
        self.readings_ttl = 86400  # 24 hours

        # Track connection state
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.last_connection_attempt = None

    async def connect(self) -> None:
        """Connect to Redis with retry logic and circuit breaking."""
        if not self.redis_enabled:
            logger.info("Redis caching is disabled")
            return

        if self.client is not None:
            # Already connected
            return

        # Circuit breaker pattern - avoid multiple connection attempts in short succession
        current_time = datetime.now(UTC)
        if (
            self.last_connection_attempt
            and (current_time - self.last_connection_attempt).total_seconds() < 30
            and self.connection_attempts >= self.max_connection_attempts
        ):
            logger.warning("Circuit breaker active: too many Redis connection attempts")
            return

        self.last_connection_attempt = current_time
        self.connection_attempts += 1

        try:
            # Attempt connection with timeout
            self.client = redis.Redis(
                host=db_settings.REDIS_HOST,
                port=db_settings.REDIS_PORT,
                db=db_settings.REDIS_DB,
                password=db_settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=2.0,  # 2 second timeout for operations
                socket_connect_timeout=2.0,  # 2 second timeout for connection
            )
            await self.client.ping()
            logger.info(
                f"Connected to Redis at {db_settings.REDIS_HOST}:{db_settings.REDIS_PORT}"
            )
            self.connection_attempts = 0  # Reset counter on successful connection
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
            if self.connection_attempts >= self.max_connection_attempts:
                logger.warning(
                    "Max Redis connection attempts reached. Will use fallback mechanisms."
                )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with auto-reconnect."""
        if not self.client and self.redis_enabled:
            # Try to reconnect if Redis should be enabled but client is None
            await self.connect()

        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.ConnectionError as e:
            logger.error(f"Redis connection lost: {e}")
            self.client = None  # Reset client on connection error
            await self.connect()  # Try to reconnect for next time
            return None
        except Exception as e:
            logger.error(f"Redis get error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration (seconds) and auto-reconnect."""
        if not self.client and self.redis_enabled:
            # Try to reconnect if Redis should be enabled but client is None
            await self.connect()

        if not self.client:
            return False

        try:
            serialized = json.dumps(value)
            # Use default TTL if none provided
            if expire is None:
                expire = self.default_ttl

            return await self.client.setex(key, expire, serialized)
        except redis.ConnectionError as e:
            logger.error(f"Redis connection lost during set: {e}")
            self.client = None  # Reset client on connection error
            await self.connect()  # Try to reconnect for next time
            return False
        except Exception as e:
            logger.error(f"Redis set error for key '{key}': {e}")
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
        """Cache current device state with appropriate TTL."""
        # Use device-specific TTL
        return await self.set(
            f"device:{device_id}", state, expire=self.device_state_ttl
        )

    async def cache_latest_reading(self, device_id: str, reading: Dict) -> bool:
        """Cache the latest reading for a device."""
        if not reading.get("metric_name"):
            logger.warning(f"Attempted to cache reading without metric_name: {reading}")
            return False

        metric = reading["metric_name"]
        key = f"device:{device_id}:latest:{metric}"

        # Set expiration based on data type
        return await self.set(key, reading, expire=self.readings_ttl)

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
    """Dependency for getting Redis cache with health check."""
    # First-time connection
    if redis_cache.client is None:
        await redis_cache.connect()
    else:
        # If client exists, periodically verify connection is still healthy
        try:
            # Only do health check every few minutes to avoid overhead
            last_attempt = redis_cache.last_connection_attempt
            if (
                last_attempt
                and (datetime.now(UTC) - last_attempt).total_seconds() > 300
            ):
                await redis_cache.client.ping()
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            redis_cache.client = None  # Reset client to trigger reconnect
            await redis_cache.connect()

    return redis_cache
