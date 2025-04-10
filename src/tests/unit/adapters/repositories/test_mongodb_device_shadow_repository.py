"""
Unit tests for MongoDB Device Shadow Repository.

This module contains tests for the MongoDB implementation of the Device Shadow Repository,
following the TDD approach (red-green-refactor) and Clean Architecture principles.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.device_shadow import DeviceShadow


# This class will be implemented later
class MongoDBDeviceShadowRepository:
    pass


@pytest.mark.unit
class TestMongoDBDeviceShadowRepository:
    """Unit tests for MongoDB device shadow repository implementation."""

    @pytest.fixture
    def mock_mongo_client(self):
        """Create a mock MongoDB client."""
        with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock:
            mock_client = AsyncMock()
            mock.return_value = mock_client

            # Mock the database and collection access
            mock_db = AsyncMock()
            mock_collection = AsyncMock()

            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection

            # Return the collection mock for easy access in tests
            yield mock_collection

    @pytest.fixture
    def sample_device_shadow(self):
        """Create a sample device shadow entity for testing."""
        return DeviceShadow(
            device_id="test-device-001",
            reported={"temperature": 50.0, "humidity": 45.0, "status": "ONLINE"},
            desired={"temperature": 55.0, "mode": "ECO"},
            version=1,
            timestamp=datetime.now().isoformat(),
        )

    @pytest.fixture
    def repository(self, mock_mongo_client):
        """Create a repository instance with mocked MongoDB client."""
        with patch(
            "src.adapters.repositories.mongodb_device_shadow_repository.MongoDBDeviceShadowRepository.get_collection",
            return_value=mock_mongo_client,
        ):
            from src.adapters.repositories.mongodb_device_shadow_repository import (
                MongoDBDeviceShadowRepository,
            )

            return MongoDBDeviceShadowRepository(
                connection_string="mongodb://localhost:27017"
            )

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_get_device_shadow(
        self, repository, mock_mongo_client, sample_device_shadow
    ):
        """Test retrieving a device shadow from MongoDB.

        This test verifies that the repository can correctly retrieve and deserialize
        a device shadow entity from MongoDB given its device ID.
        """
        # Arrange
        mock_result = {
            "_id": sample_device_shadow.device_id,
            "reported": sample_device_shadow.reported,
            "desired": sample_device_shadow.desired,
            "version": sample_device_shadow.version,
            "timestamp": sample_device_shadow.timestamp,
        }
        mock_mongo_client.find_one.return_value = mock_result

        # Act
        result = await repository.get_device_shadow(sample_device_shadow.device_id)

        # Assert
        assert result is not None
        assert result.device_id == sample_device_shadow.device_id
        assert result.reported == sample_device_shadow.reported
        assert result.desired == sample_device_shadow.desired
        assert result.version == sample_device_shadow.version
        mock_mongo_client.find_one.assert_called_once_with(
            {"_id": sample_device_shadow.device_id}
        )

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_get_non_existent_device_shadow(self, repository, mock_mongo_client):
        """Test retrieving a non-existent device shadow from MongoDB.

        This test verifies that the repository returns None when attempting to retrieve
        a device shadow that does not exist in the database.
        """
        # Arrange
        mock_mongo_client.find_one.return_value = None

        # Act
        result = await repository.get_device_shadow("non-existent-id")

        # Assert
        assert result is None
        mock_mongo_client.find_one.assert_called_once_with({"_id": "non-existent-id"})

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_update_desired_state(
        self, repository, mock_mongo_client, sample_device_shadow
    ):
        """Test updating the desired state of a device shadow in MongoDB.

        This test ensures the repository correctly updates the desired state of an existing
        device shadow entity in MongoDB, increments the version, and returns the updated entity.
        """
        # Arrange
        # Current shadow in the database
        current_shadow = {
            "_id": sample_device_shadow.device_id,
            "reported": sample_device_shadow.reported,
            "desired": sample_device_shadow.desired,
            "version": sample_device_shadow.version,
            "timestamp": sample_device_shadow.timestamp,
        }

        # Updated shadow to be returned after update
        updated_shadow = {
            "_id": sample_device_shadow.device_id,
            "reported": sample_device_shadow.reported,
            "desired": {"temperature": 60.0, "mode": "ECO"},  # Updated value
            "version": sample_device_shadow.version + 1,  # Incremented version
            "timestamp": datetime.now().isoformat(),  # New timestamp
        }

        # Mock the find_one_and_update to return the updated document
        mock_mongo_client.find_one.return_value = current_shadow
        mock_mongo_client.find_one_and_update.return_value = updated_shadow

        # New desired state to update
        new_desired_state = {"temperature": 60.0}

        # Act
        result = await repository.update_desired_state(
            sample_device_shadow.device_id, new_desired_state
        )

        # Assert
        assert result is not None
        assert result.device_id == sample_device_shadow.device_id
        assert result.desired["temperature"] == 60.0
        assert result.version == sample_device_shadow.version + 1
        mock_mongo_client.find_one.assert_called_once_with(
            {"_id": sample_device_shadow.device_id}
        )
        mock_mongo_client.find_one_and_update.assert_called_once()

        # Verify the filter and update document structure
        filter_doc = mock_mongo_client.find_one_and_update.call_args[0][0]
        update_doc = mock_mongo_client.find_one_and_update.call_args[0][1]
        assert filter_doc == {"_id": sample_device_shadow.device_id}
        assert "$set" in update_doc
        assert "desired.temperature" in update_doc["$set"]
        assert update_doc["$set"]["desired.temperature"] == 60.0
        assert update_doc["$inc"]["version"] == 1

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_update_reported_state(
        self, repository, mock_mongo_client, sample_device_shadow
    ):
        """Test updating the reported state of a device shadow in MongoDB.

        This test ensures the repository correctly updates the reported state of an existing
        device shadow entity in MongoDB, increments the version, and returns the updated entity.
        """
        # Arrange
        # Current shadow in the database
        current_shadow = {
            "_id": sample_device_shadow.device_id,
            "reported": sample_device_shadow.reported,
            "desired": sample_device_shadow.desired,
            "version": sample_device_shadow.version,
            "timestamp": sample_device_shadow.timestamp,
        }

        # Updated shadow to be returned after update
        updated_shadow = {
            "_id": sample_device_shadow.device_id,
            "reported": {
                "temperature": 52.0,  # Updated value
                "humidity": 45.0,
                "status": "ONLINE",
            },
            "desired": sample_device_shadow.desired,
            "version": sample_device_shadow.version + 1,  # Incremented version
            "timestamp": datetime.now().isoformat(),  # New timestamp
        }

        # Mock the find_one_and_update to return the updated document
        mock_mongo_client.find_one.return_value = current_shadow
        mock_mongo_client.find_one_and_update.return_value = updated_shadow

        # New reported state to update
        new_reported_state = {"temperature": 52.0}

        # Act
        result = await repository.update_reported_state(
            sample_device_shadow.device_id, new_reported_state
        )

        # Assert
        assert result is not None
        assert result.device_id == sample_device_shadow.device_id
        assert result.reported["temperature"] == 52.0
        assert result.version == sample_device_shadow.version + 1
        mock_mongo_client.find_one.assert_called_once_with(
            {"_id": sample_device_shadow.device_id}
        )
        mock_mongo_client.find_one_and_update.assert_called_once()

        # Verify the filter and update document structure
        filter_doc = mock_mongo_client.find_one_and_update.call_args[0][0]
        update_doc = mock_mongo_client.find_one_and_update.call_args[0][1]
        assert filter_doc == {"_id": sample_device_shadow.device_id}
        assert "$set" in update_doc
        assert "reported.temperature" in update_doc["$set"]
        assert update_doc["$set"]["reported.temperature"] == 52.0
        assert update_doc["$inc"]["version"] == 1

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_update_non_existent_device_shadow(
        self, repository, mock_mongo_client
    ):
        """Test updating a non-existent device shadow in MongoDB.

        This test verifies that the repository correctly handles the case where
        an attempt is made to update a device shadow that does not exist.
        """
        # Arrange
        device_id = "non-existent-id"
        mock_mongo_client.find_one.return_value = None

        # Act and Assert
        with pytest.raises(
            ValueError, match=f"No shadow document exists for device {device_id}"
        ):
            await repository.update_desired_state(device_id, {"temperature": 60.0})

        mock_mongo_client.find_one.assert_called_once_with({"_id": device_id})
        mock_mongo_client.find_one_and_update.assert_not_called()

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_get_shadow_delta(
        self, repository, mock_mongo_client, sample_device_shadow
    ):
        """Test retrieving the delta between desired and reported states.

        This test ensures the repository correctly calculates and returns the delta
        between desired and reported states of a device shadow.
        """
        # Arrange
        # Sample shadow with differences between desired and reported
        shadow_with_delta = {
            "_id": sample_device_shadow.device_id,
            "reported": {
                "temperature": 50.0,
                "humidity": 45.0,
                "status": "ONLINE",
                "fan_speed": "low",
            },
            "desired": {
                "temperature": 55.0,
                "mode": "ECO",
                "fan_speed": "high",  # Different from reported
            },
            "version": sample_device_shadow.version,
            "timestamp": sample_device_shadow.timestamp,
        }

        mock_mongo_client.find_one.return_value = shadow_with_delta

        # Expected delta - only the differences
        expected_delta = {
            "temperature": 55.0,  # Different in desired
            "mode": "ECO",  # Only in desired
            "fan_speed": "high",  # Different values
        }

        # Act
        result = await repository.get_shadow_delta(sample_device_shadow.device_id)

        # Assert
        assert result is not None
        assert "delta" in result
        assert result["delta"] == expected_delta
        mock_mongo_client.find_one.assert_called_once_with(
            {"_id": sample_device_shadow.device_id}
        )

    @pytest.mark.red
    @pytest.mark.asyncio
    async def test_create_device_shadow(
        self, repository, mock_mongo_client, sample_device_shadow
    ):
        """Test creating a new device shadow in MongoDB.

        This test ensures the repository correctly serializes and creates a new
        device shadow entity in MongoDB and returns the created entity.
        """
        # Arrange
        # The shadow document to be inserted
        shadow_dict = {
            "_id": sample_device_shadow.device_id,
            "reported": sample_device_shadow.reported,
            "desired": sample_device_shadow.desired,
            "version": sample_device_shadow.version,
            "timestamp": sample_device_shadow.timestamp,
        }

        # Mock the insert_one operation
        mock_mongo_client.insert_one.return_value = AsyncMock(
            inserted_id=sample_device_shadow.device_id
        )
        mock_mongo_client.find_one.return_value = shadow_dict

        # Act
        result = await repository.create_device_shadow(sample_device_shadow)

        # Assert
        assert result is not None
        assert result.device_id == sample_device_shadow.device_id
        assert result.reported == sample_device_shadow.reported
        assert result.desired == sample_device_shadow.desired
        mock_mongo_client.insert_one.assert_called_once()

        # Verify the document structure matches our entity
        doc = mock_mongo_client.insert_one.call_args[0][0]
        assert doc["_id"] == sample_device_shadow.device_id
        assert doc["reported"] == sample_device_shadow.reported
        assert doc["desired"] == sample_device_shadow.desired
        assert doc["version"] == sample_device_shadow.version
