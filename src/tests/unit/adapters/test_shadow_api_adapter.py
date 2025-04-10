"""
Unit tests for ShadowApiAdapter following TDD principles (RED phase).

This file demonstrates the RED phase of TDD where we define the expected
behavior of the ShadowApiAdapter before implementing the functionality.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.shadow_api_adapter import ShadowApiAdapter
from src.domain.exceptions import DeviceShadowNotFoundException

# Test data
TEST_DEVICE_ID = "test-device-001"
MOCK_SHADOW_STATE = {
    "reported": {"temperature": 120, "status": "ONLINE", "firmware_version": "v1.2.3"},
    "desired": {"target_temperature": 120},
    "version": 1,
    "timestamp": "2025-04-09T10:30:00Z",
}

# Expected shadow document format
EXPECTED_SHADOW_DOCUMENT = {
    "device_id": TEST_DEVICE_ID,
    "reported": MOCK_SHADOW_STATE["reported"],
    "desired": MOCK_SHADOW_STATE["desired"],
    "version": MOCK_SHADOW_STATE["version"],
    "timestamp": MOCK_SHADOW_STATE["timestamp"],
}

# Test update data
TEST_UPDATE_DATA = {"target_temperature": 125}


@pytest.fixture
def mock_shadow_client():
    """Create a mock shadow client for testing."""
    mock = AsyncMock()

    # Setup get_shadow_state behavior
    mock.get_shadow_state = AsyncMock(return_value=MOCK_SHADOW_STATE)

    # Setup update_desired_state behavior
    updated_state = {
        **MOCK_SHADOW_STATE,
        "desired": {**MOCK_SHADOW_STATE["desired"], **TEST_UPDATE_DATA},
        "version": MOCK_SHADOW_STATE["version"] + 1,
        "timestamp": "2025-04-09T10:35:00Z",
    }
    mock.update_desired_state = AsyncMock(return_value=updated_state)

    # Setup error case for non-existent device
    mock.get_shadow_state.side_effect = lambda device_id: (
        MOCK_SHADOW_STATE if device_id == TEST_DEVICE_ID else None
    )

    return mock


@pytest.mark.unit
class TestShadowApiAdapter:
    """
    Unit tests for the ShadowApiAdapter class.

    These tests follow the RED phase of TDD, defining expected behavior
    before implementation.
    """

    async def test_get_device_shadow_success(self, mock_shadow_client):
        """
        Test retrieving a device shadow successfully.
        RED phase: This test will initially fail until ShadowApiAdapter is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)

        # Act
        result = await adapter.get_device_shadow(TEST_DEVICE_ID)

        # Assert
        assert result == EXPECTED_SHADOW_DOCUMENT
        mock_shadow_client.get_shadow_state.assert_called_once_with(TEST_DEVICE_ID)

    async def test_get_device_shadow_not_found(self, mock_shadow_client):
        """
        Test handling of a non-existent device shadow.
        RED phase: This test will initially fail until error handling is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)
        non_existent_id = "non-existent-device"

        # Act & Assert
        with pytest.raises(DeviceShadowNotFoundException):
            await adapter.get_device_shadow(non_existent_id)

        mock_shadow_client.get_shadow_state.assert_called_once_with(non_existent_id)

    async def test_update_desired_state_success(self, mock_shadow_client):
        """
        Test updating the desired state successfully.
        RED phase: This test will initially fail until the update method is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)

        # Act
        result = await adapter.update_desired_state(TEST_DEVICE_ID, TEST_UPDATE_DATA)

        # Assert
        assert result["device_id"] == TEST_DEVICE_ID
        assert result["desired"]["target_temperature"] == 125
        assert result["version"] == MOCK_SHADOW_STATE["version"] + 1

        mock_shadow_client.update_desired_state.assert_called_once_with(
            TEST_DEVICE_ID, TEST_UPDATE_DATA
        )

    async def test_get_real_time_updates_setup(self, mock_shadow_client):
        """
        Test setting up real-time updates for a device.
        RED phase: This test will initially fail until WebSocket functionality is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)
        mock_callback = MagicMock()

        # Simulate the shadow client's subscribe_to_updates method
        mock_shadow_client.subscribe_to_updates = AsyncMock()

        # Act
        await adapter.get_real_time_updates(TEST_DEVICE_ID, mock_callback)

        # Assert
        mock_shadow_client.subscribe_to_updates.assert_called_once_with(
            TEST_DEVICE_ID, mock_callback
        )

    async def test_format_shadow_document(self, mock_shadow_client):
        """
        Test the internal method that formats shadow state into a shadow document.
        RED phase: This test will initially fail until the format method is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)

        # Act
        result = adapter._format_shadow_document(TEST_DEVICE_ID, MOCK_SHADOW_STATE)

        # Assert
        assert result == EXPECTED_SHADOW_DOCUMENT

    async def test_validate_shadow_update(self, mock_shadow_client):
        """
        Test validation of shadow updates.
        RED phase: This test will initially fail until validation is implemented.
        """
        # Arrange
        adapter = ShadowApiAdapter(mock_shadow_client)
        invalid_data = {"target_temperature": "not_a_number"}

        # Act & Assert
        with pytest.raises(ValueError):
            await adapter.update_desired_state(TEST_DEVICE_ID, invalid_data)
