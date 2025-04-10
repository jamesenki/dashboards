"""
MQTT-WebSocket Bridge - Forwards MQTT messages to WebSocket clients.

This component bridges the gap between MQTT and WebSocket, allowing
real-time shadow updates to be streamed to frontend clients.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

# Import the existing WebSocket manager
from src.infrastructure.websocket.websocket_manager import WebSocketServiceManager

logger = logging.getLogger(__name__)


class MQTTWebSocketBridge:
    """
    Bridges MQTT messages to WebSocket clients.
    
    This class subscribes to MQTT topics and forwards messages
    to connected WebSocket clients. It ensures shadow updates
    are delivered in real-time to the frontend UI.
    
    Responsibilities:
    - Subscribe to relevant MQTT topics
    - Forward MQTT messages to WebSocket clients
    - Filter messages based on client subscriptions
    """
    
    def __init__(self, mqtt_client):
        """
        Initialize the MQTT-WebSocket bridge.
        
        Args:
            mqtt_client: MQTT client for subscribing to topics
        """
        self.mqtt_client = mqtt_client
        self.websocket_manager = WebSocketServiceManager.get_instance()
        self.connected = False
        self._subscribed_topics = set()
        logger.info("MQTT-WebSocket bridge initialized")
        
    async def connect(self) -> bool:
        """
        Connect to MQTT broker and set up subscriptions.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Connect to MQTT broker
            await self.mqtt_client.connect()
            
            # Set up message handler
            self.mqtt_client.on_message = self._on_mqtt_message
            
            self.connected = True
            logger.info("Connected to MQTT broker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            self.connected = False
            return False
            
    async def subscribe(self, topics: List[str]) -> bool:
        """
        Subscribe to MQTT topics.
        
        Args:
            topics: List of MQTT topics to subscribe to
            
        Returns:
            True if subscribed successfully, False otherwise
        """
        if not self.connected:
            success = await self.connect()
            if not success:
                return False
                
        try:
            # Subscribe to each topic
            for topic in topics:
                if topic not in self._subscribed_topics:
                    await self.mqtt_client.subscribe(topic)
                    self._subscribed_topics.add(topic)
                    logger.debug(f"Subscribed to MQTT topic: {topic}")
                    
            return True
        except Exception as e:
            logger.error(f"Error subscribing to MQTT topics: {str(e)}")
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.connected:
            try:
                await self.mqtt_client.disconnect()
                self.connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
                
    async def _on_mqtt_message(self, client, userdata, message) -> None:
        """
        Handler for MQTT messages.
        
        This method is called when a message is received from MQTT.
        It forwards the message to all connected WebSocket clients
        that have subscribed to the relevant topic.
        
        Args:
            client: MQTT client instance
            userdata: User data
            message: MQTT message
        """
        try:
            # Extract topic and payload
            topic = message.topic.decode() if isinstance(message.topic, bytes) else message.topic
            payload = message.payload.decode() if isinstance(message.payload, bytes) else message.payload
            
            logger.debug(f"Received MQTT message on topic: {topic}")
            
            # Get WebSocket service
            websocket_service = self.websocket_manager.get_websocket_service()
            if not websocket_service:
                logger.warning("WebSocket service not available")
                return
                
            # Forward to all connected clients that have subscribed to this topic
            for client_id, client_info in websocket_service.connected_clients.items():
                websocket = client_info.get("websocket")
                subscriptions = client_info.get("subscriptions", [])
                
                # Check if client has subscribed to this topic
                if self._topic_matches_subscription(topic, subscriptions):
                    try:
                        await websocket.send_text(payload)
                        logger.debug(f"Forwarded MQTT message to client: {client_id}")
                    except Exception as e:
                        logger.error(f"Error sending message to client {client_id}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error handling MQTT message: {str(e)}")
            
    def _topic_matches_subscription(self, topic: str, subscriptions: List[str]) -> bool:
        """
        Check if a topic matches any of the client's subscriptions.
        
        Args:
            topic: MQTT topic
            subscriptions: List of subscription patterns
            
        Returns:
            True if topic matches any subscription, False otherwise
        """
        for subscription in subscriptions:
            # Exact match
            if subscription == topic:
                return True
                
            # Wildcard match
            if subscription.endswith('#'):
                prefix = subscription[:-1]
                if topic.startswith(prefix):
                    return True
                    
            # Single-level wildcard
            if '+' in subscription:
                pattern_parts = subscription.split('/')
                topic_parts = topic.split('/')
                
                if len(pattern_parts) != len(topic_parts):
                    continue
                    
                match = True
                for pattern, part in zip(pattern_parts, topic_parts):
                    if pattern != '+' and pattern != part:
                        match = False
                        break
                        
                if match:
                    return True
                    
        return False
        
    async def subscribe_to_topics(self, topics: Optional[List[str]] = None) -> bool:
        """
        Subscribe to default or specified MQTT topics for shadow updates.
        
        This method is called during application startup to subscribe
        to the relevant MQTT topics for shadow updates. It sets up
        the bridge for forwarding shadow updates to WebSocket clients.
        
        Args:
            topics: Optional list of MQTT topics to subscribe to.
                   If None, default shadow topics will be used.
                   
        Returns:
            True if successfully subscribed, False otherwise
        """
        # Use default shadow topics if none provided
        if topics is None:
            # Default topics for device shadows - using wildcards to match all devices
            topics = [
                "shadows/#",            # All shadow updates
                "telemetry/#"           # All telemetry data
            ]
            
        logger.info(f"Subscribing to MQTT topics: {topics}")
        return await self.subscribe(topics)
