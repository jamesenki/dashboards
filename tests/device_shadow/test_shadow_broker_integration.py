"""
Test suite for the integration between Change Data Capture and Message Broker.

This test suite validates that the shadow change events are properly
transformed into broker messages and delivered to clients.
"""
import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from src.infrastructure.messaging.message_broker_adapter import (
    MessageBrokerAdapter,
    MessagePublishRequest,
)
from src.infrastructure.messaging.shadow_broker_integration import (
    ShadowBrokerIntegration,
    ShadowTopicMapper,
)
from src.services.shadow_change_stream_listener import ShadowChangeEvent


class TestShadowBrokerIntegration(unittest.TestCase):
    """Test suite for the shadow broker integration implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_change_stream_listener = AsyncMock()
        self.mock_message_broker = AsyncMock(spec=MessageBrokerAdapter)

        self.integration = ShadowBrokerIntegration(
            change_stream_listener=self.mock_change_stream_listener,
            message_broker=self.mock_message_broker,
            topic_prefix="iotsphere.devices",
        )

    def test_initialization_registers_change_handler(self):
        """Test that initialization registers a change handler with the change stream listener."""
        # Assert
        self.mock_change_stream_listener.register_event_handler.assert_called_once_with(
            self.integration.handle_shadow_change_event
        )

    @pytest.mark.asyncio
    async def test_handle_shadow_change_event_publishes_message(self):
        """Test that handle_shadow_change_event publishes messages to the broker."""
        # Arrange
        device_id = "device123"
        timestamp = datetime.now().isoformat()

        # Create a sample change event
        change_event = ShadowChangeEvent(
            device_id=device_id,
            operation_type="update",
            full_document={
                "reported": {"temperature": 75},
                "desired": {"temperature": 70},
                "version": 2,
                "timestamp": timestamp,
            },
            changed_fields={
                "reported.temperature": 75,
                "version": 2,
                "timestamp": timestamp,
            },
            timestamp=timestamp,
        )

        # Act
        await self.integration.handle_shadow_change_event(change_event)

        # Assert
        self.mock_message_broker.publish.assert_called_once()

        # Check the publish request
        publish_request = self.mock_message_broker.publish.call_args[0][0]
        self.assertIsInstance(publish_request, MessagePublishRequest)

        # Verify topic
        expected_topic = f"iotsphere.devices.{device_id}.shadow.update"
        self.assertEqual(publish_request.topic, expected_topic)

        # Verify message content
        message = publish_request.message
        self.assertEqual(message["device_id"], device_id)
        self.assertEqual(message["operation"], "update")
        self.assertEqual(message["reported"]["temperature"], 75)
        self.assertEqual(message["desired"]["temperature"], 70)
        self.assertEqual(message["version"], 2)
        self.assertEqual(message["timestamp"], timestamp)

        # Verify message properties
        self.assertEqual(publish_request.content_type, "application/json")
        self.assertIsNotNone(publish_request.message_id)
        self.assertEqual(publish_request.headers["source"], "shadow_service")

    @pytest.mark.asyncio
    async def test_handle_insert_event(self):
        """Test that handle_shadow_change_event handles insert events correctly."""
        # Arrange
        device_id = "device123"
        timestamp = datetime.now().isoformat()

        # Create a sample insert event
        change_event = ShadowChangeEvent(
            device_id=device_id,
            operation_type="insert",
            full_document={
                "reported": {"temperature": 72},
                "desired": {"temperature": 70},
                "version": 1,
                "timestamp": timestamp,
            },
            changed_fields=None,
            timestamp=timestamp,
        )

        # Act
        await self.integration.handle_shadow_change_event(change_event)

        # Assert
        self.mock_message_broker.publish.assert_called_once()

        # Check the publish request
        publish_request = self.mock_message_broker.publish.call_args[0][0]

        # Verify topic
        expected_topic = f"iotsphere.devices.{device_id}.shadow.created"
        self.assertEqual(publish_request.topic, expected_topic)

        # Verify message content
        message = publish_request.message
        self.assertEqual(message["operation"], "created")
        self.assertEqual(message["reported"]["temperature"], 72)

    @pytest.mark.asyncio
    async def test_handle_delete_event(self):
        """Test that handle_shadow_change_event handles delete events correctly."""
        # Arrange
        device_id = "device123"
        timestamp = datetime.now().isoformat()

        # Create a sample delete event
        change_event = ShadowChangeEvent(
            device_id=device_id,
            operation_type="delete",
            full_document=None,
            changed_fields=None,
            timestamp=timestamp,
        )

        # Act
        await self.integration.handle_shadow_change_event(change_event)

        # Assert
        self.mock_message_broker.publish.assert_called_once()

        # Check the publish request
        publish_request = self.mock_message_broker.publish.call_args[0][0]

        # Verify topic
        expected_topic = f"iotsphere.devices.{device_id}.shadow.deleted"
        self.assertEqual(publish_request.topic, expected_topic)

        # Verify message content
        message = publish_request.message
        self.assertEqual(message["device_id"], device_id)
        self.assertEqual(message["operation"], "deleted")
        self.assertEqual(message["timestamp"], timestamp)

    @pytest.mark.asyncio
    async def test_handle_shadow_change_event_with_invalid_event(self):
        """Test that handle_shadow_change_event handles invalid events gracefully."""
        # Arrange
        device_id = "device123"

        # Create an invalid event
        change_event = ShadowChangeEvent(
            device_id=device_id,
            operation_type="invalid_operation",
            full_document=None,
            changed_fields=None,
            timestamp=None,
        )

        # Act
        await self.integration.handle_shadow_change_event(change_event)

        # Assert
        self.mock_message_broker.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_shadow_change_specific_field_event(self):
        """Test that handle_shadow_change_event publishes specific field change messages."""
        # Arrange
        device_id = "device123"
        timestamp = datetime.now().isoformat()

        # Create a sample update event with only temperature change
        change_event = ShadowChangeEvent(
            device_id=device_id,
            operation_type="update",
            full_document={
                "reported": {"temperature": 75, "humidity": 50, "power": "on"},
                "desired": {"temperature": 70},
                "version": 2,
                "timestamp": timestamp,
            },
            changed_fields={
                "reported.temperature": 75,
                "version": 2,
                "timestamp": timestamp,
            },
            timestamp=timestamp,
        )

        # Act
        await self.integration.handle_shadow_change_event(change_event)

        # Assert
        # Should have two publish calls - one for the general update and one for the specific field
        self.assertEqual(self.mock_message_broker.publish.call_count, 2)

        # First call should be the general update
        publish_request_1 = self.mock_message_broker.publish.call_args_list[0][0][0]
        self.assertEqual(
            publish_request_1.topic, f"iotsphere.devices.{device_id}.shadow.update"
        )

        # Second call should be the specific field update
        publish_request_2 = self.mock_message_broker.publish.call_args_list[1][0][0]
        self.assertEqual(
            publish_request_2.topic,
            f"iotsphere.devices.{device_id}.shadow.reported.temperature",
        )

        # Check the specific field message content
        field_message = publish_request_2.message
        self.assertEqual(field_message["device_id"], device_id)
        self.assertEqual(field_message["field"], "temperature")
        self.assertEqual(field_message["value"], 75)
        self.assertEqual(field_message["timestamp"], timestamp)


class TestShadowTopicMapper(unittest.TestCase):
    """Test suite for the shadow topic mapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ShadowTopicMapper(topic_prefix="iotsphere.devices")

    def test_get_shadow_update_topic(self):
        """Test that get_shadow_update_topic generates the correct topic."""
        # Arrange
        device_id = "device123"

        # Act
        topic = self.mapper.get_shadow_update_topic(device_id)

        # Assert
        self.assertEqual(topic, "iotsphere.devices.device123.shadow.update")

    def test_get_shadow_created_topic(self):
        """Test that get_shadow_created_topic generates the correct topic."""
        # Arrange
        device_id = "device123"

        # Act
        topic = self.mapper.get_shadow_created_topic(device_id)

        # Assert
        self.assertEqual(topic, "iotsphere.devices.device123.shadow.created")

    def test_get_shadow_deleted_topic(self):
        """Test that get_shadow_deleted_topic generates the correct topic."""
        # Arrange
        device_id = "device123"

        # Act
        topic = self.mapper.get_shadow_deleted_topic(device_id)

        # Assert
        self.assertEqual(topic, "iotsphere.devices.device123.shadow.deleted")

    def test_get_shadow_field_topic(self):
        """Test that get_shadow_field_topic generates the correct topic."""
        # Arrange
        device_id = "device123"
        field_path = "reported.temperature"

        # Act
        topic = self.mapper.get_shadow_field_topic(device_id, field_path)

        # Assert
        self.assertEqual(
            topic, "iotsphere.devices.device123.shadow.reported.temperature"
        )

        # Test with complex field path
        field_path = "reported.sensors.temperature.value"
        topic = self.mapper.get_shadow_field_topic(device_id, field_path)
        self.assertEqual(
            topic,
            "iotsphere.devices.device123.shadow.reported.sensors.temperature.value",
        )

    def test_get_shadow_desired_topic(self):
        """Test that get_shadow_desired_topic generates the correct topic."""
        # Arrange
        device_id = "device123"

        # Act
        topic = self.mapper.get_shadow_desired_topic(device_id)

        # Assert
        self.assertEqual(topic, "iotsphere.devices.device123.shadow.desired")

    def test_get_shadow_reported_topic(self):
        """Test that get_shadow_reported_topic generates the correct topic."""
        # Arrange
        device_id = "device123"

        # Act
        topic = self.mapper.get_shadow_reported_topic(device_id)

        # Assert
        self.assertEqual(topic, "iotsphere.devices.device123.shadow.reported")

    def test_parse_device_id_from_topic(self):
        """Test that parse_device_id_from_topic extracts the device ID correctly."""
        # Test cases
        test_cases = [
            {
                "topic": "iotsphere.devices.device123.shadow.update",
                "expected": "device123",
            },
            {
                "topic": "iotsphere.devices.device456.shadow.reported.temperature",
                "expected": "device456",
            },
            {"topic": "iotsphere.other.topic", "expected": None},
        ]

        # Test each case
        for case in test_cases:
            topic = case["topic"]
            expected = case["expected"]

            result = self.mapper.parse_device_id_from_topic(topic)
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
