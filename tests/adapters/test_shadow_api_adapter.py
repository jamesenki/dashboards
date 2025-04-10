"""
Tests for the Shadow API Adapter component following TDD principles.

These tests verify that the adapter properly bridges between the new Shadow
Integration and existing API contracts.
"""
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.shadow_api_adapter import ShadowApiAdapter
from src.infrastructure.client.shadow_client_adapter import (
    ShadowClientAdapter,
    ShadowUpdateEvent,
)
from src.infrastructure.messaging.shadow_broker_integration import (
    ShadowBrokerIntegration,
)


class TestShadowApiAdapter:
    """Test suite for the Shadow API Adapter implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_shadow_broker = AsyncMock(spec=ShadowBrokerIntegration)
        self.mock_notification_service = AsyncMock()
        self.mock_client_adapter = AsyncMock(spec=ShadowClientAdapter)

        # Configure the client adapter mock
        self.mock_client_adapter.get_current_state.return_value = {
            "reported": {"temperature": 120, "status": "ONLINE"},
            "desired": {"temperature": 125},
            "version": 2,
            "timestamp": datetime.now().isoformat(),
        }

        # Configure the adapter with a mock client factory
        def mock_client_factory(base_url, device_id):
            self.mock_client_adapter.device_id = device_id
            return self.mock_client_adapter

        # Create adapter with mocks
        self.adapter = ShadowApiAdapter(
            shadow_broker_integration=self.mock_shadow_broker,
            shadow_notification_service=self.mock_notification_service,
            client_adapter_factory=mock_client_factory,
            base_ws_url="ws://test/api/ws/shadows",
        )

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_broker_initialize(self):
        """Test that ensure_initialized calls initialize on the shadow broker."""
        # Act
        await self.adapter.ensure_initialized()

        # Assert
        self.mock_shadow_broker.initialize.assert_called_once()
        assert self.adapter._initialized is True

    @pytest.mark.asyncio
    async def test_get_device_shadow_returns_formatted_shadow(self):
        """Test that get_device_shadow returns a properly formatted shadow document."""
        # Arrange
        device_id = "test-device"

        # Act
        result = await self.adapter.get_device_shadow(device_id)

        # Assert
        self.mock_client_adapter.connect.assert_called_once()
        self.mock_client_adapter.subscribe.assert_called_once()
        self.mock_client_adapter.get_current_state.assert_called_once()
        self.mock_client_adapter.disconnect.assert_called_once()

        assert result["device_id"] == device_id
        assert result["reported"]["temperature"] == 120
        assert result["reported"]["status"] == "ONLINE"
        assert result["desired"]["temperature"] == 125
        assert result["version"] == 2

    @pytest.mark.asyncio
    async def test_update_device_shadow_calls_client_update(self):
        """Test that update_device_shadow calls update_desired_state on the client adapter."""
        # Arrange
        device_id = "test-device"
        desired_state = {"temperature": 130, "mode": "VACATION"}
        self.mock_client_adapter.update_desired_state.return_value = {
            "success": True,
            "version": 3,
        }

        # Act
        result = await self.adapter.update_device_shadow(device_id, desired_state)

        # Assert
        self.mock_client_adapter.connect.assert_called_once()
        self.mock_client_adapter.update_desired_state.assert_called_once_with(
            desired_state
        )
        self.mock_client_adapter.disconnect.assert_called_once()

        assert result["success"] is True
        assert result["device_id"] == device_id
        assert result["version"] == 3
        assert "temperature" in result["pending"]
        assert "mode" in result["pending"]

    @pytest.mark.asyncio
    async def test_update_device_shadow_handles_errors(self):
        """Test that update_device_shadow handles errors from the client adapter."""
        # Arrange
        device_id = "test-device"
        desired_state = {"temperature": 130}
        self.mock_client_adapter.update_desired_state.side_effect = ValueError(
            "Test error"
        )

        # Act
        result = await self.adapter.update_device_shadow(device_id, desired_state)

        # Assert
        assert result["success"] is False
        assert result["device_id"] == device_id
        assert "message" in result
        assert "Test error" in result["message"]

    @pytest.mark.asyncio
    async def test_get_all_shadows_delegates_to_broker(self):
        """Test that get_all_shadows delegates to the shadow broker."""
        # Arrange
        self.mock_shadow_broker.get_all_shadows.return_value = [
            {"device_id": "device1"},
            {"device_id": "device2"},
        ]

        # Act
        result = await self.adapter.get_all_shadows()

        # Assert
        self.mock_shadow_broker.get_all_shadows.assert_called_once()
        assert len(result) == 2
        assert result[0]["device_id"] == "device1"
        assert result[1]["device_id"] == "device2"

    @pytest.mark.asyncio
    async def test_get_shadow_history_delegates_to_broker(self):
        """Test that get_shadow_history delegates to the shadow broker."""
        # Arrange
        device_id = "test-device"
        self.mock_shadow_broker.get_shadow_history.return_value = [
            {"timestamp": "2023-01-01T00:00:00Z"},
            {"timestamp": "2023-01-01T00:01:00Z"},
        ]

        # Act
        result = await self.adapter.get_shadow_history(device_id, limit=2)

        # Assert
        self.mock_shadow_broker.get_shadow_history.assert_called_once_with(device_id, 2)
        assert len(result) == 2
