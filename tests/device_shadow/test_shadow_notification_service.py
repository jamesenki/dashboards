"""
Test suite for the Shadow Notification Service following TDD principles.

This test suite defines the expected behavior of the notification service
that delivers shadow changes to clients via WebSockets, with each test focusing
on a single atomic behavior.
"""
import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from src.services.shadow_change_stream_listener import ShadowChangeEvent
from src.services.shadow_notification_service import (
    NotificationManager,
    ShadowNotificationService,
    ShadowSubscription,
)


class TestShadowNotificationService(unittest.TestCase):
    """Test suite for the Shadow Notification Service implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_change_stream_listener = AsyncMock()
        self.service = ShadowNotificationService(
            change_stream_listener=self.mock_change_stream_listener
        )

    def test_initialization_registers_event_handler(self):
        """Test that initialization registers an event handler with the change stream listener."""
        # Assert
        self.mock_change_stream_listener.register_event_handler.assert_called_once_with(
            self.service.handle_shadow_change_event
        )

    def test_initialization_creates_empty_subscriptions_list(self):
        """Test that initialization creates an empty subscriptions list."""
        # Assert
        self.assertIsInstance(self.service.subscriptions, list)
        self.assertEqual(len(self.service.subscriptions), 0)

    @pytest.mark.asyncio
    async def test_handle_shadow_change_event_identifies_matching_subscribers(self):
        """Test that handle_shadow_change_event identifies subscribers for the correct device."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")

        # Create mock subscriptions for different devices
        mock_subscription_matching = create_mock_subscription(device_id)
        mock_subscription_non_matching = create_mock_subscription("different_device")

        self.service.subscriptions = [
            mock_subscription_matching,
            mock_subscription_non_matching,
        ]
        self.service._notify_subscriber = AsyncMock()

        # Act
        await self.service.handle_shadow_change_event(mock_event)

        # Assert
        self.service._notify_subscriber.assert_called_once_with(
            mock_subscription_matching, mock_event
        )
        # Verify non-matching subscription was not notified
        assert mock_subscription_non_matching not in [
            call[0][0] for call in self.service._notify_subscriber.call_args_list
        ]

    @pytest.mark.asyncio
    async def test_handle_shadow_change_event_does_nothing_without_subscribers(self):
        """Test that handle_shadow_change_event does nothing when there are no subscribers."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")
        self.service.subscriptions = []
        self.service._notify_subscriber = AsyncMock()

        # Act
        await self.service.handle_shadow_change_event(mock_event)

        # Assert
        self.service._notify_subscriber.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_notification_data_for_full_document(self):
        """Test that _extract_notification_data extracts the correct data from a full document event."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "insert")
        mock_subscription = create_mock_subscription(
            device_id, ["*"]
        )  # Wildcard subscription

        # Act
        notification_data = self.service._extract_notification_data(
            mock_event, mock_subscription
        )

        # Assert
        self.assertEqual(notification_data["device_id"], device_id)
        self.assertEqual(notification_data["operation"], "insert")
        self.assertEqual(notification_data["reported"]["temperature"], 75)
        self.assertEqual(notification_data["desired"]["temperature"], 72)
        self.assertIsNotNone(notification_data["timestamp"])

    @pytest.mark.asyncio
    async def test_extract_notification_data_filters_fields(self):
        """Test that _extract_notification_data filters fields according to subscription."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")
        mock_subscription = create_mock_subscription(
            device_id, ["reported.temperature"]  # Only subscribe to temperature
        )

        # Act
        notification_data = self.service._extract_notification_data(
            mock_event, mock_subscription
        )

        # Assert
        self.assertEqual(notification_data["device_id"], device_id)
        self.assertEqual(notification_data["operation"], "update")
        # Verify temperature is included
        self.assertIn("reported", notification_data)
        self.assertIn("temperature", notification_data["reported"])
        # Verify humidity is excluded
        self.assertNotIn("humidity", notification_data["reported"])
        # Verify desired state is excluded completely
        self.assertNotIn("desired", notification_data)

    @pytest.mark.asyncio
    async def test_extract_notification_data_includes_all_fields_for_wildcard(self):
        """Test that _extract_notification_data includes all fields for wildcard subscriptions."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")
        mock_subscription = create_mock_subscription(
            device_id, ["*"]
        )  # Wildcard subscription

        # Act
        notification_data = self.service._extract_notification_data(
            mock_event, mock_subscription
        )

        # Assert
        self.assertEqual(notification_data["device_id"], device_id)
        self.assertEqual(notification_data["operation"], "update")
        # Verify all fields are included
        self.assertIn("reported", notification_data)
        self.assertIn("temperature", notification_data["reported"])
        self.assertIn("humidity", notification_data["reported"])
        self.assertIn("desired", notification_data)
        self.assertIn("temperature", notification_data["desired"])

    @pytest.mark.asyncio
    async def test_extract_notification_data_for_delete_operation(self):
        """Test that _extract_notification_data handles delete operations correctly."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "delete")
        mock_subscription = create_mock_subscription(device_id, ["*"])

        # Act
        notification_data = self.service._extract_notification_data(
            mock_event, mock_subscription
        )

        # Assert
        self.assertEqual(notification_data["device_id"], device_id)
        self.assertEqual(notification_data["operation"], "delete")
        # Delete operations should not include reported/desired state
        self.assertNotIn("reported", notification_data)
        self.assertNotIn("desired", notification_data)
        self.assertIsNotNone(notification_data["timestamp"])

    @pytest.mark.asyncio
    async def test_notify_subscriber_sends_notification(self):
        """Test that _notify_subscriber sends a notification to the subscriber."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")
        mock_subscription = create_mock_subscription(device_id)

        # Mock the _extract_notification_data method
        notification_data = {"device_id": device_id, "operation": "update"}
        self.service._extract_notification_data = MagicMock(
            return_value=notification_data
        )

        # Act
        await self.service._notify_subscriber(mock_subscription, mock_event)

        # Assert
        self.service._extract_notification_data.assert_called_once_with(
            mock_event, mock_subscription
        )
        mock_subscription.send_notification.assert_called_once_with(notification_data)

    @pytest.mark.asyncio
    async def test_notify_subscriber_handles_websocket_exceptions(self):
        """Test that _notify_subscriber handles WebSocket exceptions gracefully."""
        # Arrange
        device_id = "device123"
        mock_event = create_mock_shadow_event(device_id, "update")
        mock_subscription = create_mock_subscription(device_id)

        # Mock the _extract_notification_data method
        notification_data = {"device_id": device_id, "operation": "update"}
        self.service._extract_notification_data = MagicMock(
            return_value=notification_data
        )

        # Make the send_notification method raise an exception
        mock_subscription.send_notification.side_effect = WebSocketDisconnect(code=1000)

        # Act - This should not raise an exception
        await self.service._notify_subscriber(mock_subscription, mock_event)

        # Assert
        self.service._extract_notification_data.assert_called_once_with(
            mock_event, mock_subscription
        )
        mock_subscription.send_notification.assert_called_once_with(notification_data)
        # Verify the subscription is still present (cleanup happens separately)
        self.assertIn(mock_subscription, self.service.subscriptions)

    @pytest.mark.asyncio
    async def test_subscribe_creates_new_subscription(self):
        """Test that subscribe creates a new ShadowSubscription object."""
        # Arrange
        device_id = "device123"
        mock_websocket = AsyncMock(spec=WebSocket)
        data_fields = ["reported.temperature"]

        # Act
        await self.service.subscribe(device_id, mock_websocket, data_fields)

        # Assert
        self.assertEqual(len(self.service.subscriptions), 1)
        subscription = self.service.subscriptions[0]
        self.assertIsInstance(subscription, ShadowSubscription)
        self.assertEqual(subscription.device_id, device_id)
        self.assertEqual(subscription.websocket, mock_websocket)
        self.assertEqual(subscription.receive_data_fields, data_fields)

    @pytest.mark.asyncio
    async def test_subscribe_handles_duplicate_websocket(self):
        """Test that subscribe handles a websocket that is already subscribed."""
        # Arrange
        device_id = "device123"
        mock_websocket = AsyncMock(spec=WebSocket)
        data_fields_1 = ["reported.temperature"]
        data_fields_2 = ["reported.temperature", "reported.humidity"]

        # First subscription
        await self.service.subscribe(device_id, mock_websocket, data_fields_1)
        initial_count = len(self.service.subscriptions)

        # Act - Subscribe again with the same websocket but different fields
        await self.service.subscribe(device_id, mock_websocket, data_fields_2)

        # Assert
        self.assertEqual(
            len(self.service.subscriptions), initial_count
        )  # Should still be the same count
        subscription = self.service.subscriptions[0]
        # Should update the fields
        self.assertEqual(subscription.receive_data_fields, data_fields_2)

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_websocket(self):
        """Test that unsubscribe removes a specific websocket subscription."""
        # Arrange
        device_id = "device123"
        mock_websocket_1 = AsyncMock(spec=WebSocket)
        mock_websocket_2 = AsyncMock(spec=WebSocket)

        # Create multiple subscriptions
        await self.service.subscribe(
            device_id, mock_websocket_1, ["reported.temperature"]
        )
        await self.service.subscribe(device_id, mock_websocket_2, ["reported.humidity"])
        initial_count = len(self.service.subscriptions)

        # Act
        await self.service.unsubscribe(mock_websocket_1)

        # Assert
        self.assertEqual(len(self.service.subscriptions), initial_count - 1)
        # Verify the correct subscription was removed
        remaining_websockets = [sub.websocket for sub in self.service.subscriptions]
        self.assertNotIn(mock_websocket_1, remaining_websockets)
        self.assertIn(mock_websocket_2, remaining_websockets)

    @pytest.mark.asyncio
    async def test_unsubscribe_handles_nonexistent_websocket(self):
        """Test that unsubscribe handles a websocket that isn't subscribed."""
        # Arrange
        device_id = "device123"
        mock_websocket_1 = AsyncMock(spec=WebSocket)
        mock_websocket_2 = AsyncMock(spec=WebSocket)  # Not subscribed

        # Create a subscription
        await self.service.subscribe(
            device_id, mock_websocket_1, ["reported.temperature"]
        )
        initial_count = len(self.service.subscriptions)

        # Act - Try to unsubscribe a websocket that isn't subscribed
        await self.service.unsubscribe(mock_websocket_2)

        # Assert - Should not change the subscription count
        self.assertEqual(len(self.service.subscriptions), initial_count)
        # Original subscription should still be there
        self.assertEqual(self.service.subscriptions[0].websocket, mock_websocket_1)

    @pytest.mark.asyncio
    async def test_check_connection_verifies_websocket_alive(self):
        """Test that _check_connection verifies if a websocket is still connected."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_subscription = ShadowSubscription(
            device_id="device123",
            websocket=mock_websocket,
            receive_data_fields=["reported.temperature"],
        )

        # Configure the websocket to respond to a ping
        mock_subscription.is_connected = AsyncMock(return_value=True)

        # Act
        result = await self.service._check_connection(mock_subscription)

        # Assert
        self.assertTrue(result)
        mock_subscription.is_connected.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_connection_identifies_disconnected_websocket(self):
        """Test that _check_connection identifies a disconnected websocket."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_subscription = ShadowSubscription(
            device_id="device123",
            websocket=mock_websocket,
            receive_data_fields=["reported.temperature"],
        )

        # Configure the websocket to fail when pinged
        mock_subscription.is_connected = AsyncMock(return_value=False)

        # Act
        result = await self.service._check_connection(mock_subscription)

        # Assert
        self.assertFalse(result)
        mock_subscription.is_connected.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_disconnected_clients_removes_dead_connections(self):
        """Test that cleanup_disconnected_clients removes disconnected websockets."""
        # Arrange
        mock_websocket_1 = AsyncMock(spec=WebSocket)
        mock_websocket_2 = AsyncMock(spec=WebSocket)

        mock_subscription_1 = ShadowSubscription(
            device_id="device123",
            websocket=mock_websocket_1,
            receive_data_fields=["reported.temperature"],
        )

        mock_subscription_2 = ShadowSubscription(
            device_id="device456",
            websocket=mock_websocket_2,
            receive_data_fields=["reported.humidity"],
        )

        self.service.subscriptions = [mock_subscription_1, mock_subscription_2]

        # Mock _check_connection to return True for subscription_1, False for subscription_2
        original_check_connection = self.service._check_connection
        check_connection_results = {
            mock_subscription_1: True,
            mock_subscription_2: False,
        }

        async def mock_check_connection(subscription):
            return check_connection_results[subscription]

        self.service._check_connection = mock_check_connection

        # Act
        await self.service.cleanup_disconnected_clients()

        # Assert
        self.assertEqual(len(self.service.subscriptions), 1)
        self.assertIn(mock_subscription_1, self.service.subscriptions)
        self.assertNotIn(mock_subscription_2, self.service.subscriptions)

        # Restore original method
        self.service._check_connection = original_check_connection


class TestShadowSubscription(unittest.TestCase):
    """Test suite for the ShadowSubscription class."""

    def setUp(self):
        """Set up test fixtures."""
        self.device_id = "device123"
        self.mock_websocket = AsyncMock(spec=WebSocket)
        self.data_fields = ["reported.temperature", "desired.temperature"]

        self.subscription = ShadowSubscription(
            device_id=self.device_id,
            websocket=self.mock_websocket,
            receive_data_fields=self.data_fields,
        )

    def test_init_sets_properties(self):
        """Test that initialization sets the properties correctly."""
        # Assert
        self.assertEqual(self.subscription.device_id, self.device_id)
        self.assertEqual(self.subscription.websocket, self.mock_websocket)
        self.assertEqual(self.subscription.receive_data_fields, self.data_fields)

    @pytest.mark.asyncio
    async def test_send_notification_serializes_data(self):
        """Test that send_notification serializes the data correctly."""
        # Arrange
        notification_data = {
            "device_id": self.device_id,
            "operation": "update",
            "reported": {"temperature": 75},
            "timestamp": datetime.now().isoformat(),
        }

        # Act
        await self.subscription.send_notification(notification_data)

        # Assert
        self.mock_websocket.send_text.assert_called_once()
        # Check that the data was serialized to JSON
        sent_json = self.mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(sent_json)
        self.assertEqual(sent_data, notification_data)

    @pytest.mark.asyncio
    async def test_send_notification_handles_serialization_error(self):
        """Test that send_notification handles serialization errors."""
        # Arrange
        notification_data = {
            "device_id": self.device_id,
            "operation": "update",
            "reported": {"temperature": 75},
            "timestamp": datetime.now(),  # Not JSON serializable
        }

        # Act & Assert
        with pytest.raises(TypeError):
            await self.subscription.send_notification(notification_data)

    @pytest.mark.asyncio
    async def test_is_connected_checks_websocket_state(self):
        """Test that is_connected checks the WebSocket state."""
        # Act
        await self.subscription.is_connected()

        # Assert
        self.mock_websocket.send_text.assert_called_once()
        self.assertTrue(await self.subscription.is_connected())

    @pytest.mark.asyncio
    async def test_is_connected_detects_disconnected_websocket(self):
        """Test that is_connected detects a disconnected WebSocket."""
        # Arrange
        self.mock_websocket.send_text.side_effect = WebSocketDisconnect(code=1000)

        # Act & Assert
        self.assertFalse(await self.subscription.is_connected())

    def test_matches_device_id_returns_true_for_match(self):
        """Test that matches_device_id returns True for a matching device ID."""
        # Act & Assert
        self.assertTrue(self.subscription.matches_device_id(self.device_id))

    def test_matches_device_id_returns_false_for_mismatch(self):
        """Test that matches_device_id returns False for a non-matching device ID."""
        # Act & Assert
        self.assertFalse(self.subscription.matches_device_id("different_device"))

    def test_field_is_subscribed_checks_field_subscription(self):
        """Test that field_is_subscribed checks if a field is in the subscription."""
        # Act & Assert
        self.assertTrue(self.subscription.field_is_subscribed("reported.temperature"))
        self.assertTrue(self.subscription.field_is_subscribed("desired.temperature"))
        self.assertFalse(self.subscription.field_is_subscribed("reported.humidity"))

    def test_field_is_subscribed_handles_wildcard(self):
        """Test that field_is_subscribed handles wildcard subscriptions."""
        # Arrange
        subscription = ShadowSubscription(
            device_id=self.device_id,
            websocket=self.mock_websocket,
            receive_data_fields=["*"],
        )

        # Act & Assert
        self.assertTrue(subscription.field_is_subscribed("reported.temperature"))
        self.assertTrue(subscription.field_is_subscribed("reported.humidity"))
        self.assertTrue(subscription.field_is_subscribed("desired.anything"))


class TestNotificationManager(unittest.TestCase):
    """Test suite for the NotificationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = NotificationManager()

    @pytest.mark.asyncio
    async def test_connect_adds_client(self):
        """Test that connect adds a client to active connections."""
        # Arrange
        client_id = "client123"
        mock_websocket = AsyncMock(spec=WebSocket)

        # Act
        await self.manager.connect(client_id, mock_websocket)

        # Assert
        self.assertIn(client_id, self.manager.active_connections)
        self.assertEqual(self.manager.active_connections[client_id], mock_websocket)

    @pytest.mark.asyncio
    async def test_connect_replaces_existing_client(self):
        """Test that connect replaces an existing client connection."""
        # Arrange
        client_id = "client123"
        mock_websocket_1 = AsyncMock(spec=WebSocket)
        mock_websocket_2 = AsyncMock(spec=WebSocket)

        # First connection
        await self.manager.connect(client_id, mock_websocket_1)

        # Act - New connection with same ID
        await self.manager.connect(client_id, mock_websocket_2)

        # Assert
        self.assertEqual(self.manager.active_connections[client_id], mock_websocket_2)

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self):
        """Test that disconnect removes a client from active connections."""
        # Arrange
        client_id = "client123"
        mock_websocket = AsyncMock(spec=WebSocket)
        await self.manager.connect(client_id, mock_websocket)

        # Act
        await self.manager.disconnect(client_id)

        # Assert
        self.assertNotIn(client_id, self.manager.active_connections)

    @pytest.mark.asyncio
    async def test_disconnect_handles_nonexistent_client(self):
        """Test that disconnect handles a nonexistent client."""
        # Act - Should not raise an exception
        await self.manager.disconnect("nonexistent_client")

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        """Test that broadcast sends a message to all connected clients."""
        # Arrange
        client_ids = ["client1", "client2", "client3"]
        mock_websockets = [AsyncMock(spec=WebSocket) for _ in range(3)]

        # Connect three clients
        for i, client_id in enumerate(client_ids):
            await self.manager.connect(client_id, mock_websockets[i])

        message = {"event": "test", "data": "test_data"}

        # Act
        await self.manager.broadcast(message)

        # Assert
        for websocket in mock_websockets:
            websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self):
        """Test that broadcast properly handles disconnected clients."""
        # Arrange
        client_ids = ["client1", "client2"]
        mock_websockets = [AsyncMock(spec=WebSocket) for _ in range(2)]

        # Connect two clients
        for i, client_id in enumerate(client_ids):
            await self.manager.connect(client_id, mock_websockets[i])

        # Make the first websocket raise an exception when sending
        mock_websockets[0].send_json.side_effect = WebSocketDisconnect(code=1000)

        message = {"event": "test", "data": "test_data"}

        # Act
        await self.manager.broadcast(message)

        # Assert
        # First client should be disconnected
        self.assertNotIn(client_ids[0], self.manager.active_connections)
        # Second client should still be connected
        self.assertIn(client_ids[1], self.manager.active_connections)
        mock_websockets[1].send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test that send_personal_message sends to a specific client."""
        # Arrange
        client_id = "client123"
        mock_websocket = AsyncMock(spec=WebSocket)
        await self.manager.connect(client_id, mock_websocket)

        message = {"event": "test", "data": "test_data"}

        # Act
        await self.manager.send_personal_message(client_id, message)

        # Assert
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_handles_nonexistent_client(self):
        """Test that send_personal_message handles a nonexistent client."""
        # Arrange
        message = {"event": "test", "data": "test_data"}

        # Act - Should not raise an exception
        await self.manager.send_personal_message("nonexistent_client", message)

    @pytest.mark.asyncio
    async def test_send_personal_message_handles_disconnected_client(self):
        """Test that send_personal_message handles a disconnected client."""
        # Arrange
        client_id = "client123"
        mock_websocket = AsyncMock(spec=WebSocket)
        await self.manager.connect(client_id, mock_websocket)

        # Make the websocket raise an exception when sending
        mock_websocket.send_json.side_effect = WebSocketDisconnect(code=1000)

        message = {"event": "test", "data": "test_data"}

        # Act
        await self.manager.send_personal_message(client_id, message)

        # Assert
        # Client should be disconnected
        self.assertNotIn(client_id, self.manager.active_connections)


# Helper functions for creating test fixtures


def create_mock_shadow_event(device_id, operation_type):
    """Create a mock ShadowChangeEvent for testing."""
    event = MagicMock(spec=ShadowChangeEvent)
    event.device_id = device_id
    event.operation_type = operation_type
    event.timestamp = datetime.now().isoformat()

    if operation_type != "delete":
        event.full_document = {
            "reported": {"temperature": 75, "humidity": 50},
            "desired": {"temperature": 72},
        }

        if operation_type == "update":
            event.changed_fields = {"reported.temperature": 75}
    else:
        event.full_document = None
        event.changed_fields = None

    return event


def create_mock_subscription(device_id, fields=None):
    """Create a mock ShadowSubscription for testing."""
    if fields is None:
        fields = ["reported.temperature", "reported.humidity"]

    subscription = MagicMock(spec=ShadowSubscription)
    subscription.device_id = device_id
    subscription.receive_data_fields = fields
    subscription.matches_device_id = lambda d: d == device_id
    subscription.field_is_subscribed = lambda f: f in fields or "*" in fields
    subscription.send_notification = AsyncMock()
    subscription.is_connected = AsyncMock(return_value=True)

    return subscription


if __name__ == "__main__":
    unittest.main()
