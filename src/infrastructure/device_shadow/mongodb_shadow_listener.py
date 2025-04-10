"""
MongoDB Shadow Listener - Listens for MongoDB shadow changes.

This component uses MongoDB Change Streams to detect changes in device shadows
and publishes those changes to MQTT for real-time distribution.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class MongoDBShadowListener:
    """
    Listens for changes to shadow documents in MongoDB.
    
    This class leverages MongoDB Change Streams to detect shadow updates
    and publishes them to MQTT for real-time distribution to clients.
    
    Responsibilities:
    - Set up and maintain MongoDB change stream
    - Process change events
    - Extract updated shadow data
    - Publish changes to MQTT
    """
    
    def __init__(self, shadow_storage, mqtt_client):
        """
        Initialize the shadow listener.
        
        Args:
            shadow_storage: Storage implementation for device shadows
            mqtt_client: MQTT client for publishing
        """
        self.shadow_storage = shadow_storage
        self.mqtt_client = mqtt_client
        self.change_stream = None
        self.running = False
        self.connected = False
        logger.info("MongoDB Shadow Listener initialized")
        
    async def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            await self.mqtt_client.connect()
            self.connected = True
            logger.info("Connected to MQTT broker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            self.connected = False
            return False
            
    async def start(self) -> None:
        """
        Start listening for shadow changes.
        
        This method sets up a MongoDB change stream to monitor changes
        to shadow documents and starts processing change events.
        """
        if self.running:
            return
            
        if not self.connected:
            await self.connect()
            
        try:
            # Get collection from shadow storage
            collection = self.shadow_storage.shadows
            
            # Set up change stream
            self.change_stream = collection.watch(
                pipeline=[
                    # Only watch for inserts and updates
                    {"$match": {"operationType": {"$in": ["insert", "update", "replace"]}}}
                ],
                full_document="updateLookup"
            )
            
            self.running = True
            logger.info("Started listening for shadow changes")
            
            # Start processing change events in the background
            asyncio.create_task(self._process_changes())
            
        except Exception as e:
            logger.error(f"Failed to start shadow listener: {str(e)}")
            self.running = False
            
    async def stop(self) -> None:
        """Stop listening for shadow changes."""
        if not self.running:
            return
            
        try:
            # Close change stream
            if self.change_stream:
                await self.change_stream.close()
                self.change_stream = None
                
            self.running = False
            logger.info("Stopped listening for shadow changes")
            
        except Exception as e:
            logger.error(f"Error stopping shadow listener: {str(e)}")
            
    async def _process_changes(self) -> None:
        """
        Process change events from the change stream.
        
        This method runs in a background task and processes change events
        as they arrive from MongoDB.
        """
        if not self.change_stream:
            logger.error("Cannot process changes, change stream not initialized")
            return
            
        try:
            # Process change events as they arrive
            async for change in self.change_stream:
                await self._on_shadow_change(change)
                
        except Exception as e:
            logger.error(f"Error processing shadow changes: {str(e)}")
            self.running = False
            
    async def _on_shadow_change(self, change_event: Dict[str, Any]) -> None:
        """
        Handle a shadow change event.
        
        This method is called when a shadow document is changed in MongoDB.
        It extracts the updated data and publishes it to MQTT.
        
        Args:
            change_event: MongoDB change event
        """
        try:
            # Extract device ID from document key
            device_id = change_event.get("documentKey", {}).get("_id")
            if not device_id:
                logger.warning("Change event missing document key ID")
                return
                
            # Extract full document if available
            full_document = change_event.get("fullDocument")
            if not full_document:
                logger.warning(f"No full document in change event for {device_id}")
                return
                
            # Remove MongoDB-specific fields
            if "_id" in full_document:
                device_id = full_document["_id"]
                full_document = {k: v for k, v in full_document.items() if k != "_id"}
                
            # Publish to MQTT
            topic = f"shadows/{device_id}"
            message = {
                "device_id": device_id,
                **full_document
            }
            
            await self.mqtt_client.publish(topic, json.dumps(message))
            logger.debug(f"Published shadow change for {device_id}")
            
        except Exception as e:
            logger.error(f"Error handling shadow change: {str(e)}")
