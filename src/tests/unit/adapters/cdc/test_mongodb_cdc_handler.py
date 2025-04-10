"""
Unit tests for MongoDB CDC Event Handler.

This module contains tests for the MongoDB CDC (Change Data Capture) Event Handler,
following the TDD approach (red-green-refactor) and Clean Architecture principles.
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Domain Events
class DomainEvent:
    """Base class for domain events."""

    def __init__(self, event_type, timestamp=None):
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        """Convert event to dictionary."""
        return {"event_type": self.event_type, "timestamp": self.timestamp}


class WaterHeaterDocumentChanged(DomainEvent):
    """Event raised when a water heater document is changed in MongoDB."""

    def __init__(self, heater_id, operation_type, full_document, timestamp=None):
        super().__init__("WaterHeaterDocumentChanged", timestamp)
        self.heater_id = heater_id
        self.operation_type = operation_type  # insert, update, delete
        self.full_document = full_document

    def to_dict(self):
        """Convert event to dictionary."""
        event_dict = super().to_dict()
        event_dict.update(
            {
                "heater_id": self.heater_id,
                "operation_type": self.operation_type,
                "full_document": self.full_document,
            }
        )
        return event_dict


class DeviceShadowDocumentChanged(DomainEvent):
    """Event raised when a device shadow document is changed in MongoDB."""

    def __init__(self, device_id, operation_type, full_document, timestamp=None):
        super().__init__("DeviceShadowDocumentChanged", timestamp)
        self.device_id = device_id
        self.operation_type = operation_type  # insert, update, delete
        self.full_document = full_document

    def to_dict(self):
        """Convert event to dictionary."""
        event_dict = super().to_dict()
        event_dict.update(
            {
                "device_id": self.device_id,
                "operation_type": self.operation_type,
                "full_document": self.full_document,
            }
        )
        return event_dict


@pytest.mark.unit
class TestMongoDBCDCHandler:
    """Unit tests for MongoDB CDC event handler."""

    @pytest.fixture
    def mock_mongo_client(self):
        """Create a mock MongoDB client."""
        mock_client = AsyncMock()

        # Mock the database and collection access
        mock_db = AsyncMock()
        mock_collection = AsyncMock()

        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Return the client mock
        return mock_client

    @pytest.fixture
    def mock_change_stream(self):
        """Create a mock change stream."""
        mock = AsyncMock()
        mock.__aiter__.return_value = mock
        return mock

    @pytest.fixture
    def mock_broker_adapter(self):
        """Create a mock message broker adapter."""
        return MagicMock()

    @pytest.fixture
    def cdc_handler(self, mock_mongo_client, mock_broker_adapter):
        """Create a CDC handler instance with mocked dependencies."""
        with patch(
            "src.adapters.cdc.mongodb_cdc_handler.MongoDBCDCHandler._init_mongo_client",
            return_value=mock_mongo_client,
        ):
            from src.adapters.cdc.mongodb_cdc_handler import MongoDBCDCHandler

            handler = MongoDBCDCHandler(
                mongo_connection_string="mongodb://localhost:27017",
                broker_adapter=mock_broker_adapter,
            )
            return handler

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_init_mongo_client(self):
        """Test initialization of MongoDB client.

        This test verifies that the CDC handler correctly initializes a MongoDB client
        with the provided connection string.
        """
        # Arrange
        mongo_connection_string = "mongodb://localhost:27017"

        # Create a mock for the AsyncIOMotorClient constructor
        with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client_constructor:
            mock_client = AsyncMock()
            mock_client_constructor.return_value = mock_client

            # Act
            from src.adapters.cdc.mongodb_cdc_handler import MongoDBCDCHandler

            handler = MongoDBCDCHandler(
                mongo_connection_string=mongo_connection_string,
                broker_adapter=MagicMock(),
            )

            # Assert
            mock_client_constructor.assert_called_once_with(mongo_connection_string)
            assert handler.mongo_client == mock_client

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_start_change_stream(
        self, cdc_handler, mock_mongo_client, mock_change_stream
    ):
        """Test starting a change stream for MongoDB.

        This test verifies that the CDC handler correctly starts a change stream
        for the specified collection.
        """
        # Arrange
        collection_name = "water_heaters"
        mock_collection = AsyncMock()
        mock_mongo_client.__getitem__.return_value.__getitem__.return_value = (
            mock_collection
        )
        mock_collection.watch.return_value = mock_change_stream

        # Act
        await cdc_handler.start_watching(collection_name)

        # Assert
        mock_collection.watch.assert_called_once()
        assert cdc_handler.change_streams[collection_name] == mock_change_stream

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_process_insert_event(
        self, cdc_handler, mock_change_stream, mock_broker_adapter
    ):
        """Test processing an insert event from change stream.

        This test ensures the CDC handler correctly processes an insert event from the
        change stream and publishes a domain event to the message broker.
        """
        # Arrange
        collection_name = "water_heaters"

        # Mock the change stream to return an insert event
        insert_event = {
            "operationType": "insert",
            "ns": {"db": "iot_sphere", "coll": collection_name},
            "documentKey": {"_id": "test-heater-001"},
            "fullDocument": {
                "_id": "test-heater-001",
                "name": "Test Heater",
                "manufacturer": "TestCo",
                "model": "TestModel100",
                "current_temperature": {"value": 50.0, "unit": "C"},
                "target_temperature": {"value": 55.0, "unit": "C"},
            },
        }

        mock_change_stream.__anext__.return_value = insert_event

        # Mock the change stream in the handler
        cdc_handler.change_streams[collection_name] = mock_change_stream

        # Act
        await cdc_handler._process_next_change(collection_name)

        # Assert
        mock_broker_adapter.publish_event.assert_called_once()
        # Verify the topic and event
        args, kwargs = mock_broker_adapter.publish_event.call_args
        assert args[0] == f"{collection_name}_events"  # topic name
        assert isinstance(args[1], WaterHeaterDocumentChanged)
        assert args[1].operation_type == "insert"
        assert args[1].heater_id == "test-heater-001"
        assert args[1].full_document == insert_event["fullDocument"]

        # Verify key used for the message
        assert kwargs["key"] == "test-heater-001"

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_process_update_event(
        self, cdc_handler, mock_change_stream, mock_broker_adapter
    ):
        """Test processing an update event from change stream.

        This test ensures the CDC handler correctly processes an update event from the
        change stream and publishes a domain event to the message broker.
        """
        # Arrange
        collection_name = "device_shadows"

        # Mock the change stream to return an update event
        update_event = {
            "operationType": "update",
            "ns": {"db": "iot_sphere", "coll": collection_name},
            "documentKey": {"_id": "test-device-001"},
            "updateDescription": {
                "updatedFields": {"desired.temperature": 60.0, "version": 2},
                "removedFields": [],
            },
            "fullDocument": {
                "_id": "test-device-001",
                "reported": {"temperature": 50.0, "humidity": 45.0},
                "desired": {"temperature": 60.0},  # Updated value
                "version": 2,
                "timestamp": datetime.now().isoformat(),
            },
        }

        mock_change_stream.__anext__.return_value = update_event

        # Mock the change stream in the handler
        cdc_handler.change_streams[collection_name] = mock_change_stream

        # Act
        await cdc_handler._process_next_change(collection_name)

        # Assert
        mock_broker_adapter.publish_event.assert_called_once()
        # Verify the topic and event
        args, kwargs = mock_broker_adapter.publish_event.call_args
        assert args[0] == f"{collection_name}_events"  # topic name
        assert isinstance(args[1], DeviceShadowDocumentChanged)
        assert args[1].operation_type == "update"
        assert args[1].device_id == "test-device-001"
        assert args[1].full_document == update_event["fullDocument"]

        # Verify key used for the message
        assert kwargs["key"] == "test-device-001"

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_process_delete_event(
        self, cdc_handler, mock_change_stream, mock_broker_adapter
    ):
        """Test processing a delete event from change stream.

        This test ensures the CDC handler correctly processes a delete event from the
        change stream and publishes a domain event to the message broker.
        """
        # Arrange
        collection_name = "water_heaters"

        # Mock the change stream to return a delete event
        delete_event = {
            "operationType": "delete",
            "ns": {"db": "iot_sphere", "coll": collection_name},
            "documentKey": {"_id": "test-heater-001"}
            # Note: fullDocument is not available for delete operations
        }

        mock_change_stream.__anext__.return_value = delete_event

        # Mock the change stream in the handler
        cdc_handler.change_streams[collection_name] = mock_change_stream

        # Act
        await cdc_handler._process_next_change(collection_name)

        # Assert
        mock_broker_adapter.publish_event.assert_called_once()
        # Verify the topic and event
        args, kwargs = mock_broker_adapter.publish_event.call_args
        assert args[0] == f"{collection_name}_events"  # topic name
        assert isinstance(args[1], WaterHeaterDocumentChanged)
        assert args[1].operation_type == "delete"
        assert args[1].heater_id == "test-heater-001"
        assert args[1].full_document is None

        # Verify key used for the message
        assert kwargs["key"] == "test-heater-001"

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_watch_multiple_collections(self, cdc_handler):
        """Test watching multiple collections simultaneously.

        This test verifies that the CDC handler can watch multiple MongoDB
        collections simultaneously and handle their change events.
        """
        # Arrange
        collections = ["water_heaters", "device_shadows"]

        # Mock the start_watching method
        with patch.object(cdc_handler, "start_watching") as mock_start_watching:
            # Make start_watching return a coroutine mock
            mock_start_watching.return_value = asyncio.Future()
            mock_start_watching.return_value.set_result(None)

            # Act
            await cdc_handler.watch_collections(collections)

            # Assert
            assert mock_start_watching.call_count == len(collections)
            # Verify each collection was watched
            for collection in collections:
                mock_start_watching.assert_any_call(collection)

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_stop_watching(self, cdc_handler, mock_change_stream):
        """Test stopping change streams.

        This test ensures that the CDC handler correctly closes change streams
        when they are no longer needed.
        """
        # Arrange
        collection_name = "water_heaters"
        cdc_handler.change_streams[collection_name] = mock_change_stream

        # Act
        await cdc_handler.stop_watching(collection_name)

        # Assert
        mock_change_stream.close.assert_called_once()
        assert collection_name not in cdc_handler.change_streams

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_handle_change_stream_error(
        self, cdc_handler, mock_change_stream, mock_broker_adapter
    ):
        """Test handling errors in the change stream.

        This test verifies that the CDC handler correctly handles errors that may occur
        while processing change stream events.
        """
        # Arrange
        collection_name = "water_heaters"

        # Mock the change stream to raise an exception
        mock_change_stream.__anext__.side_effect = Exception("Change stream error")

        # Mock the change stream in the handler
        cdc_handler.change_streams[collection_name] = mock_change_stream

        # Act & Assert
        # The handler should catch the exception and not propagate it
        await cdc_handler._process_next_change(collection_name)

        # Verify no events were published due to the error
        mock_broker_adapter.publish_event.assert_not_called()
