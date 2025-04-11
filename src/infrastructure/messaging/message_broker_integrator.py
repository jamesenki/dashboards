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
import time
from typing import Dict, Any, Optional, List, Callable

import paho.mqtt.client as mqtt
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.infrastructure.messaging.shadow_publisher import ShadowPublisher
from src.infrastructure.device_shadow.mongodb_shadow_listener import MongoDBShadowListener
from src.infrastructure.websocket.mqtt_websocket_bridge import MQTTWebSocketBridge
from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage

logger = logging.getLogger(__name__)

class MessageBrokerHealthCheck:
    """Health check for message broker components."""
    
    def __init__(self):
        self.mqtt_connected = False
        self.shadow_listener_active = False
        self.websocket_bridge_active = False
        self.last_check_time = 0
        self.error_messages: List[str] = []
    
    def update_status(self, component: str, status: bool, error_message: Optional[str] = None) -> None:
        """Update component status."""
        if component == "mqtt":
            self.mqtt_connected = status
        elif component == "shadow_listener":
            self.shadow_listener_active = status
        elif component == "websocket_bridge":
            self.websocket_bridge_active = status
            
        if not status and error_message:
            self.error_messages.append(f"{component}: {error_message}")
        elif status and component in [msg.split(":")[0] for msg in self.error_messages]:
            # Remove errors for this component if it's now healthy
            self.error_messages = [msg for msg in self.error_messages if not msg.startswith(f"{component}:")]
        
        self.last_check_time = time.time()
    
    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        return self.mqtt_connected and self.shadow_listener_active and self.websocket_bridge_active
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status."""
        return {
            "mqtt_connected": self.mqtt_connected,
            "shadow_listener_active": self.shadow_listener_active,
            "websocket_bridge_active": self.websocket_bridge_active,
            "last_check_time": self.last_check_time,
            "is_healthy": self.is_healthy(),
            "errors": self.error_messages
        }


class MessageBrokerIntegrator:
    """
    Integrates all message broker components and manages their lifecycle.
    
    This class follows the Façade pattern to provide a simple interface for 
    connecting all components of the message broker pattern. It includes
    enhanced error handling, health checks, and retry mechanisms to ensure
    robust operation in production environments.
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
        self.health_check = MessageBrokerHealthCheck()
        self.connection_retry_count = 0
        self.max_retries = 5
        self.retry_delay = 2  # seconds
        
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
        """Initialize all message broker components with retry logic."""
        logger.info("Initializing message broker components")
        
        # Connect MQTT client with retry
        connected = await self._connect_mqtt_with_retry()
        if not connected:
            self.health_check.update_status("mqtt", False, "Failed to connect after maximum retries")
            raise ConnectionError("Failed to connect to MQTT broker after maximum retries")
        
        self.health_check.update_status("mqtt", True)
        
        # Initialize components with enhanced error handling
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
            
            # Start shadow listener with health check monitoring
            self.tasks["shadow_listener"] = asyncio.create_task(
                self._run_with_health_check(
                    self.shadow_listener.start(),
                    "shadow_listener",
                    self._on_shadow_listener_status_change
                )
            )
            
            # Start periodic health check task
            self.tasks["health_check"] = asyncio.create_task(
                self._periodic_health_check()
            )
            
            # Subscribe bridge to shadow topic
            try:
                await asyncio.wait_for(
                    self.mqtt_websocket_bridge.subscribe_to_topics(),
                    timeout=5.0  # 5 second timeout for subscription
                )
                self.health_check.update_status("websocket_bridge", True)
            except asyncio.TimeoutError:
                logger.warning("Timeout while subscribing to topics, will retry in background")
                # Create background task to retry subscription
                self.tasks["retry_subscribe"] = asyncio.create_task(
                    self._retry_topic_subscription()
                )
                self.health_check.update_status("websocket_bridge", False, "Subscription timeout, retrying")
            
            logger.info("Message broker components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize message broker components: {str(e)}")
            self.health_check.update_status("mqtt", False, str(e))
            self.health_check.update_status("shadow_listener", False, str(e))
            self.health_check.update_status("websocket_bridge", False, str(e))
            await self.shutdown()
            raise
    
    async def _connect_mqtt_with_retry(self) -> bool:
        """Connect to MQTT broker with retry logic."""
        self.connection_retry_count = 0
        retry_delay = self.retry_delay
        
        while self.connection_retry_count < self.max_retries:
            try:
                logger.info(f"Connecting to MQTT broker at {self.settings.mqtt_broker_host}:{self.settings.mqtt_broker_port} (attempt {self.connection_retry_count + 1}/{self.max_retries})")
                self.mqtt_client.connect(
                    host=self.settings.mqtt_broker_host,
                    port=self.settings.mqtt_broker_port
                )
                self.mqtt_client.loop_start()
                logger.info(f"Successfully connected to MQTT broker")
                return True
            except Exception as e:
                self.connection_retry_count += 1
                logger.warning(f"Failed to connect to MQTT broker (attempt {self.connection_retry_count}/{self.max_retries}): {str(e)}")
                
                if self.connection_retry_count >= self.max_retries:
                    logger.error("Maximum connection retry attempts reached")
                    return False
                
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay = min(retry_delay * 2, 30)  # Cap at 30 seconds
        
        return False
    
    async def _retry_topic_subscription(self, max_attempts: int = 5, retry_delay: float = 2.0) -> None:
        """Retry MQTT topic subscription in the background."""
        attempts = 0
        current_delay = retry_delay
        
        while attempts < max_attempts:
            try:
                logger.info(f"Retrying topic subscription (attempt {attempts + 1}/{max_attempts})")
                await self.mqtt_websocket_bridge.subscribe_to_topics()
                logger.info("Successfully subscribed to topics")
                self.health_check.update_status("websocket_bridge", True)
                return
            except Exception as e:
                attempts += 1
                logger.warning(f"Failed to subscribe to topics (attempt {attempts}/{max_attempts}): {str(e)}")
                
                if attempts >= max_attempts:
                    logger.error("Maximum subscription retry attempts reached")
                    self.health_check.update_status("websocket_bridge", False, "Failed to subscribe after maximum retries")
                    return
                
                await asyncio.sleep(current_delay)
                # Exponential backoff
                current_delay = min(current_delay * 2, 30)  # Cap at 30 seconds
    
    async def _run_with_health_check(self, coroutine, component_name: str, status_callback: Callable) -> None:
        """Run a coroutine with health check monitoring."""
        try:
            # Set initial status
            status_callback(True)
            # Run the coroutine
            await coroutine
        except Exception as e:
            logger.error(f"Error in {component_name}: {str(e)}")
            status_callback(False, str(e))
            raise
        finally:
            status_callback(False, "Task completed unexpectedly")
    
    def _on_shadow_listener_status_change(self, is_active: bool, error_message: Optional[str] = None) -> None:
        """Handle shadow listener status changes."""
        self.health_check.update_status("shadow_listener", is_active, error_message)
        
        if not is_active and error_message:
            logger.warning(f"Shadow listener inactive: {error_message}")
            # Could add auto-recovery logic here
    
    async def _periodic_health_check(self, interval: int = 60) -> None:
        """Run periodic health checks."""
        while True:
            try:
                # Verify MQTT connection
                if not self.mqtt_client.is_connected():
                    self.health_check.update_status("mqtt", False, "Connection lost")
                    # Try to reconnect
                    logger.warning("MQTT connection lost, attempting to reconnect")
                    await self._connect_mqtt_with_retry()
                else:
                    self.health_check.update_status("mqtt", True)
                
                # Log overall health status
                overall_status = "healthy" if self.health_check.is_healthy() else "unhealthy"
                logger.debug(f"Message broker health check: {overall_status}")
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Health check task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry on error
        
    async def shutdown(self) -> None:
        """Shutdown all message broker components."""
        logger.info("Shutting down message broker components")
        
        # Cancel all tasks gracefully
        for name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Canceling task: {name}")
                task.cancel()
                try:
                    # Give task 5 seconds to gracefully cancel
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Task {name} did not cancel within timeout")
                except asyncio.CancelledError:
                    logger.debug(f"Task {name} cancelled successfully")
                except Exception as e:
                    logger.error(f"Error while cancelling task {name}: {str(e)}")
        
        # Disconnect MQTT client
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting MQTT client: {str(e)}")
        
        # Update health status
        self.health_check.update_status("mqtt", False)
        self.health_check.update_status("shadow_listener", False)
        self.health_check.update_status("websocket_bridge", False)
        
        logger.info("Message broker components shutdown complete")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get the current health status of the message broker."""
        return self.health_check.get_status()


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
    
    # Register health check endpoint
    @app.get("/api/health/message-broker", response_class=JSONResponse)
    async def message_broker_health() -> JSONResponse:
        """Get health status of the message broker."""
        status = integrator.get_health_status()
        return JSONResponse(
            content=status,
            status_code=200 if status["is_healthy"] else 503
        )
    
    # Add middleware for handling message broker errors
    @app.middleware("http")
    async def message_broker_error_middleware(request: Request, call_next: Callable) -> Response:
        """Middleware to handle message broker errors."""
        try:
            return await call_next(request)
        except ConnectionError as e:
            if "MQTT broker" in str(e):
                logger.error(f"MQTT connection error: {str(e)}")
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Message broker service unavailable", "error": str(e)}
                )
            raise
