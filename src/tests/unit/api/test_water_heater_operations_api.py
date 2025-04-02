from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.services.water_heater_operations_service import WaterHeaterOperationsService


@pytest.fixture
def test_client():
    """Fixture to provide a test client."""
    return TestClient(app)


@pytest.fixture
def mock_water_heater_operations_service():
    """Fixture to provide a mocked water heater operations service."""
    with patch(
        "src.api.water_heater_operations.WaterHeaterOperationsService"
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        yield mock_service


def test_get_operations_dashboard(test_client, mock_water_heater_operations_service):
    """Test getting operations dashboard."""
    # Set up mock
    mock_water_heater_operations_service.get_operations_dashboard.return_value = {
        "asset_id": "test-heater-123",
        "status": "Online",
        "temperature": 45.5,
        "target_temperature": 50.0,
        "efficiency": 0.85,
        "energy_usage": [
            {"timestamp": "2025-03-15T00:00:00Z", "value": 120},
            {"timestamp": "2025-03-16T00:00:00Z", "value": 118},
            {"timestamp": "2025-03-17T00:00:00Z", "value": 125},
        ],
        "uptime_percentage": 98.5,
        "last_maintenance_date": "2025-01-15T10:30:00Z",
        "next_maintenance_date": "2025-07-15T10:30:00Z",
    }

    # Make request
    heater_id = "test-heater-123"
    response = test_client.get(f"/api/water-heaters/{heater_id}/operations")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == heater_id
    assert "temperature" in data
    assert "energy_usage" in data
    assert len(data["energy_usage"]) == 3

    # Verify service was called
    mock_water_heater_operations_service.get_operations_dashboard.assert_called_once_with(
        heater_id
    )


def test_get_operations_dashboard_not_found(
    test_client, mock_water_heater_operations_service
):
    """Test getting operations dashboard for non-existent water heater."""
    # Set up mock to simulate not found
    heater_id = "nonexistent-id"
    mock_water_heater_operations_service.get_operations_dashboard.side_effect = (
        Exception(f"Water heater {heater_id} not found")
    )

    # Make request
    response = test_client.get(f"/api/water-heaters/{heater_id}/operations")

    # Verify response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    # Verify service was called
    mock_water_heater_operations_service.get_operations_dashboard.assert_called_once_with(
        heater_id
    )
