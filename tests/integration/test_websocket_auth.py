import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from src.config.security import ALGORITHM, SECRET_KEY
from src.main import app
from src.models.user import UserRole

"""
Tests for WebSocket authentication
These tests verify that WebSocket connections require proper authentication
and that permissions are enforced correctly.
"""

# Test constants
TEST_USER_ID = "test-user-123"
TEST_USERNAME = "test_facility_manager"
TEST_DEVICE_ID = "test-device-001"


def create_test_token(
    user_id: str,
    username: str,
    role: str = UserRole.FACILITY_MANAGER,
    expired: bool = False,
):
    """Create a test JWT token with configurable expiration"""
    expiration = datetime.utcnow() + (
        timedelta(minutes=-1) if expired else timedelta(days=1)
    )

    payload = {"sub": user_id, "username": username, "role": role, "exp": expiration}

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_websocket_connection_requires_token():
    """Test that WebSocket connections require a valid token"""
    client = TestClient(app)

    # Attempt to connect without a token
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws/devices/{TEST_DEVICE_ID}/state"):
            pass

    # Verify the connection was rejected with the correct status code
    assert excinfo.value.code == 1008  # Policy violation


@pytest.mark.asyncio
async def test_websocket_connection_with_valid_token():
    """Test that WebSocket connections succeed with a valid token"""
    client = TestClient(app)

    # Create a valid token
    token = create_test_token(TEST_USER_ID, TEST_USERNAME)

    # Mock the shadow service to avoid DB access
    with patch("src.api.routes.websocket.get_shadow_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_shadow = {
            "device_id": TEST_DEVICE_ID,
            "reported": {},
            "desired": {},
            "version": 1,
        }
        mock_service.get_device_shadow.return_value = mock_shadow
        mock_get_service.return_value = mock_service

        # Connect with a valid token
        with client.websocket_connect(
            f"/ws/devices/{TEST_DEVICE_ID}/state",
            headers={"Authorization": f"Bearer {token}"},
        ) as websocket:
            # Verify we can receive data
            response = websocket.receive_text()
            assert response is not None

            # Verify we can send a message
            websocket.send_text(json.dumps({"type": "get_state"}))
            response = websocket.receive_text()
            assert response is not None


@pytest.mark.asyncio
async def test_websocket_connection_with_expired_token():
    """Test that WebSocket connections are rejected with an expired token"""
    client = TestClient(app)

    # Create an expired token
    expired_token = create_test_token(TEST_USER_ID, TEST_USERNAME, expired=True)

    # Attempt to connect with an expired token
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(
            f"/ws/devices/{TEST_DEVICE_ID}/state",
            headers={"Authorization": f"Bearer {expired_token}"},
        ):
            pass

    # Verify the connection was rejected with the correct status code
    assert excinfo.value.code == 1008  # Policy violation


@pytest.mark.asyncio
async def test_websocket_connection_role_based_access():
    """Test that role-based permissions are enforced for WebSocket connections"""
    client = TestClient(app)

    # Create tokens for different roles
    admin_token = create_test_token(TEST_USER_ID, TEST_USERNAME, role=UserRole.ADMIN)
    readonly_token = create_test_token(
        TEST_USER_ID, TEST_USERNAME, role=UserRole.READ_ONLY
    )

    # Mock the shadow service
    with patch("src.api.routes.websocket.get_shadow_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_shadow = {
            "device_id": TEST_DEVICE_ID,
            "reported": {},
            "desired": {},
            "version": 1,
        }
        mock_service.get_device_shadow.return_value = mock_shadow
        mock_get_service.return_value = mock_service

        # Test admin access (should be able to both read and write)
        with client.websocket_connect(
            f"/ws/devices/{TEST_DEVICE_ID}/state",
            headers={"Authorization": f"Bearer {admin_token}"},
        ) as websocket:
            # Send a command to update desired state (write operation)
            websocket.send_text(
                json.dumps({"type": "update_desired", "desired": {"temperature": 60.0}})
            )

            # Should get a success response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert "status" in response_data
            assert response_data["status"] == "success"

        # Test read-only access (should be able to read but not write)
        with client.websocket_connect(
            f"/ws/devices/{TEST_DEVICE_ID}/state",
            headers={"Authorization": f"Bearer {readonly_token}"},
        ) as websocket:
            # First verify we can read
            websocket.send_text(json.dumps({"type": "get_state"}))
            response = websocket.receive_text()
            assert response is not None

            # Now try to update desired state (should be rejected)
            websocket.send_text(
                json.dumps({"type": "update_desired", "desired": {"temperature": 65.0}})
            )

            # Should get an error response due to insufficient permissions
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert "error" in response_data
            assert "permission" in response_data["error"].lower()
