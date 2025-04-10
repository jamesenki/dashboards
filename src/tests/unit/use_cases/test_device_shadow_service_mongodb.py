"""
Unit tests for Device Shadow Service with MongoDB Repository.

This module contains tests for the Device Shadow Service that uses a MongoDB repository,
following the TDD approach (red-green-refactor) and Clean Architecture principles.
"""
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.device_shadow import DeviceShadow


@pytest.mark.unit
class TestDeviceShadowServiceWithMongoDB:
    """Unit tests for Device Shadow Service with MongoDB repository."""

    @pytest.fixture
    def mock_mongodb_repository(self):
        """Create a mock MongoDB device shadow repository."""
        mock_repo = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_message_broker(self):
        """Create a mock message broker adapter."""
        return MagicMock()

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
    def device_shadow_service(self, mock_mongodb_repository, mock_message_broker):
        """Create a device shadow service instance with mocked dependencies."""
        from src.use_cases.device_shadow_service import DeviceShadowService

        return DeviceShadowService(
            repository=mock_mongodb_repository, message_broker=mock_message_broker
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_device_shadow(
        self, device_shadow_service, mock_mongodb_repository, sample_device_shadow
    ):
        """Test retrieving a device shadow from MongoDB.

        This test verifies that the service correctly delegates to the MongoDB repository
        and returns the device shadow entity.
        """
        # Arrange
        mock_mongodb_repository.get_device_shadow.return_value = sample_device_shadow

        # Act
        result = await device_shadow_service.get_device_shadow(
            sample_device_shadow.device_id
        )

        # Assert
        assert result == sample_device_shadow
        mock_mongodb_repository.get_device_shadow.assert_called_once_with(
            sample_device_shadow.device_id
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_device_shadow_not_found(
        self, device_shadow_service, mock_mongodb_repository
    ):
        """Test retrieving a non-existent device shadow.

        This test verifies that the service correctly handles the case where the MongoDB
        repository returns None for a non-existent device shadow.
        """
        # Arrange
        mock_mongodb_repository.get_device_shadow.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="No shadow document exists for device non-existent-id"
        ):
            await device_shadow_service.get_device_shadow("non-existent-id")

        mock_mongodb_repository.get_device_shadow.assert_called_once_with(
            "non-existent-id"
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_update_desired_state(
        self,
        device_shadow_service,
        mock_mongodb_repository,
        mock_message_broker,
        sample_device_shadow,
    ):
        """Test updating the desired state of a device shadow.

        This test verifies that the service correctly delegates to the MongoDB repository
        to update the desired state of a device shadow and publishes an event to the message broker.
        """
        # Arrange
        # Create an updated shadow with the new desired state
        updated_shadow = DeviceShadow(
            device_id=sample_device_shadow.device_id,
            reported=sample_device_shadow.reported,
            desired={"temperature": 60.0, "mode": "ECO"},  # Updated value
            version=sample_device_shadow.version + 1,
            timestamp=datetime.now().isoformat(),
        )

        mock_mongodb_repository.update_desired_state.return_value = updated_shadow

        # New desired state to update
        new_desired_state = {"temperature": 60.0}

        # Act
        result = await device_shadow_service.update_desired_state(
            sample_device_shadow.device_id, new_desired_state
        )

        # Assert
        assert result == updated_shadow
        assert result.desired["temperature"] == 60.0
        mock_mongodb_repository.update_desired_state.assert_called_once_with(
            sample_device_shadow.device_id, new_desired_state
        )

        # Verify event was published to message broker
        mock_message_broker.publish_event.assert_called_once()
        # Verify the topic and event content
        args, kwargs = mock_message_broker.publish_event.call_args
        assert args[0] == "device-shadow-events"  # topic
        assert "DeviceShadowDesiredStateUpdated" in str(args[1])  # event type
        assert kwargs["key"] == sample_device_shadow.device_id

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_update_reported_state(
        self,
        device_shadow_service,
        mock_mongodb_repository,
        mock_message_broker,
        sample_device_shadow,
    ):
        """Test updating the reported state of a device shadow.

        This test verifies that the service correctly delegates to the MongoDB repository
        to update the reported state of a device shadow and publishes an event to the message broker.
        """
        # Arrange
        # Create an updated shadow with the new reported state
        updated_shadow = DeviceShadow(
            device_id=sample_device_shadow.device_id,
            reported={
                "temperature": 52.0,  # Updated value
                "humidity": 45.0,
                "status": "ONLINE",
            },
            desired=sample_device_shadow.desired,
            version=sample_device_shadow.version + 1,
            timestamp=datetime.now().isoformat(),
        )

        mock_mongodb_repository.update_reported_state.return_value = updated_shadow

        # New reported state to update
        new_reported_state = {"temperature": 52.0}

        # Act
        result = await device_shadow_service.update_reported_state(
            sample_device_shadow.device_id, new_reported_state
        )

        # Assert
        assert result == updated_shadow
        assert result.reported["temperature"] == 52.0
        mock_mongodb_repository.update_reported_state.assert_called_once_with(
            sample_device_shadow.device_id, new_reported_state
        )

        # Verify event was published to message broker
        mock_message_broker.publish_event.assert_called_once()
        # Verify the topic and event content
        args, kwargs = mock_message_broker.publish_event.call_args
        assert args[0] == "device-shadow-events"  # topic
        assert "DeviceShadowReportedStateUpdated" in str(args[1])  # event type
        assert kwargs["key"] == sample_device_shadow.device_id

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_shadow_delta(
        self, device_shadow_service, mock_mongodb_repository, sample_device_shadow
    ):
        """Test retrieving the delta between desired and reported states.

        This test verifies that the service correctly delegates to the MongoDB repository
        to calculate and return the delta between desired and reported states.
        """
        # Arrange
        expected_delta = {
            "delta": {
                "temperature": 55.0,  # Desired is 55.0, reported is 50.0
                "mode": "ECO",  # Only in desired
            }
        }

        mock_mongodb_repository.get_shadow_delta.return_value = expected_delta

        # Act
        result = await device_shadow_service.get_shadow_delta(
            sample_device_shadow.device_id
        )

        # Assert
        assert result == expected_delta
        mock_mongodb_repository.get_shadow_delta.assert_called_once_with(
            sample_device_shadow.device_id
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_create_device_shadow(
        self,
        device_shadow_service,
        mock_mongodb_repository,
        mock_message_broker,
        sample_device_shadow,
    ):
        """Test creating a new device shadow.

        This test verifies that the service correctly delegates to the MongoDB repository
        to create a new device shadow and publishes an event to the message broker.
        """
        # Arrange
        mock_mongodb_repository.create_device_shadow.return_value = sample_device_shadow

        # Act
        result = await device_shadow_service.create_device_shadow(sample_device_shadow)

        # Assert
        assert result == sample_device_shadow
        mock_mongodb_repository.create_device_shadow.assert_called_once_with(
            sample_device_shadow
        )

        # Verify event was published to message broker
        mock_message_broker.publish_event.assert_called_once()
        # Verify the topic and event content
        args, kwargs = mock_message_broker.publish_event.call_args
        assert args[0] == "device-shadow-events"  # topic
        assert "DeviceShadowCreated" in str(args[1])  # event type
        assert kwargs["key"] == sample_device_shadow.device_id

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_handle_shadow_sync(
        self,
        device_shadow_service,
        mock_mongodb_repository,
        mock_message_broker,
        sample_device_shadow,
    ):
        """Test handling shadow synchronization events from IoT devices.

        This test verifies that the service correctly processes shadow synchronization events
        received from IoT devices and updates the device shadow accordingly.
        """
        # Arrange
        # Message from an IoT device
        sync_message = {
            "device_id": sample_device_shadow.device_id,
            "reported": {
                "temperature": 53.0,  # Updated value
                "humidity": 47.0,  # Updated value
                "status": "ONLINE",
            },
            "client_token": "abc123",  # Client token for correlation
        }

        # Updated shadow after processing
        updated_shadow = DeviceShadow(
            device_id=sample_device_shadow.device_id,
            reported={"temperature": 53.0, "humidity": 47.0, "status": "ONLINE"},
            desired=sample_device_shadow.desired,
            version=sample_device_shadow.version + 1,
            timestamp=datetime.now().isoformat(),
        )

        mock_mongodb_repository.get_device_shadow.return_value = sample_device_shadow
        mock_mongodb_repository.update_reported_state.return_value = updated_shadow

        # Act
        result = await device_shadow_service.handle_shadow_sync(sync_message)

        # Assert
        assert result == updated_shadow
        mock_mongodb_repository.get_device_shadow.assert_called_once_with(
            sample_device_shadow.device_id
        )
        mock_mongodb_repository.update_reported_state.assert_called_once()

        # Verify what was passed to update_reported_state
        updated_reported = mock_mongodb_repository.update_reported_state.call_args[0][1]
        assert updated_reported["temperature"] == 53.0
        assert updated_reported["humidity"] == 47.0

        # Verify event was published to message broker
        mock_message_broker.publish_event.assert_called_once()

        # Verify acknowledgment message was published
        args, kwargs = mock_message_broker.publish_event.call_args
        assert args[0] == "device-shadow-events"  # topic
        assert "DeviceShadowReportedStateUpdated" in str(args[1])  # event type
        assert kwargs["key"] == sample_device_shadow.device_id
