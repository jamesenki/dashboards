"""
Tests for the VendingMachineOperationsServiceDB class which retrieves operations data from the database.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.db.adapters.operations_cache import OperationsDashboardCache
from src.db.repository import DeviceRepository
from src.models.device import DeviceStatus, DeviceType
from src.models.device_reading import DeviceReading
from src.models.vending_machine import VendingMachine, VendingMachineReading, VendingMachineStatus, VendingMachineMode, SubLocation, LocationType, UseType, ProductItem
from src.services.vending_machine_operations_service_db import VendingMachineOperationsServiceDB


@pytest.fixture
def mock_repo():
    """Mock repository for testing."""
    mock = AsyncMock(spec=DeviceRepository)
    mock.get_device = AsyncMock()
    mock.get_device_readings = AsyncMock()
    return mock


@pytest.fixture
def mock_cache():
    """Mock operations cache for testing."""
    mock = AsyncMock(spec=OperationsDashboardCache)
    mock.get_vending_machine_operations = AsyncMock(return_value=None)
    mock.cache_vending_machine_operations = AsyncMock(return_value=True)
    mock.get_ice_cream_machine_operations = AsyncMock(return_value=None)
    mock.cache_ice_cream_machine_operations = AsyncMock(return_value=True)
    mock.invalidate_operations_cache = AsyncMock()
    mock.publish_operations_update = AsyncMock()
    return mock


@pytest.fixture
def sample_vm():
    """Sample vending machine for testing."""
    from src.models.device import DeviceType
    from src.models.vending_machine import (
        VendingMachineStatus,
        VendingMachineMode,
        ProductItem,
        SubLocation,
        LocationType,
        UseType
    )

    return VendingMachine(
        id="test-vm-1",
        name="Test Vending Machine",
        type=DeviceType.VENDING_MACHINE,
        status=DeviceStatus.ONLINE,
        location="Test Location",
        last_seen=datetime.utcnow(),
        model_number="Test-123",
        machine_status=VendingMachineStatus.OPERATIONAL,
        mode=VendingMachineMode.NORMAL,
        temperature=3.5,
        total_capacity=50,
        cash_capacity=1000.0,
        current_cash=500.0,
        sub_location=SubLocation.LOBBY,
        location_type=LocationType.RETAIL,
        location_business_name="Test Business",
        use_type=UseType.PUBLIC,
        maintenance_partner="Test Maintenance",
        last_maintenance_date="2024-11-15T10:30:00",
        next_maintenance_date="2025-05-15T10:30:00",
        products=[
            ProductItem(
                product_id="prod-1", 
                name="Test Product", 
                price=1.5, 
                quantity=10, 
                category="Snacks", 
                location="A1"
            )
        ],
        readings=[
            VendingMachineReading(
                timestamp=datetime.utcnow() - timedelta(hours=1),
                temperature=3.5,
                power_consumption=100.0,
                door_status="CLOSED",
                cash_level=450.0,
                sales_count=5
            ),
            VendingMachineReading(
                timestamp=datetime.utcnow(),
                temperature=3.7,
                power_consumption=110.0,
                door_status="OPEN",
                cash_level=500.0,
                sales_count=6
            )
        ]
    )


@pytest.mark.asyncio
async def test_get_operations_from_cache(mock_repo, mock_cache, sample_vm):
    """Test retrieving operations data from cache."""
    # Setup cached response
    cached_ops = {
        "machine_id": "test-vm-1",
        "machine_status": "OPERATIONAL",
        "last_updated": datetime.utcnow().isoformat(),
        "temperature": 3.7,
        "door_status": "OPEN",
        "inventory": [{"name": "Test Product", "level": 10, "max": 20}]
    }
    mock_cache.get_vending_machine_operations.return_value = cached_ops
    
    # Create service instance
    service = VendingMachineOperationsServiceDB(mock_repo, mock_cache)
    
    # Call the method
    result = await service.get_vm_operations("test-vm-1")
    
    # Verify cache was checked
    mock_cache.get_vending_machine_operations.assert_called_once_with("test-vm-1")
    
    # Verify db was not called
    mock_repo.get_device.assert_not_called()
    
    # Verify result matches cache
    assert result == cached_ops


@pytest.mark.asyncio
async def test_get_operations_from_db(mock_repo, mock_cache, sample_vm):
    """Test retrieving operations data from database when cache misses."""
    # Setup cache miss
    mock_cache.get_vending_machine_operations.return_value = None
    
    # Setup DB response
    mock_repo.get_device.return_value = sample_vm
    
    # Create service instance
    service = VendingMachineOperationsServiceDB(mock_repo, mock_cache)
    
    # Call the method
    result = await service.get_vm_operations("test-vm-1")
    
    # Verify cache was checked
    mock_cache.get_vending_machine_operations.assert_called_once_with("test-vm-1")
    
    # Verify DB was called
    mock_repo.get_device.assert_called_once_with("test-vm-1")
    
    # Verify cache was updated
    mock_cache.cache_vending_machine_operations.assert_called_once()
    
    # Verify result contains expected fields
    assert result["machine_id"] == "test-vm-1"
    assert result["machine_status"] == "OPERATIONAL"
    assert "last_updated" in result
    assert result["temperature"] == 3.7  # latest reading
    assert result["door_status"] == "OPEN"  # latest reading


@pytest.mark.asyncio
async def test_get_ice_cream_operations_from_cache(mock_repo, mock_cache, sample_vm):
    """Test retrieving ice cream operations data from cache."""
    # Setup cached response for ice cream machine
    cached_ops = {
        "machine_id": "test-vm-1",
        "machine_status": "Online",
        "last_updated": datetime.utcnow().isoformat(),
        "freezer_temperature": -14.1,
        "cap_position": {"status": "OK"},
        "ram_position": {"status": "OK"},
        "cycle_status": {"status": "OK"},
        "pod_code": "12345",
        "ice_cream_inventory": [{"name": "Vanilla", "current_level": 5, "max_level": 10}]
    }
    mock_cache.get_ice_cream_machine_operations.return_value = cached_ops
    
    # Create service instance
    service = VendingMachineOperationsServiceDB(mock_repo, mock_cache)
    
    # Call the method
    result = await service.get_ice_cream_operations("test-vm-1")
    
    # Verify cache was checked
    mock_cache.get_ice_cream_machine_operations.assert_called_once_with("test-vm-1")
    
    # Verify db was not called
    mock_repo.get_device.assert_not_called()
    
    # Verify result matches cache
    assert result == cached_ops


@pytest.mark.asyncio
async def test_operations_update_invalidates_cache(mock_repo, mock_cache, sample_vm):
    """Test that operations data update invalidates the cache."""
    # Setup
    service = VendingMachineOperationsServiceDB(mock_repo, mock_cache)
    
    # Call update method
    update_data = {"temperature": 4.0, "door_status": "CLOSED"}
    await service.update_vm_operations("test-vm-1", update_data)
    
    # Verify cache was invalidated
    mock_cache.invalidate_operations_cache.assert_called_once_with("test-vm-1", "vending_machine")
    
    # Verify update notification was published
    mock_cache.publish_operations_update.assert_called_once_with("test-vm-1", "vending_machine")
