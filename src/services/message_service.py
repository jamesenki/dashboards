"""
Message Service - Core component of the Message Broker Pattern
Responsible for processing messages from external sources and directing them to storage
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.storage.mongodb_shadow_storage import MongoDBShadowStorage
from src.messaging.mqtt_publisher import MQTTPublisher

logger = logging.getLogger(__name__)

class MessageService:
    """
    Service responsible for processing device messages and maintaining device shadows
    
    Following Clean Architecture principles:
    - This service is part of the use case layer
    - It coordinates between data sources (external MQTT) and storage (MongoDB)
    - Ensures proper data validation and transformation
    """
    
    def __init__(self, storage: MongoDBShadowStorage, publisher: MQTTPublisher):
        """
        Initialize the message service
        
        Args:
            storage: MongoDB shadow storage for persisting device state
            publisher: MQTT publisher for internal message distribution
        """
        self.storage = storage
        self.publisher = publisher
        # Register callback for shadow updates
        self.storage.register_shadow_update_callback(self._on_shadow_updated)
        logger.info("Message Service initialized")
        
    async def process_device_message(self, message_str: str) -> None:
        """
        Process an incoming device message from the external MQTT broker
        
        Args:
            message_str: JSON string containing the device message
        """
        try:
            # Parse and validate message
            message = json.loads(message_str)
            if not self._validate_device_message(message):
                logger.warning(f"Invalid device message: {message_str}")
                return
                
            # Extract device ID
            device_id = message.get("device_id")
            if not device_id:
                logger.warning(f"Message missing device_id: {message_str}")
                return
                
            # Transform message to shadow document format
            shadow_update = self._transform_to_shadow(message)
            
            # Update shadow in MongoDB
            await self.storage.update_shadow(device_id, shadow_update)
            
            logger.info(f"Processed message for device {device_id}")
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message as JSON: {message_str}")
        except Exception as e:
            logger.exception(f"Error processing device message: {str(e)}")
            
    async def _on_shadow_updated(self, device_id: str, shadow: Dict[str, Any]) -> None:
        """
        Callback for when a shadow is updated in MongoDB
        Publishes the update to the internal MQTT broker
        
        Args:
            device_id: Device identifier
            shadow: Updated shadow document
        """
        try:
            # Prepare message for publishing
            message = {
                "device_id": device_id,
                **shadow,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Publish to device-specific topic
            topic = f"shadows/{device_id}"
            await self.publisher.publish(topic, json.dumps(message))
            
            logger.debug(f"Published shadow update for {device_id} to {topic}")
            
        except Exception as e:
            logger.exception(f"Error publishing shadow update: {str(e)}")
            
    def _validate_device_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate incoming device message schema
        
        Args:
            message: Parsed device message
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        required_fields = ["device_id"]
        
        # Check required fields exist
        if not all(field in message for field in required_fields):
            return False
            
        # Message must contain at least one telemetry field
        telemetry_fields = ["temperature", "target_temperature", "status", "mode", "pressure", "flow_rate"]
        if not any(field in message for field in telemetry_fields):
            return False
            
        return True
        
    def _transform_to_shadow(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform device message to shadow document format
        
        Args:
            message: Validated device message
            
        Returns:
            Shadow document ready for storage
        """
        # Start with empty shadow update
        shadow_update = {}
        
        # Map common telemetry fields directly
        direct_mappings = [
            "temperature", "target_temperature", "status", "mode", 
            "pressure", "flow_rate", "energy_usage", "heating_active"
        ]
        
        for field in direct_mappings:
            if field in message:
                shadow_update[field] = message[field]
                
        # Special field mappings and transformations
        if "status" in message:
            status_value = message["status"]
            # Convert string status to proper format if needed
            if isinstance(status_value, str):
                if status_value.upper() in ["ONLINE", "ACTIVE", "ON"]:
                    shadow_update["status"] = {
                        "operational": True,
                        "condition": "normal"
                    }
                elif status_value.upper() in ["OFFLINE", "INACTIVE", "OFF"]:
                    shadow_update["status"] = {
                        "operational": False,
                        "condition": "disconnected"
                    }
                    
        # Add metadata
        shadow_update["last_updated"] = datetime.utcnow().isoformat() + "Z"
        
        # Map telemetry into proper structure
        if any(f in message for f in ["temperature", "target_temperature", "heating_active"]):
            telemetry = {}
            if "temperature" in message:
                telemetry["temperature"] = message["temperature"]
            if "target_temperature" in message:
                telemetry["target_temperature"] = message["target_temperature"]
            if "heating_active" in message:
                telemetry["heating_status"] = "heating" if message["heating_active"] else "standby"
                
            shadow_update["telemetry"] = telemetry
                
        return shadow_update
