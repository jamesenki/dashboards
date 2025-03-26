"""
Redis caching specifically optimized for operational dashboard data.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.adapters.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class OperationsDashboardCache:
    """Cache handler for real-time operations dashboard data."""
    
    def __init__(self, redis_cache: RedisCache):
        self.redis = redis_cache
        self.cache_ttl = 60  # 1 minute TTL for operational data
    
    async def cache_vending_machine_operations(self, machine_id: str, ops_data: Dict) -> bool:
        """Cache vending machine operations dashboard data."""
        key = f"dashboard:vm:{machine_id}:operations"
        return await self.redis.set(key, ops_data, expire=self.cache_ttl)
    
    async def get_vending_machine_operations(self, machine_id: str) -> Optional[Dict]:
        """Get cached vending machine operations dashboard data."""
        key = f"dashboard:vm:{machine_id}:operations"
        return await self.redis.get(key)
    
    async def cache_ice_cream_machine_operations(self, machine_id: str, ops_data: Dict) -> bool:
        """Cache ice cream machine operations dashboard data."""
        key = f"dashboard:icm:{machine_id}:operations"
        return await self.redis.set(key, ops_data, expire=self.cache_ttl)
    
    async def get_ice_cream_machine_operations(self, machine_id: str) -> Optional[Dict]:
        """Get cached ice cream machine operations dashboard data."""
        key = f"dashboard:icm:{machine_id}:operations"
        return await self.redis.get(key)
    
    async def cache_water_heater_operations(self, heater_id: str, ops_data: Dict) -> bool:
        """Cache water heater operations dashboard data."""
        key = f"dashboard:wh:{heater_id}:operations"
        return await self.redis.set(key, ops_data, expire=self.cache_ttl)
    
    async def get_water_heater_operations(self, heater_id: str) -> Optional[Dict]:
        """Get cached water heater operations dashboard data."""
        key = f"dashboard:wh:{heater_id}:operations"
        return await self.redis.get(key)
    
    async def invalidate_operations_cache(self, device_id: str, device_type: str) -> None:
        """Invalidate operations cache when device data changes."""
        if device_type == "vending_machine":
            key = f"dashboard:vm:{device_id}:operations"
            await self.redis.delete(key)
            
            # Also invalidate ice cream machine cache if this might be one
            key_icm = f"dashboard:icm:{device_id}:operations"
            await self.redis.delete(key_icm)
        
        elif device_type == "water_heater":
            key = f"dashboard:wh:{device_id}:operations"
            await self.redis.delete(key)
    
    async def publish_operations_update(self, device_id: str, device_type: str) -> None:
        """Publish real-time update notification for dashboard subscribers."""
        channel = f"dashboard:{device_id}:updates"
        message = {
            "type": "operations_update",
            "device_id": device_id,
            "device_type": device_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis.publish(channel, message)
