"""
Unit tests for the Water Heater tools for the Agent Framework.
Following TDD principles - these tests define the expected behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config.ai_config import AgentConfig
from src.models.water_heater import WaterHeaterMode
from src.services.water_heater import WaterHeaterService


@pytest.fixture
def mock_water_heater_service():
    """Create a mock water heater service."""
    service = MagicMock(spec=WaterHeaterService)

    # Mock data for get_water_heater
    sample_water_heater = {
        "id": "wh-123456",
        "name": "Master Bath Water Heater",
        "target_temperature": 50.0,
        "current_temperature": 48.5,
        "mode": WaterHeaterMode.ECO,
        "status": "active",
        "energy_usage": 1250.5,
        "model": "Rheem ProTerra Hybrid",
        "last_maintenance_date": "2025-01-15",
    }
    service.get_water_heater.return_value = sample_water_heater

    # Mock data for get_water_heaters
    service.get_water_heaters.return_value = [
        sample_water_heater,
        {
            "id": "wh-789012",
            "name": "Kitchen Water Heater",
            "target_temperature": 45.0,
            "current_temperature": 45.2,
            "mode": WaterHeaterMode.VACATION,
            "status": "active",
            "energy_usage": 0.0,
            "model": "Rheem Performance Platinum Tankless",
            "last_maintenance_date": "2024-11-30",
        },
    ]

    # Mock data for get_readings
    service.get_readings.return_value = [
        {
            "timestamp": "2025-04-01T08:00:00Z",
            "temperature": 48.5,
            "pressure": 2.2,
            "energy_usage": 1250.5,
            "flow_rate": 0.0,
        },
        {
            "timestamp": "2025-04-01T07:00:00Z",
            "temperature": 47.2,
            "pressure": 2.1,
            "energy_usage": 1350.2,
            "flow_rate": 12.5,
        },
    ]

    return service


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return AgentConfig(
        model_name="test-model",
        embedding_model="test-embeddings",
        temperature=0.7,
        max_tokens=500,
        memory_size=10,
    )


def test_get_water_heater_info_tool():
    """Test the get_water_heater_info tool."""
    from src.ai.agent.tools.water_heater_tools import get_water_heater_info

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_water_heater.return_value = {
            "id": "wh-123456",
            "name": "Master Bath Water Heater",
            "target_temperature": 50.0,
            "current_temperature": 48.5,
            "mode": WaterHeaterMode.ECO,
        }
        mock_get_service.return_value = mock_service

        # Test with valid device ID
        result = get_water_heater_info("wh-123456")
        assert "Master Bath Water Heater" in result
        assert "50.0" in result
        assert "48.5" in result
        assert "ECO" in result

        # Test with invalid device ID
        mock_service.get_water_heater.side_effect = Exception("Water heater not found")
        result = get_water_heater_info("invalid-id")
        assert "Error" in result
        assert "not found" in result


def test_get_water_heater_list_tool():
    """Test the get_water_heater_list tool."""
    from src.ai.agent.tools.water_heater_tools import get_water_heater_list

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_water_heaters.return_value = [
            {"id": "wh-123456", "name": "Master Bath Water Heater", "status": "active"},
            {"id": "wh-789012", "name": "Kitchen Water Heater", "status": "idle"},
        ]
        mock_get_service.return_value = mock_service

        # Test listing all water heaters
        result = get_water_heater_list()
        assert "wh-123456" in result
        assert "Master Bath Water Heater" in result
        assert "wh-789012" in result
        assert "Kitchen Water Heater" in result

        # Test with error condition
        mock_service.get_water_heaters.side_effect = Exception("Database error")
        result = get_water_heater_list()
        assert "Error" in result
        assert "Database error" in result


def test_get_water_heater_telemetry_tool():
    """Test the get_water_heater_telemetry tool."""
    from src.ai.agent.tools.water_heater_tools import get_water_heater_telemetry

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_readings.return_value = [
            {
                "timestamp": "2025-04-01T08:00:00Z",
                "temperature": 48.5,
                "energy_usage": 1250.5,
            },
            {
                "timestamp": "2025-04-01T07:00:00Z",
                "temperature": 47.2,
                "energy_usage": 1350.2,
            },
        ]
        mock_get_service.return_value = mock_service

        # Test with valid device ID
        result = get_water_heater_telemetry("wh-123456", hours=2)
        assert "48.5" in result
        assert "47.2" in result
        assert "2025-04-01" in result

        # Test with different hours parameter
        get_water_heater_telemetry("wh-123456", hours=24)
        mock_service.get_readings.assert_called_with("wh-123456", hours=24)

        # Test with error condition
        mock_service.get_readings.side_effect = Exception("No data available")
        result = get_water_heater_telemetry("wh-123456", hours=2)
        assert "Error" in result
        assert "No data available" in result


def test_set_water_heater_temperature_tool():
    """Test the set_water_heater_temperature tool."""
    from src.ai.agent.tools.water_heater_tools import set_water_heater_temperature

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.update_target_temperature.return_value = {
            "id": "wh-123456",
            "name": "Master Bath Water Heater",
            "target_temperature": 52.0,
        }
        mock_get_service.return_value = mock_service

        # Test with valid parameters
        result = set_water_heater_temperature("wh-123456", 52.0)
        assert "successfully updated" in result
        assert "52.0" in result

        # Test with invalid temperature
        mock_service.update_target_temperature.side_effect = Exception(
            "Temperature out of range"
        )
        result = set_water_heater_temperature("wh-123456", 95.0)
        assert "Error" in result
        assert "Temperature out of range" in result


def test_set_water_heater_mode_tool():
    """Test the set_water_heater_mode tool."""
    from src.ai.agent.tools.water_heater_tools import set_water_heater_mode

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.update_mode.return_value = {
            "id": "wh-123456",
            "name": "Master Bath Water Heater",
            "mode": WaterHeaterMode.VACATION,
        }
        mock_get_service.return_value = mock_service

        # Test with valid parameters
        result = set_water_heater_mode("wh-123456", "vacation")
        assert "successfully updated" in result
        assert "VACATION" in result

        # Test with invalid mode
        mock_service.update_mode.side_effect = Exception("Invalid mode")
        result = set_water_heater_mode("wh-123456", "invalid_mode")
        assert "Error" in result
        assert "Invalid mode" in result


def test_get_water_heater_maintenance_info_tool():
    """Test the get_water_heater_maintenance_info tool."""
    from src.ai.agent.tools.water_heater_tools import get_water_heater_maintenance_info

    with patch(
        "src.ai.agent.tools.water_heater_tools.get_water_heater_service"
    ) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_maintenance_info.return_value = {
            "last_maintenance_date": "2025-01-15",
            "next_maintenance_due": "2025-07-15",
            "maintenance_tasks": [
                "Inspect anode rod",
                "Check pressure relief valve",
                "Flush tank",
            ],
            "efficiency_score": 92,
        }
        mock_get_service.return_value = mock_service

        # Test with valid device ID
        result = get_water_heater_maintenance_info("wh-123456")
        assert "2025-01-15" in result
        assert "2025-07-15" in result
        assert "anode rod" in result
        assert "92" in result

        # Test with error condition
        mock_service.get_maintenance_info.side_effect = Exception(
            "Maintenance info not available"
        )
        result = get_water_heater_maintenance_info("wh-123456")
        assert "Error" in result
        assert "not available" in result
