"""
Shadow Publisher - Publishes device shadow updates to MQTT.

This component implements the Message Broker Pattern, translating MongoDB 
shadow updates to MQTT messages for real-time distribution.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ShadowPublisher:
    """
    Publishes device shadow updates to MQTT broker.
    
    This class subscribes to shadow updates from MongoDB and publishes them
    to MQTT topics for distribution to interested clients.
    
    Responsibilities:
    - Register for shadow update notifications
    - Format shadow updates as MQTT messages
    - Publish updates to appropriate topics
    """
    
    def __init__(self, shadow_storage, mqtt_client):
        """
        Initialize the shadow publisher.
        
        Args:
            shadow_storage: Storage implementation for device shadows
            mqtt_client: MQTT client for publishing
        """
        self.shadow_storage = shadow_storage
        self.mqtt_client = mqtt_client
        self.connected = False
        
        # Register callback for shadow updates
        self.shadow_storage.register_shadow_update_callback(self._on_shadow_updated)
        logger.info("Shadow publisher initialized")
        
    async def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Connect to MQTT broker
            await self.mqtt_client.connect()
            self.connected = True
            logger.info("Connected to MQTT broker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            self.connected = False
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.connected:
            try:
                await self.mqtt_client.disconnect()
                self.connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
                
    async def _on_shadow_updated(self, device_id: str, shadow_update: Dict[str, Any]) -> None:
        """
        Callback handler for shadow updates.
        
        This method is called when a shadow is updated in storage.
        It formats the update as an MQTT message and publishes it.
        
        Args:
            device_id: ID of the device whose shadow was updated
            shadow_update: The updated shadow data
        """
        if not self.connected:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Cannot publish update for {device_id}, not connected: {str(e)}")
                return
                
        try:
            # Prepare message payload
            message = {
                "device_id": device_id,
                **shadow_update
            }
            
            # Publish to device-specific topic
            topic = f"shadows/{device_id}"
            await self.mqtt_client.publish(topic, json.dumps(message))
            logger.debug(f"Published shadow update for {device_id}")
            
        except Exception as e:
            logger.error(f"Error publishing shadow update: {str(e)}")
