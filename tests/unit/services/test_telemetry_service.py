"""
Unit tests for the Telemetry Service
"""
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.telemetry import TelemetryData, TelemetryMetadata
from src.services.telemetry_service import TelemetryService


@pytest.fixture
def telemetry_service():
    """Create a TelemetryService instance for testing"""
    return TelemetryService()


@pytest.mark.asyncio
async def test_telemetry_service_initialization(telemetry_service):
    """Test that TelemetryService initializes correctly"""
    assert telemetry_service is not None
    assert hasattr(telemetry_service, "process_telemetry_data")
    assert hasattr(telemetry_service, "get_recent_telemetry")
    assert hasattr(telemetry_service, "get_historical_telemetry")


@pytest.mark.asyncio
async def test_process_telemetry_data(telemetry_service):
    """Test processing telemetry data"""
    # Mock the database service used by telemetry service
    with patch("src.services.telemetry_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Test data
        telemetry_data = {
            "device_id": "test-device-001",
            "metric": "temperature",
            "value": 55.5,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"unit": "celsius", "sensor_id": "temp-sensor-1"},
        }

        # Process the telemetry data
        result = await telemetry_service.process_telemetry_data(telemetry_data)

        # Verify the result
        assert result is not None
        assert result["device_id"] == "test-device-001"
        assert result["metric"] == "temperature"
        assert result["value"] == 55.5

        # Verify DB was called
        mock_db.store_telemetry.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_telemetry(telemetry_service):
    """Test retrieving recent telemetry data"""
    # Mock the database service
    with patch("src.services.telemetry_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()

        # Setup the mock to return test data
        test_data = [
            {
                "device_id": "test-device-001",
                "metric": "temperature",
                "value": 55.5,
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "metadata": {"unit": "celsius", "sensor_id": "temp-sensor-1"},
            },
            {
                "device_id": "test-device-001",
                "metric": "temperature",
                "value": 56.0,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"unit": "celsius", "sensor_id": "temp-sensor-1"},
            },
        ]
        mock_db.get_recent_telemetry.return_value = test_data
        mock_get_db.return_value = mock_db

        # Get recent telemetry
        result = await telemetry_service.get_recent_telemetry(
            device_id="test-device-001", metric="temperature", limit=10
        )

        # Verify the result
        assert len(result) == 2
        assert result[0]["value"] == 55.5
        assert result[1]["value"] == 56.0

        # Verify DB was called with correct parameters
        mock_db.get_recent_telemetry.assert_called_once_with(
            device_id="test-device-001", metric="temperature", limit=10
        )


@pytest.mark.asyncio
async def test_get_historical_telemetry(telemetry_service):
    """Test retrieving historical telemetry data with time range"""
    # Mock the database service
    with patch("src.services.telemetry_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()

        # Setup the mock
        test_data = [
            {
                "device_id": "test-device-001",
                "metric": "temperature",
                "value": 54.5,
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "metadata": {"unit": "celsius"},
            },
            {
                "device_id": "test-device-001",
                "metric": "temperature",
                "value": 55.0,
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "metadata": {"unit": "celsius"},
            },
        ]
        mock_db.get_telemetry_in_range.return_value = test_data
        mock_get_db.return_value = mock_db

        # Time range for query
        start_time = datetime.utcnow() - timedelta(hours=3)
        end_time = datetime.utcnow()

        # Get historical telemetry
        result = await telemetry_service.get_historical_telemetry(
            device_id="test-device-001",
            metric="temperature",
            start_time=start_time,
            end_time=end_time,
        )

        # Verify the result
        assert len(result) == 2
        assert result[0]["value"] == 54.5
        assert result[1]["value"] == 55.0

        # Verify DB was called with correct parameters
        mock_db.get_telemetry_in_range.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_telemetry(telemetry_service):
    """Test broadcasting telemetry updates to WebSocket clients"""
    # Mock the WebSocket manager
    with patch(
        "src.services.telemetry_service.get_websocket_manager"
    ) as mock_get_manager:
        mock_manager = AsyncMock()
        mock_get_manager.return_value = mock_manager

        # Test data
        telemetry_data = {
            "device_id": "test-device-001",
            "metric": "temperature",
            "value": 57.5,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast the telemetry data
        await telemetry_service.broadcast_telemetry(telemetry_data)

        # Verify broadcast was called
        mock_manager.broadcast_to_device.assert_called_once_with(
            device_id="test-device-001",
            message_type="telemetry",
            message=telemetry_data,
        )


@pytest.mark.asyncio
async def test_telemetry_aggregation(telemetry_service):
    """Test telemetry data aggregation for analysis"""
    # Mock the database service
    with patch("src.services.telemetry_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()

        # Setup the mock to return aggregated data
        aggregated_data = [
            {"hour": 0, "avg_value": 54.2},
            {"hour": 1, "avg_value": 54.5},
            {"hour": 2, "avg_value": 55.0},
            {"hour": 3, "avg_value": 55.5},
        ]
        mock_db.get_aggregated_telemetry.return_value = aggregated_data
        mock_get_db.return_value = mock_db

        # Get aggregated telemetry
        result = await telemetry_service.get_aggregated_telemetry(
            device_id="test-device-001",
            metric="temperature",
            aggregation="hourly",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
        )

        # Verify the result
        assert len(result) == 4
        assert result[0]["avg_value"] == 54.2
        assert result[3]["avg_value"] == 55.5

        # Verify DB was called
        mock_db.get_aggregated_telemetry.assert_called_once()


@pytest.mark.asyncio
async def test_telemetry_data_model_validation():
    """Test that telemetry data model validation works correctly"""
    # Valid telemetry data
    valid_data = TelemetryData(
        device_id="test-device-001",
        metric="temperature",
        value=55.5,
        timestamp=datetime.utcnow(),
        metadata=TelemetryMetadata(unit="celsius"),
    )

    assert valid_data.device_id == "test-device-001"
    assert valid_data.metric == "temperature"
    assert valid_data.value == 55.5
    assert valid_data.metadata.unit == "celsius"

    # Test conversion to dict
    data_dict = valid_data.dict()
    assert "device_id" in data_dict
    assert "metric" in data_dict
    assert "value" in data_dict
    assert "timestamp" in data_dict
    assert "metadata" in data_dict
