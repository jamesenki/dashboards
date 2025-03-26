import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app
from src.models.water_heater import WaterHeater, WaterHeaterReading, WaterHeaterMode, WaterHeaterStatus
from src.services.water_heater_operations_service import WaterHeaterOperationsService


client = TestClient(app)


@pytest.fixture
def mock_water_heater_operations_service():
    """Fixture to provide a mocked water heater operations service."""
    with patch('src.api.water_heater_operations.WaterHeaterOperationsService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        yield mock_service


def test_get_operations_dashboard(mock_water_heater_operations_service):
    """Test GET /water-heaters/{heater_id}/operations endpoint."""
    # Arrange
    heater_id = "test-heater-123"
    mock_response = {
        "machine_status": "ONLINE",
        "heater_status": "HEATING",
        "current_temperature": 68.0,
        "target_temperature": 70.0,
        "mode": "ECO",
        "gauges": {
            "temperature": {
                "value": 68.0,
                "min": 40.0,
                "max": 85.0,
                "unit": "°C",
                "percentage": 62.2,
                "target": 70.0
            },
            "pressure": {
                "value": 2.6,
                "min": 0.0,
                "max": 5.0,
                "unit": "bar",
                "percentage": 52.0
            },
            "energy_usage": {
                "value": 1350,
                "min": 0,
                "max": 3000,
                "unit": "W",
                "percentage": 45.0
            },
            "flow_rate": {
                "value": 3.5,
                "min": 0.0,
                "max": 10.0,
                "unit": "L/min",
                "percentage": 35.0
            }
        },
        "asset_health": 85.0
    }
    mock_water_heater_operations_service.get_operations_dashboard.return_value = mock_response
    
    # Act
    response = client.get(f"/water-heaters/{heater_id}/operations")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == mock_response
    mock_water_heater_operations_service.get_operations_dashboard.assert_called_once_with(heater_id)


def test_get_operations_dashboard_not_found(mock_water_heater_operations_service):
    """Test GET /water-heaters/{heater_id}/operations when heater is not found."""
    # Arrange
    heater_id = "non-existent-id"
    mock_water_heater_operations_service.get_operations_dashboard.return_value = None
    
    # Act
    response = client.get(f"/water-heaters/{heater_id}/operations")
    
    # Assert
    assert response.status_code == 404
    assert "detail" in response.json()
    mock_water_heater_operations_service.get_operations_dashboard.assert_called_once_with(heater_id)
