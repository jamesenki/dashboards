"""
Message Broker Integrator

This module connects all message broker components in the application startup
following Clean Architecture principles. It initializes the:
- MQTT Publisher
- MongoDB Shadow Listener
- MQTT-WebSocket Bridge

Each component is loosely coupled and communicates through the message broker.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
from fastapi import FastAPI

from src.config.settings import get_settings
from src.infrastructure.messaging.shadow_publisher import ShadowPublisher
from src.infrastructure.device_shadow.mongodb_shadow_listener import MongoDBShadowListener
from src.infrastructure.websocket.mqtt_websocket_bridge import MQTTWebSocketBridge
from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage

logger = logging.getLogger(__name__)

class MessageBrokerIntegrator:
    """
    Integrates all message broker components and manages their lifecycle.
    
    This class follows the Façade pattern to provide a simple interface for 
    connecting all components of the message broker pattern.
    """
    
    def __init__(
        self, 
        app: FastAPI,
        mqtt_client: Optional[mqtt.Client] = None,
        shadow_storage: Optional[MongoDBShadowStorage] = None
    ):
        """Initialize the message broker integrator."""
        self.app = app
        self.settings = get_settings()
        self.tasks: Dict[str, asyncio.Task] = {}
        
        # Initialize MQTT client if not provided
        self.mqtt_client = mqtt_client or self._create_mqtt_client()
        
        # Initialize shadow storage if not provided
        self.shadow_storage = shadow_storage or MongoDBShadowStorage()
        
        # Initialize components
        self.shadow_listener = None
        self.mqtt_websocket_bridge = None
        self.mqtt_publisher = None
    
    def _create_mqtt_client(self) -> mqtt.Client:
        """Create and configure an MQTT client."""
        client = mqtt.Client(client_id=f"iotsphere-broker-{id(self)}", 
                             protocol=mqtt.MQTTv5)
        
        # Configure client with credentials if available
        if self.settings.mqtt_username and self.settings.mqtt_password:
            client.username_pw_set(
                username=self.settings.mqtt_username,
                password=self.settings.mqtt_password
            )
        
        # Configure TLS if enabled
        if self.settings.mqtt_use_tls:
            client.tls_set()
        
        return client
    
    async def initialize(self) -> None:
        """Initialize all message broker components."""
        logger.info("Initializing message broker components")
        
        # Connect MQTT client
        try:
            self.mqtt_client.connect(
                host=self.settings.mqtt_broker_host,
                port=self.settings.mqtt_broker_port
            )
            self.mqtt_client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.settings.mqtt_broker_host}:{self.settings.mqtt_broker_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            raise
        
        # Initialize components
        try:
            # Create Shadow publisher
            self.mqtt_publisher = ShadowPublisher(
                mqtt_client=self.mqtt_client,
                shadow_storage=self.shadow_storage
            )
            
            # Create MongoDB shadow listener
            self.shadow_listener = MongoDBShadowListener(
                mqtt_client=self.mqtt_client,
                shadow_storage=self.shadow_storage
            )
            
            # Create MQTT-WebSocket bridge
            self.mqtt_websocket_bridge = MQTTWebSocketBridge(
                mqtt_client=self.mqtt_client
            )
            
            # Start background tasks
            self.tasks["shadow_listener"] = asyncio.create_task(
                self.shadow_listener.start()
            )
            
            # Subscribe bridge to shadow topic
            self.mqtt_websocket_bridge.subscribe_to_topics()
            
            logger.info("Message broker components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize message broker components: {str(e)}")
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all message broker components."""
        logger.info("Shutting down message broker components")
        
        # Cancel all tasks
        for name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Canceling task: {name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Disconnect MQTT client
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("Disconnected from MQTT broker")
        
        logger.info("Message broker components shutdown complete")


def register_events(app: FastAPI) -> None:
    """
    Register startup and shutdown events for the message broker.
    
    This function should be called when the application is created.
    
    Args:
        app: The FastAPI application
    """
    integrator = MessageBrokerIntegrator(app)
    
    @app.on_event("startup")
    async def startup_message_broker() -> None:
        """Initialize message broker on application startup."""
        await integrator.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_message_broker() -> None:
        """Shutdown message broker on application shutdown."""
        await integrator.shutdown()
