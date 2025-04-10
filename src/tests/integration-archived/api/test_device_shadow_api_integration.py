"""
Integration tests for the Device Shadow API following TDD principles.

These tests validate the integration between the API layer and the service layer
following Clean Architecture principles. Tests are tagged with their TDD phase:
- @red: Tests that define expected behavior but will fail (not yet implemented)
- @green: Tests that pass with minimal implementation
- @refactor: Tests that continue to pass after code improvements

Currently all tests are in the RED phase as we're following the TDD approach.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.device_shadow import get_shadow_service
from src.main import app

# Create a test client
client = TestClient(app)

# Sample test data
TEST_DEVICE_ID = "test-device-001"
MOCK_SHADOW_DATA = {
    "device_id": TEST_DEVICE_ID,
    "reported": {"temperature": 120, "status": "ONLINE", "firmware_version": "v1.2.3"},
    "desired": {"target_temperature": 120},
    "version": 1,
    "timestamp": "2025-04-09T10:30:00Z",
}

# Mock update data
TEST_UPDATE_DATA = {"target_temperature": 125}


@pytest.fixture
def mock_shadow_service():
    """Create a mock shadow service for testing"""
    mock = MagicMock()

    # Setup mock methods
    mock.get_device_shadow.return_value = MOCK_SHADOW_DATA.copy()
    mock.update_desired_state.return_value = {
        "device_id": TEST_DEVICE_ID,
        "reported": MOCK_SHADOW_DATA["reported"],
        "desired": {**MOCK_SHADOW_DATA["desired"], **TEST_UPDATE_DATA},
        "version": MOCK_SHADOW_DATA["version"] + 1,
        "timestamp": "2025-04-09T10:35:00Z",
    }

    # Setup error behavior for non-existent device
    mock.get_device_shadow.side_effect = lambda device_id: (
        MOCK_SHADOW_DATA.copy() if device_id == TEST_DEVICE_ID else None
    )

    return mock


@pytest.mark.integration
@pytest.mark.api
class TestDeviceShadowAPI:
    """
    Integration tests for the Device Shadow API.
    These tests verify the API endpoints function correctly.
    """

    @patch("src.api.device_shadow.get_shadow_service")
    def test_get_device_shadow_success(self, mock_get_service, mock_shadow_service):
        """
        Test retrieving a device shadow successfully.
        RED phase: This test will initially fail if the endpoint is not implemented correctly.
        """
        # Arrange
        mock_get_service.return_value = mock_shadow_service

        # Act
        response = client.get(f"/api/shadows/{TEST_DEVICE_ID}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert "reported" in data
        assert "desired" in data
        assert data["reported"]["temperature"] == 120
        assert data["desired"]["target_temperature"] == 120

        # Verify the service was called
        mock_shadow_service.get_device_shadow.assert_called_once_with(TEST_DEVICE_ID)

    @patch("src.api.device_shadow.get_shadow_service")
    def test_get_device_shadow_not_found(self, mock_get_service, mock_shadow_service):
        """
        Test retrieving a non-existent device shadow.
        RED phase: This test will initially fail if error handling is not implemented.
        """
        # Arrange
        mock_get_service.return_value = mock_shadow_service
        non_existent_id = "non-existent-device"

        # Act
        response = client.get(f"/api/shadows/{non_existent_id}")

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()

        # Verify the service was called
        mock_shadow_service.get_device_shadow.assert_called_once_with(non_existent_id)

    @patch("src.api.device_shadow.get_shadow_service")
    def test_update_desired_state_success(self, mock_get_service, mock_shadow_service):
        """
        Test updating the desired state successfully.
        RED phase: This test will initially fail if the update endpoint is not implemented.
        """
        # Arrange
        mock_get_service.return_value = mock_shadow_service

        # Act
        response = client.patch(
            f"/api/shadows/{TEST_DEVICE_ID}/desired", json=TEST_UPDATE_DATA
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert data["desired"]["target_temperature"] == 125
        assert data["version"] == MOCK_SHADOW_DATA["version"] + 1

        # Verify the service was called with correct parameters
        mock_shadow_service.update_desired_state.assert_called_once_with(
            TEST_DEVICE_ID, TEST_UPDATE_DATA
        )

    @patch("src.api.device_shadow.get_shadow_service")
    def test_update_desired_state_validation(
        self, mock_get_service, mock_shadow_service
    ):
        """
        Test validation of desired state updates.
        RED phase: This test will initially fail if request validation is not implemented.
        """
        # Arrange
        mock_get_service.return_value = mock_shadow_service
        invalid_data = {"target_temperature": "not_a_number"}

        # Act
        response = client.patch(
            f"/api/shadows/{TEST_DEVICE_ID}/desired", json=invalid_data
        )

        # Assert
        assert response.status_code == 422  # Unprocessable Entity

        # Verify the service was not called
        mock_shadow_service.update_desired_state.assert_not_called()

    @pytest.mark.websocket
    def test_websocket_connection(self):
        """
        Test establishing a WebSocket connection for shadow updates.
        RED phase: This test will initially fail if WebSocket is not implemented.

        Note: This is a simplified test. In practice, WebSocket testing would require
        more sophisticated test fixtures and async testing approaches.
        """
        with client.websocket_connect(f"/api/ws/shadows/{TEST_DEVICE_ID}") as websocket:
            # Just test that we can connect
            assert websocket is not None

            # In a real test, we would send and receive messages
            # But that requires more complex async testing setup
