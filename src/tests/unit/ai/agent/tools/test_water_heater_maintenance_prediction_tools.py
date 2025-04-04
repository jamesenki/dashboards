"""
Test cases for water heater maintenance prediction tools.
These tools will be integrated into the AI agent system.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.agent.tools.water_heater_tools import execute_service_call


class TestWaterHeaterMaintenancePredictionTools:
    """Test cases for water heater maintenance prediction tools."""

    @pytest.fixture
    def mock_maintenance_service(self):
        """Mock maintenance service for testing."""
        mock_service = AsyncMock()

        # Setup get_water_heater method
        mock_service.get_water_heater.return_value = {
            "id": "rheem-123",
            "name": "Rheem ProTerra Hybrid",
            "manufacturer": "Rheem",
            "model": "ProTerra",
            "heater_type": "HYBRID",
            "current_temperature": 50.0,
            "target_temperature": 52.0,
            "mode": "ENERGY_SAVER",
            "installation_date": datetime(2023, 1, 15).isoformat(),
            "last_maintenance_date": datetime(2024, 2, 10).isoformat(),
        }

        # Setup get_maintenance_prediction method
        mock_service.get_maintenance_prediction.return_value = {
            "days_until_maintenance": 45,
            "confidence": 0.87,
            "component_risks": {
                "heating_element": 0.15,
                "thermostat": 0.08,
                "anode_rod": 0.42,
                "pressure_valve": 0.12,
                "compressor": 0.22,
            },
            "next_maintenance_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "recommended_actions": [
                "Inspect and possibly replace anode rod",
                "Check compressor operation",
                "Flush tank to remove sediment",
            ],
        }

        # Setup get_efficiency_analysis method
        mock_service.get_efficiency_analysis.return_value = {
            "current_efficiency": 0.92,
            "estimated_annual_cost": 320.50,
            "potential_savings": 45.75,
            "recommendations": [
                "Lower temperature by 2°C to save 7% energy",
                "Switch to Heat Pump mode during off-peak hours",
                "Consider upgrading insulation around pipes",
            ],
        }

        return mock_service

    @patch("src.ai.agent.tools.water_heater_tools.get_service")
    def test_get_water_heater_maintenance_prediction_tool(
        self, mock_get_service, mock_maintenance_service
    ):
        """Test the get_water_heater_maintenance_prediction function."""
        # Import here to avoid circular import in the actual implementation
        from src.ai.agent.tools.water_heater_tools import (
            get_water_heater_maintenance_prediction,
        )

        # Setup mock
        mock_get_service.return_value = mock_maintenance_service

        # Execute tool
        result = get_water_heater_maintenance_prediction("rheem-123")

        # Verify the result
        assert isinstance(result, str)
        assert "days until maintenance: 45" in result.lower()
        assert "confidence: 87%" in result.lower()
        assert "anode rod" in result.lower()
        assert "recommended actions" in result.lower()

        # Verify service was called correctly
        mock_maintenance_service.get_maintenance_prediction.assert_called_once_with(
            "rheem-123"
        )

    @patch("src.ai.agent.tools.water_heater_tools.get_service")
    def test_get_water_heater_efficiency_analysis_tool(
        self, mock_get_service, mock_maintenance_service
    ):
        """Test the get_water_heater_efficiency_analysis function."""
        # Import here to avoid circular import in the actual implementation
        from src.ai.agent.tools.water_heater_tools import (
            get_water_heater_efficiency_analysis,
        )

        # Setup mock
        mock_get_service.return_value = mock_maintenance_service

        # Execute tool
        result = get_water_heater_efficiency_analysis("rheem-123")

        # Verify the result
        assert isinstance(result, str)
        assert "current efficiency: 92%" in result.lower()
        assert "estimated annual cost: $320.50" in result.lower()
        assert "potential savings: $45.75" in result.lower()
        assert "recommendations" in result.lower()
        assert "lower temperature" in result.lower()

        # Verify service was called correctly
        mock_maintenance_service.get_efficiency_analysis.assert_called_once_with(
            "rheem-123"
        )

    @patch("src.ai.agent.tools.water_heater_tools.get_service")
    def test_analyze_water_heater_telemetry_tool(
        self, mock_get_service, mock_maintenance_service
    ):
        """Test the analyze_water_heater_telemetry function."""
        # Import here to avoid circular import in the actual implementation
        from src.ai.agent.tools.water_heater_tools import analyze_water_heater_telemetry

        # Setup telemetry analysis mock
        mock_maintenance_service.analyze_telemetry.return_value = {
            "telemetry_health": "good",
            "anomalies_detected": [
                {
                    "parameter": "temperature_fluctuation",
                    "severity": "low",
                    "description": "Minor temperature fluctuations detected during morning hours",
                    "recommended_action": "Monitor for one week, no immediate action required",
                }
            ],
            "patterns": [
                "Higher usage pattern on weekends",
                "Temperature drops during night hours (11pm-5am)",
            ],
            "estimated_daily_usage": 42.5,  # gallons
            "peak_usage_time": "7:30am - 8:30am",
        }

        # Setup mock
        mock_get_service.return_value = mock_maintenance_service

        # Execute tool
        result = analyze_water_heater_telemetry("rheem-123", hours=48)

        # Verify the result
        assert isinstance(result, str)
        assert "telemetry health: good" in result.lower()
        assert "anomalies detected" in result.lower()
        assert "temperature fluctuation" in result.lower()
        assert "patterns" in result.lower()
        assert "higher usage pattern on weekends" in result.lower()
        assert "estimated daily usage: 42.5 gallons" in result.lower()
        assert "peak usage time: 7:30am - 8:30am" in result.lower()

        # Verify service was called correctly
        mock_maintenance_service.analyze_telemetry.assert_called_once_with(
            "rheem-123", hours=48
        )
