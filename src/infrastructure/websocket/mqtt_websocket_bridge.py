"""
MQTT-WebSocket Bridge - Forwards MQTT messages to WebSocket clients.

This component bridges the gap between MQTT and WebSocket, allowing
real-time shadow updates to be streamed to frontend clients. It includes
advanced resilience features such as auto-reconnection, connection state
management, and improved error handling.
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable, Tuple, Union

# Import the existing WebSocket manager
from src.infrastructure.websocket.websocket_manager import WebSocketServiceManager

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states for the MQTT-WebSocket bridge."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()


class MQTTWebSocketBridge:
    """
    Bridges MQTT messages to WebSocket clients with enhanced resilience.
    
    This class subscribes to MQTT topics and forwards messages
    to connected WebSocket clients. It ensures shadow updates
    are delivered in real-time to the frontend UI.
    
    Features:
    - Auto-reconnection with exponential backoff
    - Connection state monitoring
    - Topic subscription buffering during disconnections
    - Graceful error handling and recovery
    
    Responsibilities:
    - Subscribe to relevant MQTT topics
    - Forward MQTT messages to WebSocket clients
    - Filter messages based on client subscriptions
    - Maintain connection state and recover from failures
    """
    
    def __init__(self, mqtt_client):
        """
        Initialize the MQTT-WebSocket bridge.
        
        Args:
            mqtt_client: MQTT client for subscribing to topics
        """
        self.mqtt_client = mqtt_client
        self.websocket_manager = WebSocketServiceManager.get_instance()
        self.connection_state = ConnectionState.DISCONNECTED
        self._subscribed_topics: Set[str] = set()
        self._pending_subscriptions: Set[str] = set()  # Topics to subscribe once connected
        self._connection_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_reconnect_delay = 1.0  # seconds
        self._reconnect_task: Optional[asyncio.Task] = None
        self._last_connection_time: Optional[float] = None
        self._last_error: Optional[str] = None
        self._last_error_time: Optional[float] = None
        self._message_counter = 0
        self._message_handlers: Dict[str, List[Callable]] = {}
        
        # Configure MQTT client callbacks
        self._setup_mqtt_callbacks()
        logger.info("MQTT-WebSocket bridge initialized")
        
    def _setup_mqtt_callbacks(self) -> None:
        """Set up MQTT client callbacks."""
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
    
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None) -> None:
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.connection_state = ConnectionState.CONNECTED
            self._last_connection_time = time.time()
            self._connection_attempts = 0  # Reset counter on successful connection
            
            # Resubscribe to all topics
            all_topics = self._subscribed_topics.union(self._pending_subscriptions)
            if all_topics:
                asyncio.create_task(self._resubscribe_to_all_topics(all_topics))
        else:
            error_message = f"Failed to connect to MQTT broker with code {rc}"
            logger.error(error_message)
            self._record_error(error_message)
            self.connection_state = ConnectionState.ERROR
            
            # Schedule reconnection
            self._schedule_reconnect()
    
    def _on_mqtt_disconnect(self, client, userdata, rc, properties=None) -> None:
        """Callback for when the client disconnects from the broker."""
        if rc == 0:
            logger.info("Disconnected from MQTT broker cleanly")
            self.connection_state = ConnectionState.DISCONNECTED
        else:
            error_message = f"Unexpected disconnection from MQTT broker with code {rc}"
            logger.warning(error_message)
            self._record_error(error_message)
            self.connection_state = ConnectionState.DISCONNECTED
            
            # Schedule reconnection
            self._schedule_reconnect()
    
    def _record_error(self, error_message: str) -> None:
        """Record the last error information."""
        self._last_error = error_message
        self._last_error_time = time.time()
    
    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt with exponential backoff."""
        if self._reconnect_task and not self._reconnect_task.done():
            logger.debug("Reconnect already scheduled, skipping")
            return
            
        self._connection_attempts += 1
        if self._connection_attempts > self._max_reconnect_attempts:
            logger.error(f"Maximum reconnection attempts ({self._max_reconnect_attempts}) exceeded")
            self.connection_state = ConnectionState.ERROR
            return
            
        # Calculate delay with exponential backoff (1s, 2s, 4s, 8s, 16s...)
        delay = min(self._base_reconnect_delay * (2 ** (self._connection_attempts - 1)), 60)
        logger.info(f"Scheduling reconnection attempt {self._connection_attempts} in {delay:.1f} seconds")
        
        # Create reconnection task
        self.connection_state = ConnectionState.RECONNECTING
        self._reconnect_task = asyncio.create_task(self._reconnect_with_delay(delay))
    
    async def _reconnect_with_delay(self, delay: float) -> None:
        """Reconnect after the specified delay."""
        await asyncio.sleep(delay)
        logger.info(f"Attempting reconnection to MQTT broker (attempt {self._connection_attempts}/{self._max_reconnect_attempts})")
        await self.connect()
            
    async def connect(self) -> bool:
        """
        Connect to MQTT broker and set up subscriptions.
        
        Returns:
            True if connected successfully, False otherwise
        """
        # Don't attempt to connect if already connected or connecting
        if self.connection_state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            logger.debug(f"Connection already in progress or established: {self.connection_state}")
            return self.connection_state == ConnectionState.CONNECTED
            
        self.connection_state = ConnectionState.CONNECTING
        logger.info("Connecting to MQTT broker...")
        
        try:
            # Connect using the MQTT client
            self.mqtt_client.connect(
                host=self.mqtt_client._host,
                port=self.mqtt_client._port
            )
            self.mqtt_client.loop_start()
            
            # Note: We'll get the actual connection result via the on_connect callback
            # For now, we assume success but the callback will update the state if needed
            logger.debug("MQTT connection initiated, waiting for callback")
            
            # Wait for the connection to establish or fail
            start_time = time.time()
            timeout = 10  # 10 seconds timeout
            
            while time.time() - start_time < timeout:
                if self.connection_state != ConnectionState.CONNECTING:
                    # State was updated by callback
                    break
                await asyncio.sleep(0.1)
            
            if self.connection_state == ConnectionState.CONNECTING:
                # Timed out waiting for callback
                self.connection_state = ConnectionState.ERROR
                error_message = "Timeout waiting for MQTT connection"
                self._record_error(error_message)
                logger.error(error_message)
                return False
                
            return self.connection_state == ConnectionState.CONNECTED
            
        except Exception as e:
            error_message = f"Failed to connect to MQTT broker: {str(e)}"
            logger.error(error_message)
            self._record_error(error_message)
            self.connection_state = ConnectionState.ERROR
            return False
            
    async def _resubscribe_to_all_topics(self, topics: Set[str]) -> None:
        """Resubscribe to all topics after a reconnection."""
        logger.info(f"Resubscribing to {len(topics)} topics after reconnection")
        
        try:
            for topic in topics:
                await self.mqtt_client.subscribe(topic)
                logger.debug(f"Resubscribed to topic: {topic}")
                
                # Move from pending to subscribed
                if topic in self._pending_subscriptions:
                    self._pending_subscriptions.remove(topic)
                    self._subscribed_topics.add(topic)
                    
            logger.info(f"Resubscribed to all {len(topics)} topics successfully")
        except Exception as e:
            error_message = f"Failed to resubscribe to topics: {str(e)}"
            logger.error(error_message)
            self._record_error(error_message)
    
    async def subscribe(self, topics: List[str]) -> bool:
        """
        Subscribe to MQTT topics with resilience.
        
        If the client is disconnected, topics will be added to a pending list
        and subscribed when the connection is established.
        
        Args:
            topics: List of MQTT topics to subscribe to
            
        Returns:
            True if subscribed successfully or added to pending, False on error
        """
        if not topics:
            logger.warning("No topics provided for subscription")
            return True  # Nothing to do
        
        logger.info(f"Subscribing to {len(topics)} MQTT topics")
        
        # Check connection state
        if self.connection_state != ConnectionState.CONNECTED:
            logger.warning(f"Not connected to MQTT broker (state: {self.connection_state}), topics will be queued")
            
            # Add topics to pending subscriptions
            for topic in topics:
                if topic not in self._subscribed_topics and topic not in self._pending_subscriptions:
                    self._pending_subscriptions.add(topic)
                    logger.debug(f"Topic queued for subscription: {topic}")
            
            # Try to connect (will subscribe in the on_connect callback)
            asyncio.create_task(self.connect())
            return True  # We're queuing the subscriptions, so this is a success
                
        try:
            # Subscribe to each topic
            for topic in topics:
                if topic not in self._subscribed_topics:
                    result, _ = await asyncio.wait_for(
                        self.mqtt_client.subscribe(topic),
                        timeout=5.0  # 5 second timeout for subscription
                    )
                    
                    if result == 0:  # Success
                        self._subscribed_topics.add(topic)
                        logger.debug(f"Subscribed to MQTT topic: {topic}")
                    else:
                        logger.warning(f"Failed to subscribe to topic {topic} with result code {result}")
                        self._pending_subscriptions.add(topic)  # Add to pending for retry
                        
            return True
        except asyncio.TimeoutError:
            logger.warning("Timeout while subscribing to topics, adding to pending list")
            # Add all topics to pending for later retry
            for topic in topics:
                if topic not in self._subscribed_topics:
                    self._pending_subscriptions.add(topic)
            return False
        except Exception as e:
            error_message = f"Error subscribing to MQTT topics: {str(e)}"
            logger.error(error_message)
            self._record_error(error_message)
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
                
    def _on_mqtt_message(self, client, userdata, message) -> None:
        """
        Callback for MQTT messages - creates async task to handle the message.
        
        This callback is executed in the MQTT client thread, so we create an asyncio
        task to handle the message in the event loop.
        
        Args:
            client: MQTT client instance
            userdata: User data
            message: MQTT message
        """
        # Increment message counter for monitoring
        self._message_counter += 1
        
        # Create a task to handle the message asynchronously
        asyncio.create_task(self._handle_mqtt_message(message))
        
    async def _handle_mqtt_message(self, message) -> None:
        """
        Process an MQTT message and forward it to WebSocket clients.
        
        Args:
            message: MQTT message object
        """
        try:
            # Extract topic and payload
            topic = message.topic.decode() if isinstance(message.topic, bytes) else message.topic
            payload = message.payload.decode() if isinstance(message.payload, bytes) else message.payload
            
            # Try to parse payload as JSON if possible
            try:
                payload_json = json.loads(payload)
                formatted_payload = json.dumps(payload_json)
            except (json.JSONDecodeError, TypeError):
                # Not JSON or couldn't be parsed, use as is
                formatted_payload = payload
                payload_json = None
            
            logger.debug(f"Processing MQTT message on topic: {topic}")
            
            # Add timestamp and topic to message if it's JSON
            if payload_json and isinstance(payload_json, dict):
                enriched_payload = {
                    **payload_json,
                    "_meta": {
                        "topic": topic,
                        "received_at": datetime.now().isoformat(),
                        "bridge_message_id": self._message_counter
                    }
                }
                formatted_payload = json.dumps(enriched_payload)
            
            # Get WebSocket service
            websocket_service = self.websocket_manager.get_websocket_service()
            if not websocket_service:
                logger.warning("WebSocket service not available")
                return
                
            # Call any registered handlers for this topic
            await self._call_topic_handlers(topic, payload_json or payload)
                
            # Forward to all connected clients that have subscribed to this topic
            clients_forwarded = 0
            for client_id, client_info in websocket_service.connected_clients.items():
                websocket = client_info.get("websocket")
                subscriptions = client_info.get("subscriptions", [])
                
                # Skip if client has no active websocket
                if not websocket:
                    continue
                    
                # Check if client has subscribed to this topic
                if self._topic_matches_subscription(topic, subscriptions):
                    try:
                        await websocket.send_text(formatted_payload)
                        clients_forwarded += 1
                    except Exception as e:
                        logger.error(f"Error sending message to client {client_id}: {str(e)}")
            
            if clients_forwarded > 0:
                logger.debug(f"Forwarded message on topic '{topic}' to {clients_forwarded} WebSocket clients")
                        
        except Exception as e:
            error_message = f"Error handling MQTT message: {str(e)}"
            logger.error(error_message)
            self._record_error(error_message)
    
    async def _call_topic_handlers(self, topic: str, payload: Any) -> None:
        """Call registered handlers for a specific topic."""
        # Find handlers that match this topic
        matching_handlers = []
        
        # Exact topic handlers
        if topic in self._message_handlers:
            matching_handlers.extend(self._message_handlers[topic])
        
        # Pattern-based handlers
        for pattern, handlers in self._message_handlers.items():
            if pattern != topic and self._topic_matches_pattern(topic, pattern):
                matching_handlers.extend(handlers)
        
        # Call all matching handlers
        for handler in matching_handlers:
            try:
                await handler(topic, payload)
            except Exception as e:
                logger.error(f"Error in message handler for topic {topic}: {str(e)}")
            
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
            if self._topic_matches_pattern(topic, subscription):
                return True
        return False
                
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """
        Check if a topic matches a specific pattern with MQTT wildcards.
        
        This method follows the MQTT specification for topic filtering with wildcards.
        See: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901242
        
        Args:
            topic: The actual topic of the message
            pattern: The subscription pattern with potential wildcards
            
        Returns:
            True if topic matches the pattern, False otherwise
        """
        # Exact match
        if pattern == topic:
            return True
        
        # Multi-level wildcard (#) can only appear at the end
        if '#' in pattern and not pattern.endswith('#'):
            logger.warning(f"Invalid MQTT topic pattern: {pattern} - '#' can only appear at the end")
            return False
            
        # Extract parts of the topic and pattern
        topic_parts = topic.split('/')
        pattern_parts = pattern.split('/')
        
        # Handle pattern ending with #
        if pattern.endswith('#'):
            # Remove the # from the pattern
            pattern_parts = pattern_parts[:-1] if pattern_parts[-1] == '#' else pattern_parts[:-1] + [pattern_parts[-1][:-1]]
            
            # Pattern must be shorter than or equal to topic
            if len(pattern_parts) > len(topic_parts):
                return False
                
            # Check all parts before the #
            for i, p_part in enumerate(pattern_parts):
                # Skip + wildcard
                if p_part == '+':
                    continue
                # Match exact part
                if i >= len(topic_parts) or p_part != topic_parts[i]:
                    return False
                    
            return True
        
        # Without multi-level wildcard, parts must be same length
        if len(pattern_parts) != len(topic_parts):
            return False
            
        # Check each part
        for p_part, t_part in zip(pattern_parts, topic_parts):
            if p_part != '+' and p_part != t_part:
                return False
                
        return True
        
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
            True if successfully subscribed or queued, False on error
        """
        # Use default shadow topics if none provided
        if topics is None:
            # Enhanced default topics for IoTSphere infrastructure
            topics = [
                # Shadow topics with granular monitoring
                "devices/+/shadow/update",     # Device shadow updates
                "devices/+/shadow/delta",      # Device shadow delta changes
                "devices/+/shadow/get",        # Shadow read requests
                "shadows/+/reported",          # Reported state updates
                "shadows/+/desired",           # Desired state updates
                
                # Telemetry data streams
                "devices/+/telemetry",         # Device telemetry
                "devices/+/status",            # Device connection status
                
                # System monitoring
                "$SYS/broker/clients/+",       # Client connection events
                "$SYS/broker/connection/#",    # Broker connection events
                
                # Alerts and notifications
                "alerts/#",                     # System alerts
                "notifications/+/user"         # User notifications
            ]
        
        logger.info(f"Subscribing to {len(topics)} MQTT topics")
        
        # Group the subscriptions by priority
        high_priority = [t for t in topics if t.startswith("devices/") or t.startswith("shadows/")]
        normal_priority = [t for t in topics if t not in high_priority and not t.startswith("$SYS/")]
        low_priority = [t for t in topics if t.startswith("$SYS/")]
        
        # Subscribe to high priority topics first
        success = True
        if high_priority:
            logger.debug(f"Subscribing to {len(high_priority)} high priority topics")
            hp_success = await self.subscribe(high_priority)
            success = success and hp_success
        
        # Then subscribe to normal priority topics
        if normal_priority:
            logger.debug(f"Subscribing to {len(normal_priority)} normal priority topics")
            np_success = await self.subscribe(normal_priority)
            success = success and np_success
            
        # Finally subscribe to low priority system topics
        if low_priority:
            logger.debug(f"Subscribing to {len(low_priority)} low priority system topics")
            lp_success = await self.subscribe(low_priority)
            success = success and lp_success
        
        if success:
            logger.info("Successfully subscribed or queued all MQTT topics")
        else:
            logger.warning("Some topics could not be subscribed, will retry later")
            # Schedule retry for failed topics
            self._schedule_topic_subscription_retry()
            
        return success
        
    async def _schedule_topic_subscription_retry(self, delay: float = 10.0) -> None:
        """Schedule a retry for topic subscriptions after delay."""
        await asyncio.sleep(delay)
        # Only retry if we have pending subscriptions
        if self._pending_subscriptions:
            logger.info(f"Retrying {len(self._pending_subscriptions)} pending topic subscriptions")
            await self.subscribe(list(self._pending_subscriptions))
    
    def register_message_handler(self, topic_pattern: str, handler: Callable) -> None:
        """
        Register a handler function for a specific topic pattern.
        
        The handler will be called when a message matching the topic pattern is received.
        
        Args:
            topic_pattern: MQTT topic pattern (can include wildcards)
            handler: Async function to call with (topic, payload) when message is received
        """
        if topic_pattern not in self._message_handlers:
            self._message_handlers[topic_pattern] = []
            
        if handler not in self._message_handlers[topic_pattern]:
            self._message_handlers[topic_pattern].append(handler)
            logger.debug(f"Registered handler for topic pattern: {topic_pattern}")
    
    def unregister_message_handler(self, topic_pattern: str, handler: Optional[Callable] = None) -> None:
        """
        Unregister a handler function for a specific topic pattern.
        
        If handler is None, all handlers for the topic pattern are removed.
        
        Args:
            topic_pattern: MQTT topic pattern
            handler: Handler function to remove, or None to remove all
        """
        if topic_pattern not in self._message_handlers:
            return
            
        if handler is None:
            # Remove all handlers for this topic
            del self._message_handlers[topic_pattern]
            logger.debug(f"Unregistered all handlers for topic pattern: {topic_pattern}")
        else:
            # Remove specific handler
            if handler in self._message_handlers[topic_pattern]:
                self._message_handlers[topic_pattern].remove(handler)
                logger.debug(f"Unregistered handler for topic pattern: {topic_pattern}")
                
            # Clean up empty handler lists
            if not self._message_handlers[topic_pattern]:
                del self._message_handlers[topic_pattern]
