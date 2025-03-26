"""
Test file for vending machine API that uses direct patching.

This test file demonstrates how to effectively test FastAPI routes by directly patching
the service methods used by the routes.
"""
import pytest
import importlib
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient

from src.models.device import DeviceType, DeviceStatus
from src.models.vending_machine import (
    VendingMachineStatus,
    VendingMachineMode,
    ProductItem,
    VendingMachine
)
from src.services.vending_machine import VendingMachineService
from src.main import app


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


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Direct patch of the service methods used by the API routes
@patch('src.services.vending_machine.VendingMachineService.get_all_vending_machines')
def test_get_all_vending_machines(mock_get_all, test_client, sample_vm):
    """Test GET /api/vending-machines endpoint."""
    # Configure the mock
    mock_get_all.return_value = [sample_vm]
    
    # Make request
    response = test_client.get("/api/vending-machines")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "vm-001"
    assert data[0]["name"] == "Campus Center VM"
    
    # Verify mock was called
    mock_get_all.assert_called_once()


@patch('src.services.vending_machine.VendingMachineService.get_vending_machine')
def test_get_vending_machine(mock_get_vm, test_client, sample_vm):
    """Test GET /api/vending-machines/{vm_id} endpoint."""
    # Configure the mock
    mock_get_vm.return_value = sample_vm
    
    # Make request
    response = test_client.get("/api/vending-machines/vm-001")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "vm-001"
    assert data["name"] == "Campus Center VM"
    
    # Verify mock was called with correct args
    mock_get_vm.assert_called_once_with("vm-001")


@patch('src.services.vending_machine.VendingMachineService.create_vending_machine')
def test_create_vending_machine(mock_create_vm, test_client, sample_vm):
    """Test POST /api/vending-machines endpoint."""
    # Configure the mock
    mock_create_vm.return_value = sample_vm
    
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
    assert data["id"] == "vm-001"
    
    # Verify mock was called
    mock_create_vm.assert_called_once()


@patch('src.services.vending_machine.VendingMachineService.update_vending_machine')
def test_update_vending_machine(mock_update_vm, test_client, sample_vm):
    """Test PATCH /api/vending-machines/{vm_id} endpoint."""
    # Configure the mock
    mock_update_vm.return_value = sample_vm
    
    # Prepare update data
    update_data = {
        "name": "Updated VM Name",
        "temperature": 5.0
    }
    
    # Make request
    response = test_client.patch("/api/vending-machines/vm-001", json=update_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Campus Center VM"  # We're using the mocked return value
    assert data["id"] == "vm-001"
    
    # Verify mock was called
    mock_update_vm.assert_called_once()
