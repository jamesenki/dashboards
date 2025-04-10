"""
Test suite for the MongoDB Change Stream Listener following TDD principles.

This test suite defines expected behaviors for the change stream listener
before implementation, establishing a clear contract for how the component
should function. Each test is atomic, focusing on a single behavior.
"""
import asyncio
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from bson.timestamp import Timestamp

from src.services.shadow_change_stream_listener import (
    ShadowChangeEvent,
    ShadowChangeStreamListener,
)


class TestShadowChangeStreamListener(unittest.TestCase):
    """Test suite for the MongoDB Change Stream Listener implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_mongo_client = AsyncMock()
        self.mock_db = AsyncMock()
        self.mock_collection = AsyncMock()
        self.mock_change_stream = AsyncMock()

        # Configure mocks
        self.mock_mongo_client.__getitem__.return_value = self.mock_db
        self.mock_db.__getitem__.return_value = self.mock_collection
        self.mock_collection.watch.return_value = self.mock_change_stream

        # Set up the listener
        self.listener = ShadowChangeStreamListener(
            mongo_uri="mongodb://localhost:27017",
            db_name="test_db",
            collection_name="device_shadows",
        )
        self.listener.mongo_client = self.mock_mongo_client

        # Mock event handler
        self.mock_event_handler = MagicMock()
        self.listener.register_event_handler(self.mock_event_handler)

    def test_init_sets_connection_parameters(self):
        """Test that initialization properly sets connection parameters."""
        # Act
        listener = ShadowChangeStreamListener(
            mongo_uri="mongodb://testhost:27017",
            db_name="test_database",
            collection_name="test_collection",
        )

        # Assert
        self.assertEqual(listener.mongo_uri, "mongodb://testhost:27017")
        self.assertEqual(listener.db_name, "test_database")
        self.assertEqual(listener.collection_name, "test_collection")
        self.assertFalse(listener.initialized)
        self.assertFalse(listener.is_listening)

    @pytest.mark.asyncio
    async def test_connect_establishes_mongo_client(self):
        """Test that _connect creates a MongoDB client connection."""
        # Arrange
        with patch(
            "src.services.shadow_change_stream_listener.AsyncIOMotorClient"
        ) as mock_client:
            mock_client.return_value = self.mock_mongo_client
            listener = ShadowChangeStreamListener(
                mongo_uri="mongodb://testhost:27017",
                db_name="test_database",
                collection_name="test_collection",
            )

            # Act
            await listener._connect()

            # Assert
            mock_client.assert_called_once_with("mongodb://testhost:27017")
            self.assertEqual(listener.mongo_client, self.mock_mongo_client)

    @pytest.mark.asyncio
    async def test_initialize_gets_database(self):
        """Test that initialize gets the correct database."""
        # Act
        await self.listener.initialize()

        # Assert
        self.mock_mongo_client.__getitem__.assert_called_once_with("test_db")

    @pytest.mark.asyncio
    async def test_initialize_gets_collection(self):
        """Test that initialize gets the correct collection."""
        # Act
        await self.listener.initialize()

        # Assert
        self.mock_db.__getitem__.assert_called_once_with("device_shadows")

    @pytest.mark.asyncio
    async def test_initialize_creates_change_stream(self):
        """Test that initialize sets up a change stream on the shadows collection."""
        # Act
        await self.listener.initialize()

        # Assert
        self.mock_collection.watch.assert_called_once()
        self.assertEqual(self.listener.change_stream, self.mock_change_stream)

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self):
        """Test that initialize sets the initialized flag."""
        # Act
        await self.listener.initialize()

        # Assert
        self.assertTrue(self.listener.initialized)

    @pytest.mark.asyncio
    async def test_start_listening_calls_process_events(self):
        """Test that start_listening calls the event processing method."""
        # Arrange
        self.listener.initialized = True
        self.listener.change_stream = self.mock_change_stream
        self.listener._process_change_events = AsyncMock()

        # Act
        await self.listener.start_listening()

        # Assert
        self.listener._process_change_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_listening_sets_listening_flag(self):
        """Test that start_listening sets the listening flag."""
        # Arrange
        self.listener.initialized = True
        self.listener.change_stream = self.mock_change_stream
        self.listener._process_change_events = AsyncMock()

        # Act
        await self.listener.start_listening()

        # Assert
        self.assertTrue(self.listener.is_listening)

    @pytest.mark.asyncio
    async def test_start_listening_returns_error_if_not_initialized(self):
        """Test that start_listening returns an error if not initialized."""
        # Arrange
        self.listener.initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError):
            await self.listener.start_listening()

    @pytest.mark.asyncio
    async def test_stop_listening_closes_change_stream(self):
        """Test that stop_listening closes the change stream."""
        # Arrange
        self.listener.is_listening = True
        self.listener.change_stream = self.mock_change_stream

        # Act
        await self.listener.stop_listening()

        # Assert
        self.mock_change_stream.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_listening_clears_listening_flag(self):
        """Test that stop_listening clears the listening flag."""
        # Arrange
        self.listener.is_listening = True
        self.listener.change_stream = self.mock_change_stream

        # Act
        await self.listener.stop_listening()

        # Assert
        self.assertFalse(self.listener.is_listening)

    @pytest.mark.asyncio
    async def test_extract_device_id_from_insert_event(self):
        """Test extracting device ID from an insert event."""
        # Arrange
        change_event = {
            "operationType": "insert",
            "fullDocument": {
                "_id": "device123",
                # Additional fields omitted for brevity
            },
        }

        # Act
        device_id = self.listener._extract_device_id(change_event)

        # Assert
        self.assertEqual(device_id, "device123")

    @pytest.mark.asyncio
    async def test_extract_device_id_from_update_event(self):
        """Test extracting device ID from an update event."""
        # Arrange
        change_event = {"operationType": "update", "documentKey": {"_id": "device456"}}

        # Act
        device_id = self.listener._extract_device_id(change_event)

        # Assert
        self.assertEqual(device_id, "device456")

    @pytest.mark.asyncio
    async def test_extract_device_id_from_delete_event(self):
        """Test extracting device ID from a delete event."""
        # Arrange
        change_event = {"operationType": "delete", "documentKey": {"_id": "device789"}}

        # Act
        device_id = self.listener._extract_device_id(change_event)

        # Assert
        self.assertEqual(device_id, "device789")

    @pytest.mark.asyncio
    async def test_extract_timestamp_from_event_with_timestamp(self):
        """Test extracting timestamp from an event with timestamp field."""
        # Arrange
        timestamp = datetime.now().isoformat()
        change_event = {
            "operationType": "insert",
            "fullDocument": {"_id": "device123", "timestamp": timestamp},
        }

        # Act
        extracted_timestamp = self.listener._extract_timestamp(change_event)

        # Assert
        self.assertEqual(extracted_timestamp, timestamp)

    @pytest.mark.asyncio
    async def test_extract_timestamp_from_event_without_timestamp(self):
        """Test extracting timestamp from an event without timestamp field."""
        # Arrange
        change_event = {"operationType": "delete", "documentKey": {"_id": "device123"}}

        # Act
        extracted_timestamp = self.listener._extract_timestamp(change_event)

        # Assert
        self.assertIsNotNone(extracted_timestamp)  # Should generate a timestamp

    @pytest.mark.asyncio
    async def test_create_shadow_change_event_for_insert(self):
        """Test creating a shadow change event for an insert operation."""
        # Arrange
        timestamp = datetime.now().isoformat()
        mongo_event = {
            "operationType": "insert",
            "fullDocument": {
                "_id": "device123",
                "reported": {"temperature": 72},
                "desired": {"temperature": 70},
                "version": 1,
                "timestamp": timestamp,
            },
        }

        # Act
        event = self.listener._create_shadow_change_event(mongo_event)

        # Assert
        self.assertIsInstance(event, ShadowChangeEvent)
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "insert")
        self.assertEqual(event.full_document, mongo_event["fullDocument"])
        self.assertIsNone(event.changed_fields)
        self.assertEqual(event.timestamp, timestamp)

    @pytest.mark.asyncio
    async def test_create_shadow_change_event_for_update(self):
        """Test creating a shadow change event for an update operation."""
        # Arrange
        timestamp = datetime.now().isoformat()
        changed_fields = {
            "reported.temperature": 75,
            "version": 2,
            "timestamp": timestamp,
        }
        mongo_event = {
            "operationType": "update",
            "documentKey": {"_id": "device123"},
            "updateDescription": {"updatedFields": changed_fields, "removedFields": []},
            "fullDocument": {
                "_id": "device123",
                "reported": {"temperature": 75},
                "desired": {"temperature": 70},
                "version": 2,
                "timestamp": timestamp,
            },
        }

        # Act
        event = self.listener._create_shadow_change_event(mongo_event)

        # Assert
        self.assertIsInstance(event, ShadowChangeEvent)
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "update")
        self.assertEqual(event.full_document, mongo_event["fullDocument"])
        self.assertEqual(event.changed_fields, changed_fields)
        self.assertEqual(event.timestamp, timestamp)

    @pytest.mark.asyncio
    async def test_create_shadow_change_event_for_delete(self):
        """Test creating a shadow change event for a delete operation."""
        # Arrange
        timestamp = datetime.now().isoformat()
        mongo_event = {
            "operationType": "delete",
            "documentKey": {"_id": "device123"},
            "clusterTime": Timestamp(1616161616, 1),
        }
        self.listener._extract_timestamp = MagicMock(return_value=timestamp)

        # Act
        event = self.listener._create_shadow_change_event(mongo_event)

        # Assert
        self.assertIsInstance(event, ShadowChangeEvent)
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "delete")
        self.assertIsNone(event.full_document)
        self.assertIsNone(event.changed_fields)
        self.assertEqual(event.timestamp, timestamp)

    @pytest.mark.asyncio
    async def test_notify_handlers_calls_all_registered_handlers(self):
        """Test that _notify_handlers calls all registered event handlers."""
        # Arrange
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        self.listener.register_event_handler(handler1)
        self.listener.register_event_handler(handler2)

        event = ShadowChangeEvent(
            device_id="device123",
            operation_type="update",
            full_document={"temperature": 75},
            changed_fields={"temperature": 75},
            timestamp=datetime.now().isoformat(),
        )

        # Act
        await self.listener._notify_handlers(event)

        # Assert
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
        self.mock_event_handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_register_event_handler_adds_handler(self):
        """Test that register_event_handler adds a handler to the list."""
        # Arrange
        handler = AsyncMock()
        initial_count = len(self.listener.event_handlers)

        # Act
        self.listener.register_event_handler(handler)

        # Assert
        self.assertEqual(len(self.listener.event_handlers), initial_count + 1)
        self.assertIn(handler, self.listener.event_handlers)

    @pytest.mark.asyncio
    async def test_unregister_event_handler_removes_handler(self):
        """Test that unregister_event_handler removes a handler from the list."""
        # Arrange
        handler = AsyncMock()
        self.listener.register_event_handler(handler)
        initial_count = len(self.listener.event_handlers)

        # Act
        self.listener.unregister_event_handler(handler)

        # Assert
        self.assertEqual(len(self.listener.event_handlers), initial_count - 1)
        self.assertNotIn(handler, self.listener.event_handlers)

    @pytest.mark.asyncio
    async def test_handle_change_event_processes_valid_event(self):
        """Test that _handle_change_event processes a valid event."""
        # Arrange
        self.listener._extract_device_id = MagicMock(return_value="device123")
        self.listener._create_shadow_change_event = MagicMock()
        self.listener._notify_handlers = AsyncMock()

        change_event = {"operationType": "update", "documentKey": {"_id": "device123"}}

        # Act
        await self.listener._handle_change_event(change_event)

        # Assert
        self.listener._extract_device_id.assert_called_once_with(change_event)
        self.listener._create_shadow_change_event.assert_called_once_with(change_event)
        self.listener._notify_handlers.assert_called_once()


class TestShadowChangeEvent(unittest.TestCase):
    """Test suite for the ShadowChangeEvent class."""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        # Arrange
        timestamp = datetime.now().isoformat()
        full_document = {"temperature": 75}
        changed_fields = {"temperature": 75}

        # Act
        event = ShadowChangeEvent(
            device_id="device123",
            operation_type="update",
            full_document=full_document,
            changed_fields=changed_fields,
            timestamp=timestamp,
        )

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "update")
        self.assertEqual(event.full_document, full_document)
        self.assertEqual(event.changed_fields, changed_fields)
        self.assertEqual(event.timestamp, timestamp)

    def test_init_with_minimal_parameters(self):
        """Test initialization with only required parameters."""
        # Act
        event = ShadowChangeEvent(device_id="device123", operation_type="delete")

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "delete")
        self.assertIsNone(event.full_document)
        self.assertIsNone(event.changed_fields)
        self.assertIsNotNone(event.timestamp)  # Should generate a timestamp

    def test_to_dict_with_all_fields(self):
        """Test to_dict method with all fields populated."""
        # Arrange
        timestamp = datetime.now().isoformat()
        full_document = {"temperature": 75}
        changed_fields = {"temperature": 75}

        event = ShadowChangeEvent(
            device_id="device123",
            operation_type="update",
            full_document=full_document,
            changed_fields=changed_fields,
            timestamp=timestamp,
        )

        # Act
        result = event.to_dict()

        # Assert
        self.assertEqual(result["device_id"], "device123")
        self.assertEqual(result["operation_type"], "update")
        self.assertEqual(result["full_document"], full_document)
        self.assertEqual(result["changed_fields"], changed_fields)
        self.assertEqual(result["timestamp"], timestamp)

    def test_to_dict_with_minimal_fields(self):
        """Test to_dict method with minimal fields."""
        # Arrange
        event = ShadowChangeEvent(device_id="device123", operation_type="delete")

        # Act
        result = event.to_dict()

        # Assert
        self.assertEqual(result["device_id"], "device123")
        self.assertEqual(result["operation_type"], "delete")
        self.assertIsNone(result["full_document"])
        self.assertIsNone(result["changed_fields"])
        self.assertIsNotNone(result["timestamp"])

    def test_from_dict_with_all_fields(self):
        """Test from_dict class method with all fields."""
        # Arrange
        timestamp = datetime.now().isoformat()
        full_document = {"temperature": 75}
        changed_fields = {"temperature": 75}

        data = {
            "device_id": "device123",
            "operation_type": "update",
            "full_document": full_document,
            "changed_fields": changed_fields,
            "timestamp": timestamp,
        }

        # Act
        event = ShadowChangeEvent.from_dict(data)

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "update")
        self.assertEqual(event.full_document, full_document)
        self.assertEqual(event.changed_fields, changed_fields)
        self.assertEqual(event.timestamp, timestamp)

    def test_from_dict_with_minimal_fields(self):
        """Test from_dict class method with minimal fields."""
        # Arrange
        data = {"device_id": "device123", "operation_type": "delete"}

        # Act
        event = ShadowChangeEvent.from_dict(data)

        # Assert
        self.assertEqual(event.device_id, "device123")
        self.assertEqual(event.operation_type, "delete")
        self.assertIsNone(event.full_document)
        self.assertIsNone(event.changed_fields)
        self.assertIsNotNone(event.timestamp)


if __name__ == "__main__":
    unittest.main()
