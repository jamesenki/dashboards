from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.device import DeviceStatus, DeviceType
from src.models.vending_machine import (
    LocationType,
    SubLocation,
    VendingMachine,
    VendingMachineMode,
    VendingMachineStatus,
)
from src.services.service_locator import get_service
from src.services.vending_machine import VendingMachineService


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database fixture."""
    return MagicMock()


@pytest.fixture
def sample_vm():
    """Sample vending machine fixture."""
    return VendingMachine(
        id="vm-test-123",
        name="Test Vending Machine",
        type=DeviceType.VENDING_MACHINE,
        status=DeviceStatus.ONLINE,
        location="Test Location",
        model_number="PD-2000",
        serial_number="PD2023-54321",
        machine_status=VendingMachineStatus.OPERATIONAL,
        mode=VendingMachineMode.NORMAL,
        temperature=4.0,
        total_capacity=50,
        cash_capacity=500.0,
        current_cash=125.50,
        location_business_name="Test Business",
        location_type=LocationType.RETAIL,
        sub_location=SubLocation.LOBBY,
    )


# Test endpoints for fetching operations data
# Verify payload structure matches expected format
# Test error handling (machine not found, etc.)
class TestVendingMachineOperationsAPI:
    def test_get_vending_machine_operations(self, test_client, sample_vm):
        """Test GET /api/vending-machines/{vm_id}/operations endpoint."""
        # Setup mock
        with patch("src.services.service_locator.get_service") as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            mock_service.get_vending_machine_operations.return_value = [
                {
                    "id": "op-1",
                    "name": "Restocking",
                    "type": "maintenance",
                    "state": "completed",
                    "start_time": "2025-03-25T10:00:00Z",
                    "end_time": "2025-03-25T10:30:00Z",
                }
            ]

            # Make request
            response = test_client.get(
                f"/api/vending-machines/{sample_vm.id}/operations"
            )

            # Check response
            assert response.status_code == 200
            operations = response.json()
            assert isinstance(operations, list)
            assert len(operations) > 0
            for operation in operations:
                assert "id" in operation
                assert "name" in operation
                assert "type" in operation
                assert "state" in operation
                assert "start_time" in operation
                assert "end_time" in operation

    def test_get_vending_machine_operations_vm_not_found(self, test_client, sample_vm):
        """Test GET /api/vending-machines/{vm_id}/operations endpoint with non-existent VM."""
        # Setup mock
        with patch("src.services.service_locator.get_service") as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            mock_service.get_vending_machine_operations.side_effect = ValueError(
                "Vending machine not found"
            )

            # Make request
            response = test_client.get(
                "/api/vending-machines/non-existent-vm/operations"
            )

            # Check response
            assert response.status_code == 404
