"""
Integration test for Device Shadow API to Use Case interaction.
Tests the boundary between API controllers and shadow service use cases.

This file demonstrates proper TDD phases with explicit tagging and follows
Clean Architecture principles by testing only the boundary between layers.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.device_shadow import get_device_shadow_service
from src.main import app
from src.use_cases.device_shadow_service import DeviceShadowService

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
    """Create a mock shadow service for testing the API layer.

    This fixture isolates the API layer from the actual use case implementation,
    allowing us to test just the API to use case boundary.
    """
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

    # Setup error case
    mock.get_device_shadow.side_effect = lambda device_id: (
        MOCK_SHADOW_DATA.copy()
        if device_id == TEST_DEVICE_ID
        else pytest.raises(
            Exception(f"No shadow document exists for device {device_id}")
        )
    )

    return mock


@pytest.fixture
def mock_get_service(mock_shadow_service):
    """Patch the service factory to return our mock service.

    This ensures the API layer receives our test double instead of
    creating a real service instance, maintaining clean separation.
    """
    with patch(
        "src.api.device_shadow.get_device_shadow_service",
        return_value=mock_shadow_service,
    ):
        yield


class TestDeviceShadowAPIToUseCase:
    """Integration tests for the Device Shadow API to Use Case boundary.

    These tests validate that:
    1. The API correctly translates HTTP requests to use case method calls
    2. The API properly handles responses from the use case
    3. The use case interface is being used correctly by the API

    Following Clean Architecture principles, we only test the boundary between
    the API and use case layers, not the implementation details of either.
    """

    @pytest.mark.red  # TDD Red phase - defining expected behavior
    def test_get_device_shadow_success(self, mock_get_service, mock_shadow_service):
        """Test retrieving a device shadow successfully.

        RED phase: This test defines the expected behavior between API and service layer.
        It will initially fail until the API implementation is complete.

        This tests the boundary between:
        - API Layer (Controller): The HTTP endpoint for device shadow
        - Use Case Layer: The shadow service functionality
        """
        # Execute
        response = client.get(f"/api/devices/{TEST_DEVICE_ID}/shadow")

        # Verify response to client
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert "reported" in data
        assert "desired" in data
        assert data["reported"]["temperature"] == 120
        assert data["desired"]["target_temperature"] == 120

        # Verify correct use case method was called with correct parameters
        mock_shadow_service.get_device_shadow.assert_called_once_with(TEST_DEVICE_ID)

    @pytest.mark.red  # TDD Red phase
    def test_get_device_shadow_not_found(self, mock_get_service, mock_shadow_service):
        """Test retrieving a non-existent device shadow.

        RED phase: This test defines the expected error handling behavior.
        It validates that the API properly handles use case exceptions
        and returns appropriate HTTP status codes.

        This tests the boundary handling between:
        - API Layer: Error handling and status code translation
        - Use Case Layer: Exception propagation
        """
        # Setup
        non_existent_id = "non-existent-device"
        mock_shadow_service.get_device_shadow.side_effect = Exception(
            f"No shadow document exists for device {non_existent_id}"
        )

        # Execute
        response = client.get(f"/api/devices/{non_existent_id}/shadow")

        # Verify
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data  # Error message should be in the response

        # Verify correct use case method was called with correct parameters
        mock_shadow_service.get_device_shadow.assert_called_once_with(non_existent_id)

    @pytest.mark.red  # TDD Red phase
    def test_update_desired_state_success(self, mock_get_service, mock_shadow_service):
        """Test updating the desired state successfully.

        RED phase: This test defines the expected behavior for updating device state.
        It validates that the API properly translates HTTP requests to use case calls
        and returns the updated shadow document.

        This tests the boundary between:
        - API Layer: Request validation and response formatting
        - Use Case Layer: State update functionality
        """
        # Execute
        response = client.patch(
            f"/api/devices/{TEST_DEVICE_ID}/shadow/desired", json=TEST_UPDATE_DATA
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == TEST_DEVICE_ID
        assert data["desired"]["target_temperature"] == 125
        assert data["version"] > MOCK_SHADOW_DATA["version"]

        # Verify use case was called correctly with proper parameters
        mock_shadow_service.update_desired_state.assert_called_once_with(
            TEST_DEVICE_ID, TEST_UPDATE_DATA
        )

    @pytest.mark.red  # TDD Red phase
    def test_update_desired_state_validation(
        self, mock_get_service, mock_shadow_service
    ):
        """Test validation of desired state updates.

        RED phase: This test defines the expected validation behavior.
        It ensures that the API properly validates incoming requests
        before passing them to the use case layer.

        This tests the input validation in:
        - API Layer: Request validation before use case invocation
        - Clean Architecture: Protecting domain rules via validation
        """
        # Invalid data - not a proper JSON object
        invalid_data = "not_a_json_object"

        # Execute
        response = client.patch(
            f"/api/devices/{TEST_DEVICE_ID}/shadow/desired", json=invalid_data
        )

        # Verify
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data  # Validation error details

        # Service should not be called with invalid input
        mock_shadow_service.update_desired_state.assert_not_called()

    @pytest.mark.red  # TDD Red phase
    def test_websocket_connection(self):
        """Test establishing a WebSocket connection for shadow updates.

        RED phase: This test defines the expected WebSocket behavior.
        It validates that real-time updates can be received over WebSocket.

        This tests the boundary between:
        - API Layer: WebSocket endpoint and event streaming
        - Use Case Layer: Event publication mechanisms

        Note: This is a simplified test. In practice, WebSocket testing would require
        more sophisticated test fixtures and async testing approaches.
        """
        import json

        from websockets.sync.client import connect

        # Using context manager to ensure the connection is closed properly
        try:
            with connect(
                f"ws://localhost:8000/api/devices/{TEST_DEVICE_ID}/shadow/updates"
            ) as websocket:
                # In a real implementation we would wait for and validate messages
                # This simplistic check just verifies that a connection can be established
                assert websocket.open

                # A more complete test would:
                # 1. Connect to WebSocket
                # 2. Trigger a shadow update via a separate API call
                # 3. Verify the update is received over the WebSocket
                # 4. Validate message format follows Clean Architecture principles
        except Exception as e:
            # During RED phase, we expect this to fail so we'll catch exceptions
            # In GREEN phase, we would remove this exception handling
            pytest.fail(f"WebSocket connection failed: {str(e)}")
