"""
Tests for the water heater history API endpoints
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.water_heater_history import WaterHeaterHistoryService

client = TestClient(app)

# Get the API router paths from the actual implementation
API_BASE_PATH = "/api/water-heaters"


class TestWaterHeaterHistoryAPI:
    """Test cases for water heater history API endpoints"""

    @patch("src.services.water_heater.WaterHeaterService.get_water_heater")
    @patch(
        "src.services.water_heater_history.WaterHeaterHistoryService.get_history_dashboard"
    )
    def test_get_history_dashboard(
        self, mock_get_history_dashboard, mock_get_water_heater
    ):
        """Test retrieving complete history dashboard data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7

        # Mock the water heater service to return a valid heater
        mock_get_water_heater.return_value = MagicMock(id=heater_id)

        mock_result = {
            "temperature": {
                "labels": ["Day 1", "Day 2"],
                "datasets": [{"label": "Temperature", "data": [65, 68]}],
            },
            "energy_usage": {
                "labels": ["Day 1", "Day 2"],
                "datasets": [{"label": "Energy Usage", "data": [1200, 1300]}],
            },
            "pressure_flow": {
                "labels": ["Day 1", "Day 2"],
                "datasets": [
                    {"label": "Pressure", "data": [2.5, 2.7]},
                    {"label": "Flow Rate", "data": [3.2, 3.4]},
                ],
            },
        }

        mock_get_history_dashboard.return_value = mock_result

        # Act
        response = client.get(f"/api/water-heaters/{heater_id}/history?days={days}")

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_result

        # Verify service method was called with correct arguments
        mock_get_history_dashboard.assert_called_once_with(heater_id, days)

    @patch("src.services.water_heater.WaterHeaterService.get_water_heater")
    @patch(
        "src.services.water_heater_history.WaterHeaterHistoryService.get_temperature_history"
    )
    def test_get_temperature_history(
        self, mock_get_temperature_history, mock_get_water_heater
    ):
        """Test retrieving temperature history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7

        # Mock the water heater service to return a valid heater
        mock_get_water_heater.return_value = MagicMock(id=heater_id)

        mock_result = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [{"label": "Temperature", "data": [65, 68]}],
        }

        mock_get_temperature_history.return_value = mock_result

        # Act
        response = client.get(
            f"/api/water-heaters/{heater_id}/history/temperature?days={days}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_result

        # Verify service method was called with correct arguments
        mock_get_temperature_history.assert_called_once_with(heater_id, days)

    @patch("src.services.water_heater.WaterHeaterService.get_water_heater")
    @patch(
        "src.services.water_heater_history.WaterHeaterHistoryService.get_energy_usage_history"
    )
    def test_get_energy_usage_history(
        self, mock_get_energy_usage_history, mock_get_water_heater
    ):
        """Test retrieving energy usage history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7

        # Mock the water heater service to return a valid heater
        mock_get_water_heater.return_value = MagicMock(id=heater_id)

        mock_result = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [{"label": "Energy Usage", "data": [1200, 1300]}],
        }

        mock_get_energy_usage_history.return_value = mock_result

        # Act
        response = client.get(
            f"/api/water-heaters/{heater_id}/history/energy?days={days}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_result

        # Verify service method was called with correct arguments
        mock_get_energy_usage_history.assert_called_once_with(heater_id, days)

    @patch("src.services.water_heater.WaterHeaterService.get_water_heater")
    @patch(
        "src.services.water_heater_history.WaterHeaterHistoryService.get_pressure_flow_history"
    )
    def test_get_pressure_flow_history(
        self, mock_get_pressure_flow_history, mock_get_water_heater
    ):
        """Test retrieving pressure and flow rate history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7

        # Mock the water heater service to return a valid heater
        mock_get_water_heater.return_value = MagicMock(id=heater_id)

        mock_result = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [
                {"label": "Pressure", "data": [2.5, 2.7]},
                {"label": "Flow Rate", "data": [3.2, 3.4]},
            ],
        }

        mock_get_pressure_flow_history.return_value = mock_result

        # Act
        response = client.get(
            f"/api/water-heaters/{heater_id}/history/pressure-flow?days={days}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_result

        # Verify service method was called with correct arguments
        mock_get_pressure_flow_history.assert_called_once_with(heater_id, days)

    @patch("src.services.water_heater.WaterHeaterService.get_water_heater")
    def test_handle_not_found(self, mock_get_water_heater):
        """Test handling of not found errors."""
        # Arrange
        heater_id = "nonexistent-heater"
        days = 7

        # Simulate a water heater not found error
        mock_get_water_heater.side_effect = Exception("Water heater not found")

        # Act
        response = client.get(f"/api/water-heaters/{heater_id}/history?days={days}")

        # Assert
        assert response.status_code == 404
        # Adjust assertion to match actual error format
        detail = response.json().get("detail", "")
        assert "not found" in detail.lower()
