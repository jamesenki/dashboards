"""
Shadow Client Adapter

This module provides a client-friendly adapter for interacting with the device shadow service.
It follows Clean Architecture principles by encapsulating the infrastructure details
and providing a clean interface for the application layer.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fastapi import WebSocket, WebSocketDisconnect

from src.infrastructure.messaging.message_broker_adapter import (
    MessageBrokerAdapter,
    MessageSubscriptionRequest,
    TopicPattern,
)
from src.infrastructure.messaging.shadow_broker_integration import ShadowTopicMapper
from src.services.shadow_notification_service import ShadowNotificationService

logger = logging.getLogger(__name__)


@dataclass
class ShadowUpdateEvent:
    """Represents a shadow update event received by a client."""

    device_id: str
    operation: str = "update"
    reported: Dict[str, Any] = field(default_factory=dict)
    desired: Dict[str, Any] = field(default_factory=dict)
    version: Optional[int] = None
    timestamp: Optional[str] = None
    source: str = "shadow_service"

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "ShadowUpdateEvent":
        """
        Create a ShadowUpdateEvent from JSON data.

        Args:
            json_data: The JSON data to parse

        Returns:
            A ShadowUpdateEvent object
        """
        # Get reported and desired state directly from json_data
        reported = json_data.get("reported", {})
        desired = json_data.get("desired", {})

        # If reported/desired are not in the top level, look in the data
        if not reported and "data" in json_data and isinstance(json_data["data"], dict):
            data_dict = json_data["data"]
            if "state" in data_dict and isinstance(data_dict["state"], dict):
                state = data_dict["state"]
                reported = state.get("reported", {})
                desired = state.get("desired", {})
            elif "reported" in data_dict:
                reported = data_dict["reported"]
            elif "desired" in data_dict:
                desired = data_dict["desired"]

        return cls(
            device_id=json_data.get("device_id", ""),
            operation=json_data.get("operation", "update"),
            reported=reported,
            desired=desired,
            version=json_data.get("version", None),
            timestamp=json_data.get("timestamp", None),
            source=json_data.get("source", "shadow_service"),
        )

    def to_json(self) -> Dict[str, Any]:
        """
        Convert the event to a JSON serializable dictionary.

        Returns:
            A dictionary representation of the event
        """
        result = {
            "device_id": self.device_id,
            "operation": self.operation,
            "reported": self.reported,
            "desired": self.desired,
            "source": self.source,
        }

        if self.version is not None:
            result["version"] = self.version

        if self.timestamp is not None:
            result["timestamp"] = self.timestamp

        return result


@dataclass
class ShadowSubscription:
    """Represents a client subscription to shadow updates."""

    device_id: str
    fields: Optional[List[str]] = None

    def to_request(self) -> Dict[str, Any]:
        """
        Convert the subscription to a request format.

        Returns:
            A dictionary representation of the subscription request
        """
        return {
            "type": "subscribe",
            "device_id": self.device_id,
            "fields": self.fields or ["*"],
        }

    def matches_filter(self, field: str) -> bool:
        """
        Check if a field matches this subscription's filter.

        Args:
            field: The field to check

        Returns:
            True if the field matches the subscription, False otherwise
        """
        if not self.fields or "*" in self.fields:
            return True
        return field in self.fields


@dataclass
class ShadowClientConfig:
    """Configuration for the shadow client adapter."""

    use_message_broker: bool = True
    auto_subscribe_on_connect: bool = True
    default_fields: List[str] = None


class ShadowClientAdapter:
    """
    Adapter for clients to interact with the shadow service.

    Provides a unified interface for clients to subscribe to shadow updates,
    regardless of whether they come from the message broker or direct notifications.
    """

    def __init__(
        self,
        base_url: str,
        device_id: str,
        websocket_factory=None,
        notification_service: Optional[ShadowNotificationService] = None,
        message_broker: Optional[MessageBrokerAdapter] = None,
        config: Optional[ShadowClientConfig] = None,
    ):
        """
        Initialize the shadow client adapter.

        Args:
            base_url: The base URL for WebSocket connections
            device_id: The device ID to subscribe to
            websocket_factory: Optional factory for creating WebSocket connections
            notification_service: Optional shadow notification service for WebSocket notifications
            message_broker: Optional message broker adapter for message-based notifications
            config: Configuration for the adapter
        """
        self.base_url = base_url
        self.device_id = device_id
        self.ws_url = f"{base_url}/{device_id}"
        self.websocket_factory = websocket_factory
        self.notification_service = notification_service
        self.message_broker = message_broker
        self.config = config or ShadowClientConfig()
        self.client_subscriptions = {}  # WebSocket -> Set[str] (device_ids)
        self.broker_subscriptions = (
            {}
        )  # WebSocket -> Dict[str, str] (device_id -> consumer_tag)
        self.websocket = None
        self.is_connected = False
        self.current_state = {}

        # Update handlers to be notified of shadow changes
        self.update_handlers = []

    async def connect(self) -> None:
        """
        Connect to the shadow service WebSocket.

        Creates a WebSocket connection to the shadow service and prepares
        for receiving shadow updates.
        """
        if self.websocket_factory:
            self.websocket = self.websocket_factory(self.ws_url)
        else:
            # Default WebSocket implementation would go here
            raise NotImplementedError("WebSocket factory must be provided")

        # Connect to the WebSocket
        await self.websocket.connect()
        self.is_connected = True

        # Auto-subscribe if configured
        if self.config.auto_subscribe_on_connect:
            await self.subscribe()

        logger.info(f"Connected to shadow service at {self.ws_url}")

    async def disconnect(self) -> None:
        """
        Disconnect from the shadow service WebSocket.

        Closes the WebSocket connection and cleans up resources.
        """
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from shadow service")

    async def subscribe(self, fields: Optional[List[str]] = None) -> None:
        """
        Subscribe to shadow updates for the device.

        Args:
            fields: Optional list of fields to subscribe to, or None for all fields
        """
        if not self.is_connected:
            raise RuntimeError("Must connect before subscribing")

        # Use default fields if not specified
        if fields is None and self.config.default_fields:
            fields = self.config.default_fields

        # Create subscription request
        subscription = ShadowSubscription(self.device_id, fields)
        request = subscription.to_request()

        # Send the subscription request
        await self.websocket.send_json(request)
        logger.info(
            f"Subscribed to shadow updates for device {self.device_id}, fields: {fields or ['*']}"
        )

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from shadow updates for the device.
        """
        if not self.is_connected:
            raise RuntimeError("Must connect before unsubscribing")

        # Create unsubscription request
        request = {"type": "unsubscribe", "device_id": self.device_id}

        # Send the unsubscription request
        await self.websocket.send_json(request)
        logger.info(f"Unsubscribed from shadow updates for device {self.device_id}")

    async def process_message(self) -> Optional[ShadowUpdateEvent]:
        """
        Process a message from the shadow service.

        Receives and parses a message from the WebSocket connection.

        Returns:
            A ShadowUpdateEvent object if a shadow update was received, None otherwise
        """
        if not self.is_connected:
            raise RuntimeError("Must connect before processing messages")

        # Receive a message from the WebSocket
        message = await self.websocket.receive_json()

        # Handle different message types
        message_type = message.get("type")

        if message_type == "shadow_update":
            # Create a ShadowUpdateEvent from the message
            event_data = {
                "device_id": message.get("device_id", self.device_id),
                "operation": message.get("operation", "update"),
                "timestamp": message.get("timestamp", datetime.now().isoformat()),
                "data": {
                    "state": {
                        "reported": message.get("reported", {}),
                        "desired": message.get("desired", {}),
                    },
                    "version": message.get("version", 1),
                },
                "source": message.get("source", "shadow_service"),
            }
            event = ShadowUpdateEvent.from_json(event_data)

            # Notify all update handlers
            for handler in self.update_handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in update handler: {e}")

            return event

        elif message_type == "error":
            # Log error messages
            logger.error(f"Error from shadow service: {message.get('message')}")

        elif message_type == "subscription_confirmed":
            # Log subscription confirmations
            logger.info(f"Subscription confirmed for device {message.get('device_id')}")

        elif message_type == "unsubscription_confirmed":
            # Log unsubscription confirmations
            logger.info(
                f"Unsubscription confirmed for device {message.get('device_id')}"
            )

        # Return None for non-update messages
        return None

    def add_update_handler(self, handler: Callable[[ShadowUpdateEvent], None]) -> None:
        """
        Add a handler to be notified of shadow updates.

        Args:
            handler: A callable that takes a ShadowUpdateEvent parameter
        """
        if handler not in self.update_handlers:
            self.update_handlers.append(handler)

    def remove_update_handler(
        self, handler: Callable[[ShadowUpdateEvent], None]
    ) -> None:
        """
        Remove a previously added update handler.

        Args:
            handler: The handler to remove
        """
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the device shadow.

        Returns:
            The current shadow state
        """
        if not self.is_connected:
            await self.connect()

        # If we have a cached state, return it
        if self.current_state:
            return self.current_state

        # Otherwise, make a request to get the current state
        request = {"type": "get_shadow", "device_id": self.device_id}

        await self.websocket.send_json(request)
        response = await self.websocket.receive_json()

        # Cache the state
        if "reported" in response:
            self.current_state = {
                "reported": response.get("reported", {}),
                "desired": response.get("desired", {}),
                "version": response.get("version", 1),
                "timestamp": response.get("timestamp", datetime.now().isoformat()),
            }

        return self.current_state

    async def update_desired_state(
        self, desired_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the desired state of the device shadow.

        Args:
            desired_state: The desired state to update

        Returns:
            The update result
        """
        if not self.is_connected:
            await self.connect()

        # Create the update request
        request = {
            "type": "update_desired",
            "device_id": self.device_id,
            "desired": desired_state,
        }

        # Send the request
        await self.websocket.send_json(request)
        response = await self.websocket.receive_json()

        # Update the cached state
        if response.get("success", False) and self.current_state:
            self.current_state["desired"].update(desired_state)
            if "version" in response:
                self.current_state["version"] = response["version"]

        return response

    async def create_shadow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new shadow for the device.

        Args:
            initial_state: The initial state of the shadow

        Returns:
            The creation result
        """
        if not self.is_connected:
            await self.connect()

        # Create the creation request
        request = {
            "type": "create_shadow",
            "device_id": self.device_id,
            "state": initial_state,
        }

        # Send the request
        await self.websocket.send_json(request)
        response = await self.websocket.receive_json()

        # Update the cached state
        if response.get("success", False):
            self.current_state = {
                "reported": initial_state.get("reported", {}),
                "desired": initial_state.get("desired", {}),
                "version": response.get("version", 1),
                "timestamp": response.get("timestamp", datetime.now().isoformat()),
            }

        return response


class ShadowClientManager:
    """
    Manager for shadow client connections and subscriptions.

    Provides a higher-level interface for handling client WebSocket connections
    and routing shadow updates to them.
    """

    def __init__(
        self,
        base_url: str,
        notification_service: Optional[ShadowNotificationService] = None,
    ):
        """
        Initialize the shadow client manager.

        Args:
            base_url: The base URL for WebSocket connections
            notification_service: Optional shadow notification service
        """
        self.base_url = base_url
        self.notification_service = notification_service
        self.active_clients = {}  # client_id -> ShadowClientAdapter
        self.client_websockets = {}  # client_id -> websocket

    async def handle_client_connection(
        self, websocket: WebSocket, client_id: str
    ) -> None:
        """
        Handle a new client WebSocket connection.

        Args:
            websocket: The client WebSocket connection
            client_id: A unique identifier for the client
        """
        await websocket.accept()
        self.client_websockets[client_id] = websocket

        # Send a welcome message
        await websocket.send_json(
            {
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to IoTSphere Shadow Service",
            }
        )

        try:
            # Process incoming messages from the client
            while True:
                try:
                    message = await websocket.receive_json()
                    await self._process_client_message(websocket, client_id, message)
                except WebSocketDisconnect:
                    logger.info(f"Client {client_id} disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error processing client message: {e}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Error processing message: {str(e)}",
                        }
                    )
        finally:
            # Clean up when the client disconnects
            await self._disconnect_client(client_id)

    async def _create_client_adapter(
        self, client_id: str, device_id: str
    ) -> ShadowClientAdapter:
        """
        Create a client adapter for a device.

        Args:
            client_id: The client ID
            device_id: The device ID

        Returns:
            A ShadowClientAdapter instance
        """
        websocket = self.client_websockets.get(client_id)
        if not websocket:
            raise ValueError(f"No WebSocket connection for client {client_id}")

        # Factory function to provide the WebSocket
        def websocket_factory(url):
            return websocket

        # Create a new client adapter
        adapter = ShadowClientAdapter(
            base_url=self.base_url,
            device_id=device_id,
            websocket_factory=websocket_factory,
            notification_service=self.notification_service,
        )

        self.active_clients[client_id] = adapter
        return adapter

    async def _disconnect_client(self, client_id: str) -> None:
        """
        Disconnect a client and clean up resources.

        Args:
            client_id: The client ID
        """
        if client_id in self.active_clients:
            # Disconnect client adapter
            try:
                await self.active_clients[client_id].disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting client {client_id}: {e}")
            del self.active_clients[client_id]

        if client_id in self.client_websockets:
            del self.client_websockets[client_id]

        logger.info(f"Client {client_id} disconnected and cleaned up")

    async def _process_client_message(
        self, websocket: WebSocket, client_id: str, message: Dict[str, Any]
    ) -> None:
        """
        Process a message from a client.

        Args:
            websocket: The client WebSocket connection
            client_id: The client ID
            message: The message from the client
        """
        message_type = message.get("type")

        if message_type == "subscribe":
            device_id = message.get("device_id")
            fields = message.get("fields")

            if not device_id:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Missing device_id in subscribe message",
                    }
                )
                return

            # Get or create a client adapter for this device
            if client_id not in self.active_clients:
                adapter = await self._create_client_adapter(client_id, device_id)
            else:
                adapter = self.active_clients[client_id]

            # Subscribe to shadow updates
            await adapter.subscribe(fields)

            # Confirm subscription
            await websocket.send_json(
                {
                    "type": "subscription_confirmed",
                    "device_id": device_id,
                    "fields": fields or ["*"],
                    "message": f"Subscribed to shadow updates for device {device_id}",
                }
            )

        elif message_type == "unsubscribe":
            device_id = message.get("device_id")

            if not device_id:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Missing device_id in unsubscribe message",
                    }
                )
                return

            # Check if we have an adapter for this client
            if client_id in self.active_clients:
                adapter = self.active_clients[client_id]
                await adapter.unsubscribe()

                # Confirm unsubscription
                await websocket.send_json(
                    {
                        "type": "unsubscription_confirmed",
                        "device_id": device_id,
                        "message": f"Unsubscribed from shadow updates for device {device_id}",
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Not subscribed to device {device_id}",
                    }
                )

        elif message_type == "ping":
            await websocket.send_json(
                {"type": "pong", "timestamp": message.get("timestamp")}
            )

        else:
            await websocket.send_json(
                {"type": "error", "message": f"Unknown message type: {message_type}"}
            )

    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        for client_id, websocket in list(self.client_websockets.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                # Client will be removed when their connection handler exits

    async def send_personal_message(
        self, client_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific client.

        Args:
            client_id: The client ID
            message: The message to send

        Returns:
            True if the message was sent, False if the client is not connected
        """
        if client_id in self.client_websockets:
            try:
                await self.client_websockets[client_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                await self._disconnect_client(client_id)
                return False
        return False
