"""
Shadow Notification Service for IoTSphere platform.

This service listens for shadow change events from the MongoDB change stream
and notifies subscribed clients via WebSockets in real-time.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from src.services.shadow_change_stream_listener import (
    ShadowChangeEvent,
    ShadowChangeStreamListener,
)

logger = logging.getLogger(__name__)


class ShadowSubscription:
    """
    Represents a client subscription to shadow updates for a specific device.

    Handles filtering of updates based on the fields the client is interested in
    and manages the WebSocket connection for delivering notifications.
    """

    def __init__(
        self,
        device_id: str,
        websocket: WebSocket,
        receive_data_fields: List[str] = None,
    ):
        """
        Initialize a shadow subscription.

        Args:
            device_id: The ID of the device to subscribe to
            websocket: The client's WebSocket connection
            receive_data_fields: List of fields to include in notifications (e.g., 'reported.temperature')
                                If None or empty, all fields will be included
        """
        self.device_id = device_id
        self.websocket = websocket
        self.receive_data_fields = receive_data_fields or ["*"]  # Default to all fields

    async def send_notification(self, notification_data: Dict[str, Any]) -> None:
        """
        Send a notification to the subscribed client.

        Args:
            notification_data: The notification data to send
        """
        try:
            await self.websocket.send_text(json.dumps(notification_data))
        except Exception as e:
            logger.error(f"Error sending notification to client: {e}")
            raise

    async def is_connected(self) -> bool:
        """
        Check if the WebSocket connection is still active.

        Returns:
            True if the connection is active, False otherwise
        """
        try:
            # Send a ping to check if the connection is still active
            await self.websocket.send_text(json.dumps({"type": "ping"}))
            return True
        except WebSocketDisconnect:
            return False
        except Exception as e:
            logger.error(f"Error checking WebSocket connection: {e}")
            return False

    def matches_device_id(self, device_id: str) -> bool:
        """
        Check if this subscription matches the given device ID.

        Args:
            device_id: The device ID to check

        Returns:
            True if this subscription is for the given device ID
        """
        return self.device_id == device_id

    def field_is_subscribed(self, field: str) -> bool:
        """
        Check if this subscription includes the given field.

        Args:
            field: The field to check (e.g., 'reported.temperature')

        Returns:
            True if this subscription includes the given field
        """
        if "*" in self.receive_data_fields:
            return True

        return field in self.receive_data_fields


class NotificationManager:
    """
    Manages WebSocket connections for real-time notifications.

    Handles broadcasting messages to all connected clients or sending
    messages to specific clients.
    """

    def __init__(self):
        """Initialize the notification manager."""
        self.active_connections = {}  # client_id -> websocket

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        Register a new client connection.

        Args:
            client_id: A unique identifier for the client
            websocket: The client's WebSocket connection
        """
        self.active_connections[client_id] = websocket
        logger.debug(f"Client {client_id} connected")

    async def disconnect(self, client_id: str) -> None:
        """
        Remove a client connection.

        Args:
            client_id: The client ID to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.debug(f"Client {client_id} disconnected")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def send_personal_message(
        self, client_id: str, message: Dict[str, Any]
    ) -> None:
        """
        Send a message to a specific client.

        Args:
            client_id: The client ID to send the message to
            message: The message to send
        """
        if client_id not in self.active_connections:
            return

        try:
            await self.active_connections[client_id].send_json(message)
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)


class ShadowNotificationService:
    """
    Shadow notification service for real-time updates using CDC.

    This service:
    1. Listens for shadow changes via MongoDB change streams
    2. Notifies subscribed clients via WebSockets
    3. Handles client subscriptions with field filtering
    """

    def __init__(self, change_stream_listener: ShadowChangeStreamListener):
        """
        Initialize the shadow notification service.

        Args:
            change_stream_listener: The change stream listener to get updates from
        """
        self.change_stream_listener = change_stream_listener
        self.subscriptions = []  # List of ShadowSubscription objects
        self.change_stream_listener.register_event_handler(
            self.handle_shadow_change_event
        )
        logger.info(
            "Shadow Notification Service initialized with Change Stream Listener"
        )

    async def handle_shadow_change_event(self, event: ShadowChangeEvent) -> None:
        """
        Handle a shadow change event from the change stream.

        Notifies all subscribed clients that are interested in this device's shadow.

        Args:
            event: The shadow change event
        """
        device_id = event.device_id
        logger.debug(f"Shadow change event received for {device_id}")

        # Find all subscriptions for this device
        matching_subscriptions = [
            sub for sub in self.subscriptions if sub.matches_device_id(device_id)
        ]

        # Notify each subscription
        for subscription in matching_subscriptions:
            await self._notify_subscriber(subscription, event)

    async def _notify_subscriber(
        self, subscription: ShadowSubscription, event: ShadowChangeEvent
    ) -> None:
        """
        Notify a subscriber of a shadow change event.

        Args:
            subscription: The subscription to notify
            event: The shadow change event
        """
        try:
            # Extract relevant data based on the subscription's field filter
            notification_data = self._extract_notification_data(event, subscription)

            # Send the notification
            await subscription.send_notification(notification_data)
            logger.debug(f"Notification sent to client for {event.device_id}")

        except WebSocketDisconnect:
            logger.debug(
                f"Client disconnected while sending notification for {event.device_id}"
            )
        except Exception as e:
            logger.error(f"Error notifying client for {event.device_id}: {e}")

    def _extract_notification_data(
        self, event: ShadowChangeEvent, subscription: ShadowSubscription
    ) -> Dict[str, Any]:
        """
        Extract notification data based on the subscription's field filter.

        Args:
            event: The shadow change event
            subscription: The subscription to filter for

        Returns:
            The filtered notification data
        """
        # Base notification data
        notification_data = {
            "device_id": event.device_id,
            "operation": event.operation_type,
            "timestamp": event.timestamp,
        }

        # Add shadow state for insert/update operations
        if event.operation_type in ["insert", "update"] and event.full_document:
            # Extract reported state if appropriate
            if "reported" in event.full_document and any(
                subscription.field_is_subscribed(f"reported.{field}")
                or subscription.field_is_subscribed("*")
                for field in event.full_document["reported"]
            ):
                notification_data["reported"] = {}
                for field, value in event.full_document["reported"].items():
                    if subscription.field_is_subscribed(
                        f"reported.{field}"
                    ) or subscription.field_is_subscribed("*"):
                        notification_data["reported"][field] = value

            # Extract desired state if appropriate
            if "desired" in event.full_document and any(
                subscription.field_is_subscribed(f"desired.{field}")
                or subscription.field_is_subscribed("*")
                for field in event.full_document["desired"]
            ):
                notification_data["desired"] = {}
                for field, value in event.full_document["desired"].items():
                    if subscription.field_is_subscribed(
                        f"desired.{field}"
                    ) or subscription.field_is_subscribed("*"):
                        notification_data["desired"][field] = value

        return notification_data

    async def subscribe(
        self, device_id: str, websocket: WebSocket, data_fields: List[str] = None
    ) -> None:
        """
        Subscribe a client to shadow updates for a specific device.

        Args:
            device_id: The device ID to subscribe to
            websocket: The client's WebSocket connection
            data_fields: List of fields to include in notifications (e.g., 'reported.temperature')
        """
        # Check if this websocket is already subscribed
        for i, sub in enumerate(self.subscriptions):
            if sub.websocket == websocket:
                # Update the existing subscription
                self.subscriptions[i] = ShadowSubscription(
                    device_id, websocket, data_fields
                )
                logger.debug(f"Updated subscription for {device_id}")
                return

        # Create a new subscription
        subscription = ShadowSubscription(device_id, websocket, data_fields)
        self.subscriptions.append(subscription)
        logger.debug(f"New subscription created for {device_id}")

    async def unsubscribe(self, websocket: WebSocket) -> None:
        """
        Unsubscribe a client from all shadow updates.

        Args:
            websocket: The client's WebSocket connection
        """
        self.subscriptions = [
            sub for sub in self.subscriptions if sub.websocket != websocket
        ]
        logger.debug("Client unsubscribed from shadow updates")

    async def _check_connection(self, subscription: ShadowSubscription) -> bool:
        """
        Check if a subscription's WebSocket connection is still active.

        Args:
            subscription: The subscription to check

        Returns:
            True if the connection is active, False otherwise
        """
        return await subscription.is_connected()

    async def cleanup_disconnected_clients(self) -> None:
        """Remove subscriptions for disconnected clients."""
        connected_subscriptions = []

        for subscription in self.subscriptions:
            if await self._check_connection(subscription):
                connected_subscriptions.append(subscription)

        removed_count = len(self.subscriptions) - len(connected_subscriptions)
        self.subscriptions = connected_subscriptions

        if removed_count > 0:
            logger.debug(f"Removed {removed_count} disconnected client subscriptions")
