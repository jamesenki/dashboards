"""
Integration test for Device Shadow Repository to External System integration.
Tests the boundary between repository implementations and external systems.

This file demonstrates proper TDD phases with explicit tagging and follows
Clean Architecture principles by testing the adapter implementation.
"""
import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.database.mongodb_client import get_mongodb_client
from src.adapters.repositories.device_shadow_repository import (
    DeviceShadowRepositoryImpl,
)
from src.domain.entities.device_shadow import DeviceShadow
from src.domain.value_objects.shadow_state import ShadowState


@pytest.fixture
def mock_mongodb_client():
    """Create a mock MongoDB client for testing.

    This isolates the test from the actual MongoDB connection while
    still testing the repository implementation logic.
    """
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    # Set up the mock chain
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    # Sample shadow document
    sample_shadow = {
        "device_id": "test-device-001",
        "reported": {
            "temperature": 120,
            "status": "ONLINE",
            "firmware_version": "v1.2.3",
        },
        "desired": {"target_temperature": 120},
        "version": 1,
        "timestamp": "2025-04-09T10:30:00Z",
    }

    # Set up mock responses
    mock_collection.find_one.return_value = sample_shadow
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    mock_collection.insert_one.return_value = MagicMock(inserted_id="new_id")

    return mock_client


@pytest.fixture
def shadow_repository(mock_mongodb_client):
    """Create a device shadow repository with the mock MongoDB client."""
    with patch(
        "src.adapters.repositories.device_shadow_repository.get_mongodb_client",
        return_value=mock_mongodb_client,
    ):
        repo = DeviceShadowRepositoryImpl()
        return repo


class TestDeviceShadowRepositoryToMongoDB:
    """Integration tests for Device Shadow Repository to MongoDB integration.

    These tests validate that the repository implementation correctly interacts
    with the external MongoDB database according to Clean Architecture principles.
    """

    @pytest.mark.red  # TDD Red phase
    async def test_get_device_shadow(self, shadow_repository, mock_mongodb_client):
        """Test retrieving a device shadow from the database.

        RED phase: This test defines the expected behavior between repository and MongoDB.

        This tests the boundary between:
        - Repository Implementation: The MongoDB-specific adapter
        - External System: MongoDB database interaction
        """
        # Setup
        device_id = "test-device-001"
        mock_collection = mock_mongodb_client["iot_sphere"]["device_shadows"]

        # Execute
        shadow = await shadow_repository.get_device_shadow(device_id)

        # Verify repository returned correct domain entity
        assert isinstance(shadow, DeviceShadow)
        assert shadow.device_id == device_id
        assert shadow.reported.temperature == 120
        assert shadow.desired.target_temperature == 120

        # Verify correct MongoDB query was made
        mock_collection.find_one.assert_called_once_with({"device_id": device_id})

    @pytest.mark.red  # TDD Red phase
    async def test_get_device_shadow_not_found(
        self, shadow_repository, mock_mongodb_client
    ):
        """Test handling of non-existent device shadow lookups.

        RED phase: This test defines expected error handling at the database boundary.

        This tests the boundary between:
        - Repository Implementation: Error handling logic
        - External System: MongoDB not found response
        """
        # Setup
        device_id = "non-existent-device"
        mock_collection = mock_mongodb_client["iot_sphere"]["device_shadows"]
        mock_collection.find_one.return_value = (
            None  # MongoDB returns None for not found
        )

        # Execute and verify
        with pytest.raises(
            ValueError, match=f"Device shadow not found for device {device_id}"
        ):
            await shadow_repository.get_device_shadow(device_id)

        # Verify correct MongoDB query was made
        mock_collection.find_one.assert_called_once_with({"device_id": device_id})

    @pytest.mark.red  # TDD Red phase
    async def test_update_desired_state(self, shadow_repository, mock_mongodb_client):
        """Test updating the desired state in the database.

        RED phase: This test defines the expected update behavior.

        This tests the boundary between:
        - Repository Implementation: Update logic and document mapping
        - External System: MongoDB update operation
        """
        # Setup
        device_id = "test-device-001"
        update_data = {"target_temperature": 125}
        mock_collection = mock_mongodb_client["iot_sphere"]["device_shadows"]

        # Setup the find_one to return updated data after update_one
        updated_shadow = {
            "device_id": device_id,
            "reported": {
                "temperature": 120,
                "status": "ONLINE",
                "firmware_version": "v1.2.3",
            },
            "desired": {"target_temperature": 125},  # Updated value
            "version": 2,  # Incremented version
            "timestamp": "2025-04-09T10:35:00Z",  # New timestamp
        }
        # First call returns original, second call (after update) returns updated
        mock_collection.find_one.side_effect = [
            {  # Original shadow
                "device_id": device_id,
                "reported": {
                    "temperature": 120,
                    "status": "ONLINE",
                    "firmware_version": "v1.2.3",
                },
                "desired": {"target_temperature": 120},
                "version": 1,
                "timestamp": "2025-04-09T10:30:00Z",
            },
            updated_shadow,  # Updated shadow
        ]

        # Execute
        updated = await shadow_repository.update_desired_state(device_id, update_data)

        # Verify repository returned correct domain entity with updates
        assert isinstance(updated, DeviceShadow)
        assert updated.device_id == device_id
        assert updated.desired.target_temperature == 125
        assert updated.version == 2

        # Verify correct MongoDB operations were made
        assert mock_collection.find_one.call_count == 2
        mock_collection.update_one.assert_called_once()
        # Verify the update had the desired state changes
        args, kwargs = mock_collection.update_one.call_args
        assert args[0] == {"device_id": device_id}  # Filter
        assert "desired.target_temperature" in args[1]["$set"]
        assert args[1]["$set"]["desired.target_temperature"] == 125
        assert "$inc" in args[1]
        assert args[1]["$inc"]["version"] == 1  # Version increment

    @pytest.mark.red  # TDD Red phase
    async def test_create_device_shadow(self, shadow_repository, mock_mongodb_client):
        """Test creating a new device shadow in the database.

        RED phase: This test defines the expected creation behavior.

        This tests the boundary between:
        - Repository Implementation: Document creation logic
        - External System: MongoDB insert operation
        """
        # Setup
        device_id = "new-device-001"
        mock_collection = mock_mongodb_client["iot_sphere"]["device_shadows"]
        mock_collection.find_one.return_value = None  # Device doesn't exist yet

        # Initial shadow data
        new_shadow = DeviceShadow(
            device_id=device_id,
            reported=ShadowState(temperature=0, status="OFFLINE"),
            desired=ShadowState(target_temperature=120),
            version=1,
            timestamp=datetime.now().isoformat(),
        )

        # Execute
        created = await shadow_repository.create_device_shadow(new_shadow)

        # Verify repository returned correct domain entity
        assert isinstance(created, DeviceShadow)
        assert created.device_id == device_id

        # Verify correct MongoDB operations were made
        mock_collection.find_one.assert_called_once_with({"device_id": device_id})
        mock_collection.insert_one.assert_called_once()
        # Verify the inserted document
        args, kwargs = mock_collection.insert_one.call_args
        assert args[0]["device_id"] == device_id
        assert "reported" in args[0]
        assert "desired" in args[0]
        assert args[0]["version"] == 1

    @pytest.mark.red  # TDD Red phase
    async def test_publish_shadow_update(self, shadow_repository, mock_mongodb_client):
        """Test publishing shadow updates to message broker.

        RED phase: This test defines the expected event publishing behavior.

        This tests the boundary between:
        - Repository Implementation: Event publishing logic
        - External System: Message broker interaction
        """
        # Setup
        device_id = "test-device-001"
        update_data = {"temperature": 122}

        # Mock the message broker client
        mock_broker = MagicMock()
        with patch(
            "src.adapters.repositories.device_shadow_repository.get_message_broker",
            return_value=mock_broker,
        ):
            # Execute
            await shadow_repository.publish_shadow_update(device_id, update_data)

            # Verify correct message broker interaction
            mock_broker.publish.assert_called_once()
            topic, message = mock_broker.publish.call_args[0]
            assert topic == f"device/{device_id}/shadow/update"
            assert isinstance(message, str)

            # Verify message content
            message_data = json.loads(message)
            assert message_data["device_id"] == device_id
            assert "temperature" in message_data
            assert message_data["temperature"] == 122
