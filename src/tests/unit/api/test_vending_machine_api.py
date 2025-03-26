import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.models.device import DeviceType, DeviceStatus
from src.models.vending_machine import (
    VendingMachineStatus,
    VendingMachineMode,
    ProductItem,
    VendingMachineReading,
    VendingMachine
)
from src.services.vending_machine import VendingMachineService
from src.main import app

# Mock the service locator before importing the API module
with patch('src.services.service_locator.get_service') as mock_get_service:
    # Now import the module that uses the patched function
    from src.api.vending_machine import router


class TestVendingMachineAPI:
    """Test cases for vending machine API endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create test client
        self.client = TestClient(app)
        
        # Create sample vending machine
        self.sample_vm = VendingMachine(
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
        
        # Mock service
        self.mock_service = MagicMock(spec=VendingMachineService)
    
    @patch('src.services.service_locator.get_service')
    def test_get_all_vending_machines(self, mock_get_service):
        """Test GET /api/vending-machines endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        self.mock_service.get_all_vending_machines.return_value = [self.sample_vm]
        
        # Make request
        response = self.client.get("/api/vending-machines")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "vm-001"
        assert data[0]["name"] == "Campus Center VM"
        assert data[0]["type"] == "vending_machine"
        
        # Verify mock was called
        self.mock_service.get_all_vending_machines.assert_called_once()
    
    @patch('src.services.service_locator.get_service')
    def test_get_vending_machine(self, mock_get_service):
        """Test GET /api/vending-machines/{vm_id} endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        self.mock_service.get_vending_machine.return_value = self.sample_vm
        
        # Make request
        response = self.client.get("/api/vending-machines/vm-001")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "vm-001"
        assert data["name"] == "Campus Center VM"
        assert data["model_number"] == "PD-2000"
        
        # Verify mock was called
        self.mock_service.get_vending_machine.assert_called_once_with("vm-001")
    
    @patch('src.services.service_locator.get_service')
    def test_get_vending_machine_not_found(self, mock_get_service):
        """Test GET /api/vending-machines/{vm_id} with invalid ID."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        self.mock_service.get_vending_machine.side_effect = ValueError("Vending machine not found")
        
        # Make request
        response = self.client.get("/api/vending-machines/invalid-id")
        
        # Check response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        
        # Verify mock was called
        self.mock_service.get_vending_machine.assert_called_once_with("invalid-id")
    
    @patch('src.services.service_locator.get_service')
    def test_create_vending_machine(self, mock_get_service):
        """Test POST /api/vending-machines endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        self.mock_service.create_vending_machine.return_value = self.sample_vm
        
        # Prepare data
        vm_data = {
            "name": "New Vending Machine",
            "location": "Building C, Floor 2",
            "model_number": "PD-3000",
            "serial_number": "PD2023-67890",
            "temperature": 4.0,
            "total_capacity": 60,
            "cash_capacity": 600.0
        }
        
        # Make request
        response = self.client.post("/api/vending-machines", json=vm_data)
        
        # Check response
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Campus Center VM"  # Using mock data
        assert data["type"] == "vending_machine"
        
        # Verify mock was called with correct args
        self.mock_service.create_vending_machine.assert_called_once()
        call_args = self.mock_service.create_vending_machine.call_args[1]
        assert call_args["name"] == "New Vending Machine"
        assert call_args["location"] == "Building C, Floor 2"
        assert call_args["model_number"] == "PD-3000"
    
    @patch('src.services.service_locator.get_service')
    def test_update_vending_machine(self, mock_get_service):
        """Test PATCH /api/vending-machines/{vm_id} endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        updated_vm = self.sample_vm.model_copy(deep=True)
        updated_vm.name = "Updated VM Name"
        updated_vm.location = "New Location"
        self.mock_service.update_vending_machine.return_value = updated_vm
        
        # Prepare data
        update_data = {
            "name": "Updated VM Name",
            "location": "New Location"
        }
        
        # Make request
        response = self.client.patch("/api/vending-machines/vm-001", json=update_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated VM Name"
        assert data["location"] == "New Location"
        
        # Verify mock was called with correct args
        self.mock_service.update_vending_machine.assert_called_once()
        call_args = self.mock_service.update_vending_machine.call_args[1]
        assert call_args["vm_id"] == "vm-001"
        assert call_args["name"] == "Updated VM Name"
        assert call_args["location"] == "New Location"
    
    @patch('src.services.service_locator.get_service')
    def test_delete_vending_machine(self, mock_get_service):
        """Test DELETE /api/vending-machines/{vm_id} endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        self.mock_service.delete_vending_machine.return_value = True
        
        # Make request
        response = self.client.delete("/api/vending-machines/vm-001")
        
        # Check response
        assert response.status_code == 204
        
        # Verify mock was called
        self.mock_service.delete_vending_machine.assert_called_once_with("vm-001")
    
    @patch('src.services.service_locator.get_service')
    def test_add_product(self, mock_get_service):
        """Test POST /api/vending-machines/{vm_id}/products endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        updated_vm = self.sample_vm.model_copy(deep=True)
        new_product = ProductItem(
            product_id="PD002",
            name="Polar Delight Zero",
            price=2.75,
            quantity=8,
            category="Beverages",
            location="A2"
        )
        updated_vm.add_product(new_product)
        self.mock_service.add_product.return_value = updated_vm
        
        # Prepare data
        product_data = {
            "product_id": "PD002",
            "name": "Polar Delight Zero",
            "price": 2.75,
            "quantity": 8,
            "category": "Beverages",
            "location": "A2"
        }
        
        # Make request
        response = self.client.post("/api/vending-machines/vm-001/products", json=product_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2
        assert data["products"][1]["product_id"] == "PD002"
        assert data["products"][1]["name"] == "Polar Delight Zero"
        
        # Verify mock was called
        self.mock_service.add_product.assert_called_once()
    
    @patch('src.services.service_locator.get_service')
    def test_update_product_quantity(self, mock_get_service):
        """Test PUT /api/vending-machines/{vm_id}/products/{product_id}/quantity endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        updated_vm = self.sample_vm.model_copy(deep=True)
        updated_vm.update_product_quantity("PD001", -3)
        self.mock_service.update_product_quantity.return_value = updated_vm
        
        # Prepare data
        quantity_data = {"quantity_change": -3}
        
        # Make request
        response = self.client.put("/api/vending-machines/vm-001/products/PD001/quantity", 
                                  json=quantity_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["products"][0]["quantity"] == 7  # mock data shows updated quantity
        
        # Verify mock was called
        self.mock_service.update_product_quantity.assert_called_once_with("vm-001", "PD001", -3)
    
    @patch('src.services.service_locator.get_service')
    def test_add_reading(self, mock_get_service):
        """Test POST /api/vending-machines/{vm_id}/readings endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        updated_vm = self.sample_vm.model_copy(deep=True)
        reading = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=4.5,
            power_consumption=120.5,
            door_status="CLOSED",
            cash_level=85.50,
            sales_count=12
        )
        updated_vm.add_reading(reading)
        self.mock_service.add_reading.return_value = updated_vm
        
        # Prepare data (exclude timestamp as it will be generated)
        reading_data = {
            "temperature": 4.5,
            "power_consumption": 120.5,
            "door_status": "CLOSED",
            "cash_level": 85.50,
            "sales_count": 12
        }
        
        # Make request
        response = self.client.post("/api/vending-machines/vm-001/readings", json=reading_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data["readings"]) == 1
        assert data["readings"][0]["temperature"] == 4.5
        assert data["readings"][0]["power_consumption"] == 120.5
        
        # Verify mock was called
        self.mock_service.add_reading.assert_called_once()
    
    @patch('src.services.service_locator.get_service')
    def test_get_readings(self, mock_get_service):
        """Test GET /api/vending-machines/{vm_id}/readings endpoint."""
        # Setup mock
        mock_get_service.return_value = self.mock_service
        reading = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=4.5,
            power_consumption=120.5,
            door_status="CLOSED",
            cash_level=85.50,
            sales_count=12
        )
        self.mock_service.get_readings.return_value = [reading]
        
        # Make request
        response = self.client.get("/api/vending-machines/vm-001/readings")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["temperature"] == 4.5
        assert data[0]["power_consumption"] == 120.5
        
        # Verify mock was called
        self.mock_service.get_readings.assert_called_once_with("vm-001")
