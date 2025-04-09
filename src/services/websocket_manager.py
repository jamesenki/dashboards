"""
WebSocket Manager for IoTSphere platform.

This service manages WebSocket connections for real-time communication between
the server and clients, handling connection lifecycle and message broadcasting.
"""
import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Singleton instance of the WebSocketManager
_websocket_manager_instance = None


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasting messages to connected clients.

    This manager supports:
    1. Tracking active connections by device ID and connection type
    2. Broadcasting messages to all clients or to specific device subscribers
    3. Connection lifecycle management (connect/disconnect)
    """

    def __init__(self):
        """Initialize the WebSocket manager."""
        # Active connections by device_id: {device_id: {connection_type: set(websockets)}}
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        # Active connections by client ID for individual targeting
        self.client_connections: Dict[str, WebSocket] = {}
        # Global subscriptions for broadcast topics
        self.global_subscriptions: Dict[str, Set[WebSocket]] = {}
        logger.info("WebSocket Manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        device_id: str,
        connection_type: str = "state",
        client_id: str = None,
    ):
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            device_id: The device ID this connection is associated with
            connection_type: The type of connection (state, telemetry, alerts)
            client_id: Optional unique client identifier

        Returns:
            None
        """
        # Initialize dictionaries if needed
        if device_id not in self.active_connections:
            self.active_connections[device_id] = {}

        if connection_type not in self.active_connections[device_id]:
            self.active_connections[device_id][connection_type] = set()

        # Add connection to the appropriate set
        self.active_connections[device_id][connection_type].add(websocket)

        # Register client ID if provided
        if client_id:
            self.client_connections[client_id] = websocket

        logger.info(f"Client connected to {device_id} for {connection_type}")

    async def disconnect(
        self,
        websocket: WebSocket,
        device_id: str = None,
        connection_type: str = None,
        client_id: str = None,
    ):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            device_id: The device ID this connection is associated with
            connection_type: The type of connection
            client_id: Optional unique client identifier

        Returns:
            None
        """
        # Remove from client connections if registered
        if client_id and client_id in self.client_connections:
            del self.client_connections[client_id]

        # Remove from device-specific connections
        if device_id:
            # If connection_type is specified, only remove from that type
            if connection_type and device_id in self.active_connections:
                if connection_type in self.active_connections[device_id]:
                    self.active_connections[device_id][connection_type].discard(
                        websocket
                    )
                    # Clean up empty sets
                    if not self.active_connections[device_id][connection_type]:
                        del self.active_connections[device_id][connection_type]

            # Otherwise, remove from all connection types for the device
            else:
                if device_id in self.active_connections:
                    for conn_type in list(self.active_connections[device_id].keys()):
                        self.active_connections[device_id][conn_type].discard(websocket)
                        # Clean up empty sets
                        if not self.active_connections[device_id][conn_type]:
                            del self.active_connections[device_id][conn_type]

            # Clean up empty device entries
            if (
                device_id in self.active_connections
                and not self.active_connections[device_id]
            ):
                del self.active_connections[device_id]

        # Remove from global subscriptions
        for topic in list(self.global_subscriptions.keys()):
            if websocket in self.global_subscriptions[topic]:
                self.global_subscriptions[topic].discard(websocket)
                # Clean up empty sets
                if not self.global_subscriptions[topic]:
                    del self.global_subscriptions[topic]

        logger.info(f"Client disconnected from {device_id}")

    async def broadcast_to_device(
        self, device_id: str, message: Any, connection_type: str = None
    ):
        """
        Broadcast a message to all clients connected to a specific device.

        Args:
            device_id: The device ID to broadcast to
            message: The message to broadcast (will be JSON serialized)
            connection_type: Optional type of connection to target

        Returns:
            int: Number of clients message was sent to
        """
        if device_id not in self.active_connections:
            return 0

        # Convert message to JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)

        send_count = 0

        # If connection_type is specified, only broadcast to that type
        if connection_type:
            if connection_type in self.active_connections[device_id]:
                websockets = self.active_connections[device_id][connection_type]
                for websocket in websockets:
                    try:
                        await websocket.send_text(message)
                        send_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send message to client: {e}")
                        # Will be cleaned up on next receive attempt

        # Otherwise, broadcast to all connection types
        else:
            for conn_type, websockets in self.active_connections[device_id].items():
                for websocket in websockets:
                    try:
                        await websocket.send_text(message)
                        send_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send message to client: {e}")
                        # Will be cleaned up on next receive attempt

        return send_count

    async def broadcast_to_topic(self, topic: str, message: Any):
        """
        Broadcast a message to all clients subscribed to a topic.

        Args:
            topic: The topic to broadcast to
            message: The message to broadcast (will be JSON serialized)

        Returns:
            int: Number of clients message was sent to
        """
        if topic not in self.global_subscriptions:
            return 0

        # Convert message to JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)

        send_count = 0
        websockets = self.global_subscriptions[topic]
        for websocket in websockets:
            try:
                await websocket.send_text(message)
                send_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to client: {e}")
                # Will be cleaned up on next receive attempt

        return send_count

    async def subscribe_to_topic(self, websocket: WebSocket, topic: str):
        """
        Subscribe a client to a global topic.

        Args:
            websocket: The WebSocket connection
            topic: The topic to subscribe to

        Returns:
            None
        """
        if topic not in self.global_subscriptions:
            self.global_subscriptions[topic] = set()

        self.global_subscriptions[topic].add(websocket)
        logger.info(f"Client subscribed to topic: {topic}")

    async def unsubscribe_from_topic(self, websocket: WebSocket, topic: str):
        """
        Unsubscribe a client from a global topic.

        Args:
            websocket: The WebSocket connection
            topic: The topic to unsubscribe from

        Returns:
            None
        """
        if topic in self.global_subscriptions:
            self.global_subscriptions[topic].discard(websocket)

            # Clean up empty topic
            if not self.global_subscriptions[topic]:
                del self.global_subscriptions[topic]

            logger.info(f"Client unsubscribed from topic: {topic}")

    async def send_to_client(self, client_id: str, message: Any):
        """
        Send a message to a specific client by ID.

        Args:
            client_id: The client ID to send to
            message: The message to send (will be JSON serialized)

        Returns:
            bool: Whether the message was sent successfully
        """
        if client_id not in self.client_connections:
            return False

        # Convert message to JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)

        try:
            await self.client_connections[client_id].send_text(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            return False


def get_websocket_manager() -> WebSocketManager:
    """
    Get or create the singleton instance of WebSocketManager.

    Returns:
        WebSocketManager: The singleton WebSocketManager instance
    """
    global _websocket_manager_instance

    if _websocket_manager_instance is None:
        _websocket_manager_instance = WebSocketManager()
        logger.info("Created singleton WebSocketManager instance")

    return _websocket_manager_instance
