"""
Test suite for the client-side Shadow Adapter following TDD principles.

This test suite defines the expected behavior of the shadow client adapter
that receives shadow updates via WebSockets.
"""
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.client.shadow_client_adapter import (
    ShadowClientAdapter,
    ShadowSubscription,
    ShadowUpdateEvent,
)


class TestShadowClientAdapter(unittest.TestCase):
    """Test suite for the Shadow Client Adapter implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_websocket = MagicMock()
        self.mock_websocket.url = "ws://localhost:8006/api/ws/shadows/device123"

        self.adapter = ShadowClientAdapter(
            base_url="ws://localhost:8006/api/ws/shadows",
            device_id="device123",
            websocket_factory=lambda url: self.mock_websocket,
        )

    def test_initialization_sets_correct_websocket_url(self):
        """Test that initialization sets the correct WebSocket URL."""
        # Assert
        self.assertEqual(
            self.adapter.ws_url, "ws://localhost:8006/api/ws/shadows/device123"
        )

    @pytest.mark.asyncio
    async def test_connect_establishes_websocket_connection(self):
        """Test that connect establishes a WebSocket connection."""
        # Act
        await self.adapter.connect()

        # Assert
        self.mock_websocket.connect.assert_called_once()
        self.assertTrue(self.adapter.is_connected)

    @pytest.mark.asyncio
    async def test_disconnect_closes_websocket_connection(self):
        """Test that disconnect closes the WebSocket connection."""
        # Arrange
        self.adapter.is_connected = True

        # Act
        await self.adapter.disconnect()

        # Assert
        self.mock_websocket.close.assert_called_once()
        self.assertFalse(self.adapter.is_connected)

    @pytest.mark.asyncio
    async def test_subscribe_sends_subscription_request(self):
        """Test that subscribe sends a subscription request."""
        # Arrange
        fields = ["reported.temperature", "desired.temperature"]

        # Act
        await self.adapter.subscribe(fields)

        # Assert
        self.mock_websocket.send_json.assert_called_once()

        # Check subscription message
        message = self.mock_websocket.send_json.call_args[0][0]
        self.assertEqual(message["type"], "subscribe")
        self.assertEqual(message["device_id"], "device123")
        self.assertEqual(message["fields"], fields)

    @pytest.mark.asyncio
    async def test_unsubscribe_sends_unsubscribe_request(self):
        """Test that unsubscribe sends an unsubscribe request."""
        # Act
        await self.adapter.unsubscribe()

        # Assert
        self.mock_websocket.send_json.assert_called_once()

        # Check unsubscribe message
        message = self.mock_websocket.send_json.call_args[0][0]
        self.assertEqual(message["type"], "unsubscribe")
        self.assertEqual(message["device_id"], "device123")

    @pytest.mark.asyncio
    async def test_on_message_handles_shadow_update(self):
        """Test that _on_message handles shadow update messages."""
        # Arrange
        timestamp = datetime.now().isoformat()
        message_data = {
            "device_id": "device123",
            "operation": "update",
            "reported": {"temperature": 75},
            "desired": {"temperature": 70},
            "version": 2,
            "timestamp": timestamp,
        }
        message = json.dumps(message_data)

        # Create a mock update handler
        mock_handler = MagicMock()
        self.adapter.add_update_handler(mock_handler)

        # Act
        await self.adapter._on_message(message)

        # Assert
        mock_handler.assert_called_once()

        # Check event data
        event = mock_handler.call_args[0][0]
        self.assertIsInstance(event, ShadowUpdateEvent)
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation, "update")
        self.assertEqual(event.reported["temperature"], 75)
        self.assertEqual(event.desired["temperature"], 70)
        self.assertEqual(event.version, 2)
        self.assertEqual(event.timestamp, timestamp)

    @pytest.mark.asyncio
    async def test_on_message_handles_invalid_message(self):
        """Test that _on_message handles invalid messages gracefully."""
        # Arrange
        invalid_message = "not valid json"

        # Create a mock error handler
        mock_error_handler = MagicMock()
        self.adapter.on_error = mock_error_handler

        # Act
        await self.adapter._on_message(invalid_message)

        # Assert
        mock_error_handler.assert_called_once()
        error = mock_error_handler.call_args[0][0]
        self.assertIsInstance(error, Exception)

    @pytest.mark.asyncio
    async def test_on_close_handles_websocket_closure(self):
        """Test that _on_close handles WebSocket closure."""
        # Arrange
        code = 1000
        reason = "Normal closure"

        # Create a mock close handler
        mock_close_handler = MagicMock()
        self.adapter.on_close = mock_close_handler

        # Act
        await self.adapter._on_close(code, reason)

        # Assert
        mock_close_handler.assert_called_once_with(code, reason)
        self.assertFalse(self.adapter.is_connected)

    @pytest.mark.asyncio
    async def test_reconnect_attempts_to_reconnect(self):
        """Test that reconnect attempts to reconnect to the WebSocket."""
        # Arrange
        self.adapter.is_connected = False
        self.adapter.connect = MagicMock()
        self.adapter.connect.return_value = True

        # Act
        result = await self.adapter.reconnect()

        # Assert
        self.adapter.connect.assert_called_once()
        self.assertTrue(result)

    def test_add_update_handler_registers_handler(self):
        """Test that add_update_handler registers a handler."""
        # Arrange
        handler = MagicMock()
        self.adapter.update_handlers = []

        # Act
        self.adapter.add_update_handler(handler)

        # Assert
        self.assertIn(handler, self.adapter.update_handlers)

    def test_remove_update_handler_unregisters_handler(self):
        """Test that remove_update_handler unregisters a handler."""
        # Arrange
        handler = MagicMock()
        self.adapter.update_handlers = [handler]

        # Act
        self.adapter.remove_update_handler(handler)

        # Assert
        self.assertNotIn(handler, self.adapter.update_handlers)

    @pytest.mark.asyncio
    async def test_start_processing_begins_message_processing(self):
        """Test that start_processing begins WebSocket message processing."""
        # Arrange
        self.adapter.is_processing = False
        self.adapter._process_messages = MagicMock()

        # Act
        await self.adapter.start_processing()

        # Assert
        self.adapter._process_messages.assert_called_once()
        self.assertTrue(self.adapter.is_processing)

    @pytest.mark.asyncio
    async def test_stop_processing_ends_message_processing(self):
        """Test that stop_processing ends WebSocket message processing."""
        # Arrange
        self.adapter.is_processing = True

        # Act
        await self.adapter.stop_processing()

        # Assert
        self.assertFalse(self.adapter.is_processing)

    @pytest.mark.asyncio
    async def test_get_full_shadow_fetches_complete_shadow(self):
        """Test that get_full_shadow fetches the complete shadow document."""
        # Arrange
        timestamp = datetime.now().isoformat()
        shadow_data = {
            "device_id": "device123",
            "reported": {"temperature": 75, "humidity": 50},
            "desired": {"temperature": 70},
            "version": 2,
            "timestamp": timestamp,
        }

        # Mock the response
        self.mock_websocket.receive_json.return_value = {
            "type": "shadow",
            "data": shadow_data,
        }

        # Act
        result = await self.adapter.get_full_shadow()

        # Assert
        self.mock_websocket.send_json.assert_called_once()

        # Check request message
        request = self.mock_websocket.send_json.call_args[0][0]
        self.assertEqual(request["type"], "get_shadow")
        self.assertEqual(request["device_id"], "device123")

        # Check result
        self.assertEqual(result["device_id"], "device123")
        self.assertEqual(result["reported"]["temperature"], 75)
        self.assertEqual(result["desired"]["temperature"], 70)
        self.assertEqual(result["version"], 2)


class TestShadowUpdateEvent(unittest.TestCase):
    """Test suite for the ShadowUpdateEvent class."""

    def test_from_json_with_valid_data(self):
        """Test that from_json creates an event from valid JSON data."""
        # Arrange
        timestamp = datetime.now().isoformat()
        json_data = {
            "device_id": "device123",
            "operation": "update",
            "reported": {"temperature": 75},
            "desired": {"temperature": 70},
            "version": 2,
            "timestamp": timestamp,
        }

        # Act
        event = ShadowUpdateEvent.from_json(json_data)

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation, "update")
        self.assertEqual(event.reported["temperature"], 75)
        self.assertEqual(event.desired["temperature"], 70)
        self.assertEqual(event.version, 2)
        self.assertEqual(event.timestamp, timestamp)

    def test_from_json_with_missing_fields(self):
        """Test that from_json handles missing fields gracefully."""
        # Arrange
        json_data = {
            "device_id": "device123",
            "operation": "update"
            # Missing other fields
        }

        # Act
        event = ShadowUpdateEvent.from_json(json_data)

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation, "update")
        self.assertEqual(event.reported, {})
        self.assertEqual(event.desired, {})
        self.assertIsNone(event.version)
        self.assertIsNone(event.timestamp)

    def test_to_json_serializes_event(self):
        """Test that to_json serializes the event correctly."""
        # Arrange
        timestamp = datetime.now().isoformat()
        event = ShadowUpdateEvent(
            device_id="device123",
            operation="update",
            reported={"temperature": 75},
            desired={"temperature": 70},
            version=2,
            timestamp=timestamp,
        )

        # Act
        json_data = event.to_json()

        # Assert
        self.assertEqual(json_data["device_id"], "device123")
        self.assertEqual(json_data["operation"], "update")
        self.assertEqual(json_data["reported"]["temperature"], 75)
        self.assertEqual(json_data["desired"]["temperature"], 70)
        self.assertEqual(json_data["version"], 2)
        self.assertEqual(json_data["timestamp"], timestamp)


class TestShadowSubscription(unittest.TestCase):
    """Test suite for the ShadowSubscription class."""

    def setUp(self):
        """Set up test fixtures."""
        self.device_id = "device123"
        self.fields = ["reported.temperature", "desired.temperature"]

        self.subscription = ShadowSubscription(
            device_id=self.device_id, fields=self.fields
        )

    def test_to_request_creates_subscription_request(self):
        """Test that to_request creates a proper subscription request."""
        # Act
        request = self.subscription.to_request()

        # Assert
        self.assertEqual(request["type"], "subscribe")
        self.assertEqual(request["device_id"], self.device_id)
        self.assertEqual(request["fields"], self.fields)

    def test_matches_filter_checks_field_match(self):
        """Test that matches_filter correctly checks if a field matches the subscription."""
        # Test cases
        test_cases = [
            {"field": "reported.temperature", "expected": True},
            {"field": "desired.temperature", "expected": True},
            {"field": "reported.humidity", "expected": False},
        ]

        # Test each case
        for case in test_cases:
            field = case["field"]
            expected = case["expected"]

            result = self.subscription.matches_filter(field)
            self.assertEqual(
                result, expected, f"Field '{field}' match should be {expected}"
            )

    def test_matches_filter_with_wildcard(self):
        """Test that matches_filter correctly handles wildcard subscriptions."""
        # Arrange
        subscription = ShadowSubscription(
            device_id=self.device_id, fields=["*"]  # Wildcard subscription
        )

        # Act & Assert
        self.assertTrue(subscription.matches_filter("reported.temperature"))
        self.assertTrue(subscription.matches_filter("anything.else"))


if __name__ == "__main__":
    unittest.main()
