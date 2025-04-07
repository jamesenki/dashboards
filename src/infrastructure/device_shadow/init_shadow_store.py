#!/usr/bin/env python3
"""
Redis Device Shadow/Twin Initialization Script for IoTSphere
Sets up Redis for device state management using a shadow/twin pattern.
"""
import os
import sys
import json
import logging
import redis

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis connection parameters
REDIS_PARAMS = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'password': os.environ.get('REDIS_PASSWORD', None),
    'db': int(os.environ.get('REDIS_DB', 0)),
    'decode_responses': True
}

# Redis key patterns
DEVICE_REPORTED_STATE_KEY = "device:{device_id}:reported"
DEVICE_DESIRED_STATE_KEY = "device:{device_id}:desired"
DEVICE_METADATA_KEY = "device:{device_id}:metadata"
DEVICE_SIMULATED_FLAG_KEY = "device:{device_id}:simulated"
DEVICE_LAST_UPDATE_KEY = "device:{device_id}:lastUpdate"
DEVICE_CONNECTED_KEY = "device:connected"  # Set of connected device IDs

def setup_redis_shadow():
    """Initialize Redis for device shadow storage"""
    try:
        # Connect to Redis
        logger.info("Connecting to Redis...")
        r = redis.Redis(**REDIS_PARAMS)
        
        # Test connection
        r.ping()
        logger.info("Connected to Redis successfully!")
        
        # Create example device shadow structure for documentation
        example_device = {
            "device_id": "example-device-001",
            "reported": {
                "temperature": 72.5,
                "mode": "auto",
                "power": "on",
                "lastReportTime": "2025-04-06T09:45:00Z"
            },
            "desired": {
                "temperature": 74.0,
                "mode": "auto",
                "power": "on",
                "requestTime": "2025-04-06T09:44:00Z"
            },
            "metadata": {
                "manufacturer": "Example Corp",
                "model": "Model X",
                "firmware": "1.2.3",
                "capabilities": ["temperature_control", "remote_power"]
            },
            "simulated": True
        }
        
        # Document example shadow structure - for development reference only
        docs_key = "device:shadow:documentation"
        r.set(docs_key, json.dumps(example_device, indent=2))
        logger.info("Documentation example created with key: %s", docs_key)
        
        # Set up basic Redis indexes for device shadow queries
        
        # Create a key expiration policy - only applies to disconnected devices
        # We'll set the device shadow TTL when a device disconnects, in the actual service
        
        logger.info("Redis device shadow store initialized successfully!")
        return True
        
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")
        return False

class DeviceShadowService:
    """
    Service for managing device shadows (digital twins) in Redis.
    This is a reference implementation for the shadow pattern used
    throughout the IoTSphere platform.
    """
    
    def __init__(self, redis_client=None):
        """Initialize the shadow service with Redis client"""
        self.redis = redis_client or redis.Redis(**REDIS_PARAMS)
    
    def get_device_shadow(self, device_id):
        """Get complete shadow (reported and desired state) for a device"""
        reported_key = DEVICE_REPORTED_STATE_KEY.format(device_id=device_id)
        desired_key = DEVICE_DESIRED_STATE_KEY.format(device_id=device_id)
        metadata_key = DEVICE_METADATA_KEY.format(device_id=device_id)
        simulated_key = DEVICE_SIMULATED_FLAG_KEY.format(device_id=device_id)
        
        # Get device state in a transaction
        pipe = self.redis.pipeline()
        pipe.get(reported_key)
        pipe.get(desired_key)
        pipe.get(metadata_key)
        pipe.get(simulated_key)
        results = pipe.execute()
        
        shadow = {
            "device_id": device_id,
            "reported": json.loads(results[0]) if results[0] else {},
            "desired": json.loads(results[1]) if results[1] else {},
            "metadata": json.loads(results[2]) if results[2] else {},
            "simulated": bool(results[3]) if results[3] else False,
            "connected": self.redis.sismember(DEVICE_CONNECTED_KEY, device_id)
        }
        
        return shadow
    
    def update_reported_state(self, device_id, state):
        """Update the reported state from a device"""
        key = DEVICE_REPORTED_STATE_KEY.format(device_id=device_id)
        
        # Get current state and merge with new state
        current = self.redis.get(key)
        current_state = json.loads(current) if current else {}
        
        # Update with new values
        current_state.update(state)
        
        # Store updated state
        self.redis.set(key, json.dumps(current_state))
        
        # Update last update timestamp
        self.redis.set(
            DEVICE_LAST_UPDATE_KEY.format(device_id=device_id),
            json.dumps({"timestamp": current_state.get("lastReportTime")})
        )
        
        return current_state
    
    def update_desired_state(self, device_id, state):
        """Update the desired state for a device"""
        key = DEVICE_DESIRED_STATE_KEY.format(device_id=device_id)
        
        # Get current desired state and merge with new state
        current = self.redis.get(key)
        current_state = json.loads(current) if current else {}
        
        # Update with new values
        current_state.update(state)
        
        # Store updated state
        self.redis.set(key, json.dumps(current_state))
        
        return current_state
    
    def set_device_simulated(self, device_id, simulated=True):
        """Mark a device as simulated or real"""
        key = DEVICE_SIMULATED_FLAG_KEY.format(device_id=device_id)
        self.redis.set(key, "1" if simulated else "0")
    
    def set_device_connected(self, device_id, connected=True):
        """Mark a device as connected or disconnected"""
        if connected:
            self.redis.sadd(DEVICE_CONNECTED_KEY, device_id)
        else:
            self.redis.srem(DEVICE_CONNECTED_KEY, device_id)

if __name__ == "__main__":
    if setup_redis_shadow():
        sys.exit(0)
    else:
        sys.exit(1)
