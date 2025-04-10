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

from src.api.device_shadow import get_device_shadow_service
from src.main import app
from src.use_cases.device_shadow_service import (  # Import use case class for proper typing
    DeviceShadowService,
)

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
    # Use proper typing with spec to enforce interface
    mock = MagicMock(spec=DeviceShadowService)

    # Setup mock methods
    mock.get_device_shadow.return_value = MOCK_SHADOW_DATA.copy()
    mock.update_desired_state.return_value = {
        "device_id": TEST_DEVICE_ID,
        "reported": MOCK_SHADOW_DATA["reported"],
        "desired": {**MOCK_SHADOW_DATA["desired"], **TEST_UPDATE_DATA},
        "version": MOCK_SHADOW_DATA["version"] + 1,
        "timestamp": "2025-04-09T10:35:00Z",
    }

    return mock


@pytest.fixture
def mock_get_service(mock_shadow_service):
    """Patch the service factory to return our mock"""
    with patch(
        "src.api.device_shadow.get_device_shadow_service",
        return_value=mock_shadow_service,
    ):
        yield


class TestDeviceShadowAPIToUseCase:
    """Integration tests for the Device Shadow API to Use Case boundary.

    These tests verify the API endpoints interact correctly with the use case layer,
    following Clean Architecture principles.
    """

    @pytest.mark.green  # Explicit TDD phase marker
    def test_get_device_shadow_success(self, mock_get_service, mock_shadow_service):
        """Test retrieving a device shadow successfully.

        RED phase: This test defines the expected behavior between API and use case layer.
        It will initially fail until the API implementation is complete.

        Business value: Enables monitoring of device state for facility managers.
        """
        # Execute - API call to controller
        response = client.get(f"/api/devices/{TEST_DEVICE_ID}/shadow")

        # Verify - API response format and status code
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert "reported" in data
        assert "desired" in data
        assert data["reported"]["temperature"] == 120
        assert data["desired"]["target_temperature"] == 120

        # Verify - Correct use case method was called with right parameters
        mock_shadow_service.get_device_shadow.assert_called_once_with(TEST_DEVICE_ID)

    @pytest.mark.green  # Explicit TDD phase marker
    def test_get_device_shadow_not_found(self, mock_get_service, mock_shadow_service):
        """Test retrieving a non-existent device shadow.

        RED phase: This test defines the expected error handling behavior.
        It validates that the API properly handles use case exceptions.

        Business value: Provides clear feedback when trying to access non-existent devices.
        """
        # Setup - Configure mock to raise exception for non-existent device
        non_existent_id = "non-existent-device"
        mock_shadow_service.get_device_shadow.side_effect = Exception(
            f"No shadow document exists for device {non_existent_id}"
        )

        # Execute - API call to controller
        response = client.get(f"/api/devices/{non_existent_id}/shadow")

        # Verify - Error response and status code
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data  # Error message should be in the response

        # Verify - Use case method was called with correct parameters
        mock_shadow_service.get_device_shadow.assert_called_once_with(non_existent_id)

    @pytest.mark.green  # Explicit TDD phase marker
    def test_update_desired_state_success(self, mock_get_service, mock_shadow_service):
        """Test updating the desired state successfully.

        RED phase: This test defines the expected behavior for updating device state.
        It validates that the API properly translates HTTP requests to use case calls.

        Business value: Enables remote control of water heater temperature settings.
        """
        # Execute - API call to controller
        response = client.patch(
            f"/api/devices/{TEST_DEVICE_ID}/shadow/desired", json=TEST_UPDATE_DATA
        )

        # Verify - Response format and status code
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert data["desired"]["target_temperature"] == 125
        assert data["version"] > MOCK_SHADOW_DATA["version"]

        # Verify - Use case method was called with correct parameters
        mock_shadow_service.update_desired_state.assert_called_once_with(
            TEST_DEVICE_ID, TEST_UPDATE_DATA
        )

    @pytest.mark.green  # Explicit TDD phase marker
    def test_update_desired_state_validation(
        self, mock_get_service, mock_shadow_service
    ):
        """Test validation of desired state updates.

        RED phase: This test defines the expected validation behavior.
        It ensures that the API properly validates incoming requests
        before passing them to the use case layer.

        Business value: Protects system integrity by rejecting invalid inputs.
        """
        # Invalid data - not a proper JSON object
        invalid_data = "not_a_json_object"

        # Execute - API call with invalid data
        response = client.patch(
            f"/api/devices/{TEST_DEVICE_ID}/shadow/desired", json=invalid_data
        )

        # Verify - Validation error response
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data  # Validation error details

        # Verify - Use case should not be called with invalid input
        mock_shadow_service.update_desired_state.assert_not_called()

    @pytest.mark.green  # Explicit TDD phase marker
    def test_websocket_connection(self):
        """Test establishing a WebSocket connection for shadow updates.

        RED phase: This test defines the expected WebSocket behavior for real-time
        device shadow updates.

        Business value: Enables real-time monitoring of water heater status for facility managers.

        Note: This is a simplified test. In practice, WebSocket testing would require
        more sophisticated test fixtures and async testing approaches.
        """
        import json

        from websockets.sync.client import connect

        # Using context manager to ensure proper connection handling
        try:
            with connect(
                f"ws://localhost:8000/api/devices/{TEST_DEVICE_ID}/shadow/updates"
            ) as websocket:
                # In a real implementation we would:
                # 1. Connect to WebSocket
                # 2. Trigger a shadow update via API
                # 3. Verify the update is received over WebSocket
                # 4. Validate message format
                assert websocket.open
        except Exception as e:
            # During RED phase, we expect this to fail since WebSocket isn't implemented yet
            pytest.fail(f"WebSocket connection failed: {str(e)}")

    # GREEN phase tests would be added here after implementation
    # They would have the @pytest.mark.green decorator

    # REFACTOR phase tests would be added after code improvements
    # They would have the @pytest.mark.refactor decorator
