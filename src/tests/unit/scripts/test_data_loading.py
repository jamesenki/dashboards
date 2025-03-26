"""
Tests for the data loading script to ensure proper data transformation and loading.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.db.models import DeviceModel, ReadingModel
from src.scripts.load_data_to_postgres import load_devices
from src.utils.dummy_data import dummy_data


@pytest.fixture
def mock_session():
    """Mock database session for testing."""
    mock = AsyncMock()
    mock.flush = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mock_db_session(mock_session):
    """Mock the database session generator."""
    async def _get_db_session():
        yield mock_session
    
    return _get_db_session


@pytest.mark.asyncio
async def test_load_vending_machines(mock_db_session):
    """Test loading vending machines into PostgreSQL."""
    # Create a test vending machine in dummy data
    dummy_data.vending_machines = {
        "test-vm-1": MagicMock(
            id="test-vm-1",
            name="Test Vending Machine",
            type="vending_machine",
            status="ONLINE",
            location="Test Location",
            last_seen="2025-03-26T14:44:41.320374",
            model_number="Test-123",
            readings=[
                {
                    "timestamp": "2025-03-25T14:44:41.320303",
                    "temperature": 3.5,
                    "power_consumption": 344.8,
                    "door_status": "CLOSED",
                    "cash_level": 122.41,
                    "sales_count": 3
                }
            ],
            products=[{"product_id": "prod-1", "name": "Test Product", "quantity": 10}],
            __dict__={"id": "test-vm-1", "name": "Test Vending Machine"}
        )
    }
    
    # Mock the jsonable_encoder function
    with patch('src.scripts.load_data_to_postgres.jsonable_encoder') as mock_encoder, \
         patch('src.scripts.load_data_to_postgres.get_db_session', return_value=mock_db_session()):
        
        # Mock encoder return value
        mock_encoder.return_value = {
            "id": "test-vm-1",
            "name": "Test Vending Machine",
            "type": "vending_machine",
            "status": "ONLINE",
            "location": "Test Location",
            "last_seen": "2025-03-26T14:44:41.320374",
            "model_number": "Test-123",
            "readings": [
                {
                    "timestamp": "2025-03-25T14:44:41.320303",
                    "temperature": 3.5,
                    "power_consumption": 344.8,
                    "door_status": "CLOSED",
                    "cash_level": 122.41,
                    "sales_count": 3
                }
            ],
            "products": [{"product_id": "prod-1", "name": "Test Product", "quantity": 10}]
        }
        
        # Run the function
        await load_devices()
        
        # Get the session from generator
        session = next(asyncio.run(mock_db_session().__anext__()))
        
        # Assert that correct models were added to the session
        # 1. DeviceModel for vending machine should be added
        assert session.add.call_count >= 1
        
        # Get the first call arg (should be DeviceModel)
        device_calls = [call[0][0] for call in session.add.call_args_list 
                      if isinstance(call[0][0], DeviceModel)]
        assert len(device_calls) == 1
        device = device_calls[0]
        
        # Verify device properties
        assert device.id == "test-vm-1"
        assert device.name == "Test Vending Machine"
        assert device.type == "vending_machine"
        assert device.status == "ONLINE"
        assert "products" in device.properties
        
        # Verify readings were added (5 metrics from one reading)
        reading_calls = [call[0][0] for call in session.add.call_args_list 
                       if isinstance(call[0][0], ReadingModel)]
        assert len(reading_calls) >= 5
        
        # Check at least one temperature reading exists
        temp_readings = [r for r in reading_calls if r.metric_name == "temperature"]
        assert len(temp_readings) >= 1
        assert temp_readings[0].value == 3.5
        
        # Verify session was committed
        session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_load_water_heaters(mock_db_session):
    """Test loading water heaters into PostgreSQL."""
    # Create a test water heater in dummy data
    dummy_data.water_heaters = {
        "test-wh-1": MagicMock(
            id="test-wh-1",
            name="Test Water Heater",
            type="water_heater",
            status="ONLINE",
            location="Test Location",
            last_seen="2025-03-26T14:44:41.320374",
            model_number="WH-123",
            temperature=50.5,
            readings=[
                {
                    "timestamp": "2025-03-25T14:44:41.320303",
                    "temperature": 50.5,
                    "pressure": 2.1,
                    "flow_rate": 5.0,
                    "power_consumption": 1500.0
                }
            ],
            __dict__={"id": "test-wh-1", "name": "Test Water Heater"}
        )
    }
    
    # Mock the jsonable_encoder function
    with patch('src.scripts.load_data_to_postgres.jsonable_encoder') as mock_encoder, \
         patch('src.scripts.load_data_to_postgres.get_db_session', return_value=mock_db_session()):
        
        # Mock encoder return value
        mock_encoder.return_value = {
            "id": "test-wh-1",
            "name": "Test Water Heater",
            "type": "water_heater",
            "status": "ONLINE",
            "location": "Test Location",
            "last_seen": "2025-03-26T14:44:41.320374",
            "model_number": "WH-123",
            "temperature": 50.5,
            "readings": [
                {
                    "timestamp": "2025-03-25T14:44:41.320303",
                    "temperature": 50.5,
                    "pressure": 2.1,
                    "flow_rate": 5.0,
                    "power_consumption": 1500.0
                }
            ]
        }
        
        # Run the function
        await load_devices()
        
        # Get the session from generator
        session = next(asyncio.run(mock_db_session().__anext__()))
        
        # Assert that correct models were added to the session
        # 1. DeviceModel for water heater should be added
        assert session.add.call_count >= 1
        
        # Get the calls for DeviceModel
        device_calls = [call[0][0] for call in session.add.call_args_list 
                      if isinstance(call[0][0], DeviceModel)]
        assert len(device_calls) == 1
        device = device_calls[0]
        
        # Verify device properties
        assert device.id == "test-wh-1"
        assert device.name == "Test Water Heater"
        assert device.type == "water_heater"
        assert device.status == "ONLINE"
        assert device.properties.get("temperature") == 50.5
        
        # Verify readings were added (4 metrics from one reading)
        reading_calls = [call[0][0] for call in session.add.call_args_list 
                       if isinstance(call[0][0], ReadingModel)]
        assert len(reading_calls) >= 4
        
        # Check at least one temperature reading exists
        temp_readings = [r for r in reading_calls if r.metric_name == "temperature"]
        assert len(temp_readings) >= 1
        assert temp_readings[0].value == 50.5
        
        # Verify session was committed
        session.commit.assert_called_once()
