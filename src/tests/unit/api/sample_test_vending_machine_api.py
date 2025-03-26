"""
Sample test file for vending machine API that demonstrates proper testing isolation.

This test file shows how to use the test_helpers module to run API tests with
properly isolated dependencies.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# Import our test fixtures from test_helpers
from src.tests.test_helpers import test_client, test_env

from src.models.device import DeviceType, DeviceStatus
from src.models.vending_machine import (
    VendingMachineStatus,
    VendingMachineMode,
    ProductItem,
    VendingMachineReading,
    VendingMachine
)
from src.services.vending_machine import VendingMachineService


# Fixtures are imported from test_helpers


@pytest.fixture
def sample_vm():
    """Create a sample vending machine for testing."""
    return VendingMachine(
        id="vm-001",
        name="Campus Center VM",
        type=DeviceType.VENDING_MACHINE,
        status=DeviceStatus.ONLINE,
        location="Building B, Floor 1",
        model_number="PD-2000",
        serial_number="PD2023-12345",
        machine_status=VendingMachineStatus.OPERATIONAL,
        mode=VendingMachineMode.NORMAL,
        temperature=4.0,
        total_capacity=50,
        cash_capacity=500.0,
        current_cash=125.50,
        products=[
            ProductItem(
                product_id="PD001",
                name="Polar Delight Classic",
                price=2.50,
                quantity=10,
                category="Beverages",
                location="A1"
            )
        ]
    )


def test_get_all_vending_machines(test_client, test_env, sample_vm):
    """Test GET /api/vending-machines endpoint with proper isolation."""
    # Configure the mock to return our sample data
    test_env.mock_vending_machine_service.get_all_vending_machines.return_value = [sample_vm]
    
    # Make request to the endpoint
    response = test_client.get("/api/vending-machines")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # This will now pass because we're using the mock
    assert data[0]["id"] == "vm-001"
    assert data[0]["name"] == "Campus Center VM"
    
    # Verify mock was called
    test_env.mock_vending_machine_service.get_all_vending_machines.assert_called_once()


def test_get_vending_machine(test_client, test_env, sample_vm):
    """Test GET /api/vending-machines/{vm_id} endpoint with proper isolation."""
    # Configure the mock to return our sample data
    test_env.mock_vending_machine_service.get_vending_machine.return_value = sample_vm
    
    # Make request
    response = test_client.get("/api/vending-machines/vm-001")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "vm-001"
    assert data["name"] == "Campus Center VM"
    
    # Verify mock was called with correct parameters
    test_env.mock_vending_machine_service.get_vending_machine.assert_called_once_with("vm-001")


def test_create_vending_machine(test_client, test_env, sample_vm):
    """Test POST /api/vending-machines endpoint with proper isolation."""
    # Configure the mock to return our sample data
    test_env.mock_vending_machine_service.create_vending_machine.return_value = sample_vm
    
    # Prepare data for request
    new_vm_data = {
        "name": "Campus Center VM",
        "location": "Building B, Floor 1",
        "model_number": "PD-2000",
        "serial_number": "PD2023-12345"
    }
    
    # Make request
    response = test_client.post("/api/vending-machines", json=new_vm_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Campus Center VM"
    assert data["id"] == "vm-001"  # Will match because we're returning sample_vm
    
    # Verify mock was called
    test_env.mock_vending_machine_service.create_vending_machine.assert_called_once()
