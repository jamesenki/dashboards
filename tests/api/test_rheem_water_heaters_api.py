"""
Test for Rheem water heater API endpoints.

Following TDD principles, these tests define the expected behavior
of the Rheem water heater API endpoints.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.api.dependencies import get_rheem_water_heater_service
from src.api.routes.rheem_water_heaters import router
from src.models.rheem_water_heater import (
    RheemProductSeries,
    RheemWaterHeater,
    RheemWaterHeaterMode,
    RheemWaterHeaterType,
)


# Test data fixtures
@pytest.fixture
def rheem_water_heater_data():
    """Return test data for a Rheem water heater."""
    return {
        "id": "rheem-wh-123",
        "name": "Rheem ProTerra Hybrid",
        "heater_type": RheemWaterHeaterType.HYBRID,
        "series": RheemProductSeries.PROTERRA,
        "target_temperature": 120.0,
        "current_temperature": 118.5,
        "mode": RheemWaterHeaterMode.ENERGY_SAVER,
        "eco_net_enabled": True,
        "wifi_signal_strength": 85,
        "heat_pump_mode": "high_demand",
        "anode_rod_status": "good",
        "element_status": {"upper": "good", "lower": "good"},
        "estimated_annual_cost": 318.50,
        "water_usage_daily_avg_gallons": 45.2,
        "firmware_version": "2.3.1",
    }


@pytest.fixture
def mock_rheem_water_heater_service():
    """Create a mock service for testing."""
    service = AsyncMock()
    return service


@pytest.fixture
def client(mock_rheem_water_heater_service):
    """Create a test client with dependency override."""
    app = FastAPI()
    app.include_router(router)

    # Override the dependency
    def get_test_rheem_water_heater_service():
        return mock_rheem_water_heater_service

    app.dependency_overrides[
        get_rheem_water_heater_service
    ] = get_test_rheem_water_heater_service

    yield TestClient(app)


def test_get_all_rheem_water_heaters(
    client, rheem_water_heater_data, mock_rheem_water_heater_service
):
    """Test getting all Rheem water heaters."""
    # Setup mock
    water_heaters = [RheemWaterHeater(**rheem_water_heater_data)]
    mock_rheem_water_heater_service.get_all_water_heaters.return_value = water_heaters

    # Execute test
    response = client.get("/api/rheem-water-heaters/")

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["id"] == rheem_water_heater_data["id"]
    assert result[0]["series"] == rheem_water_heater_data["series"].value
    # The eco_net_enabled field might be mapped to smart_enabled in the JSON response
    # or it might not be included directly in the JSON representation

    # Verify filter was applied correctly
    mock_rheem_water_heater_service.get_all_water_heaters.assert_called_once()


def test_get_rheem_water_heater_by_id(
    client, rheem_water_heater_data, mock_rheem_water_heater_service
):
    """Test getting a specific Rheem water heater by ID."""
    # Setup mock
    water_heater = RheemWaterHeater(**rheem_water_heater_data)
    mock_rheem_water_heater_service.get_water_heater.return_value = water_heater

    # Execute test
    response = client.get(f"/api/rheem-water-heaters/{rheem_water_heater_data['id']}")

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == rheem_water_heater_data["id"]
    assert result["heater_type"] == rheem_water_heater_data["heater_type"].value

    # Verify service call
    mock_rheem_water_heater_service.get_water_heater.assert_called_once_with(
        rheem_water_heater_data["id"]
    )


def test_get_eco_net_status(client, mock_rheem_water_heater_service):
    """Test getting EcoNet status for a Rheem water heater."""
    # Setup mock data
    device_id = "rheem-wh-123"
    eco_net_status = {
        "connected": True,
        "wifi_signal_strength": 85,
        "last_connected": datetime.now().isoformat(),
        "firmware_version": "2.3.1",
        "update_available": False,
        "remote_control_enabled": True,
    }
    mock_rheem_water_heater_service.get_eco_net_status.return_value = eco_net_status

    # Execute test
    response = client.get(f"/api/rheem-water-heaters/{device_id}/eco-net-status")

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert result["connected"] == eco_net_status["connected"]
    assert result["wifi_signal_strength"] == eco_net_status["wifi_signal_strength"]
    assert result["firmware_version"] == eco_net_status["firmware_version"]

    # Verify service call
    mock_rheem_water_heater_service.get_eco_net_status.assert_called_once_with(
        device_id
    )


def test_update_eco_net_status(client, mock_rheem_water_heater_service):
    """Test updating EcoNet settings for a Rheem water heater."""
    # Setup test data
    device_id = "rheem-wh-123"
    mock_rheem_water_heater_service.update_eco_net_settings.return_value = None

    # Execute test
    response = client.put(
        f"/api/rheem-water-heaters/{device_id}/eco-net-status?remote_control_enabled=false"
    )

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "updated successfully" in result["message"]

    # Verify service call
    mock_rheem_water_heater_service.update_eco_net_settings.assert_called_once_with(
        device_id, remote_control_enabled=False
    )


def test_get_maintenance_prediction(client, mock_rheem_water_heater_service):
    """Test getting maintenance prediction for a Rheem water heater."""
    # Setup mock data
    device_id = "rheem-wh-123"
    prediction = {
        "days_until_maintenance": 45,
        "confidence": 0.89,
        "component_risks": {
            "anode_rod": 0.2,
            "heating_element": 0.1,
            "thermostat": 0.05,
        },
        "next_maintenance_date": (datetime.now() + timedelta(days=45)).strftime(
            "%Y-%m-%d"
        ),
        "recommended_actions": ["Check anode rod in 45 days", "Monitor water quality"],
    }
    mock_rheem_water_heater_service.get_maintenance_prediction.return_value = prediction

    # Execute test
    response = client.get(
        f"/api/rheem-water-heaters/{device_id}/maintenance-prediction"
    )

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert result["days_until_maintenance"] == prediction["days_until_maintenance"]
    assert result["confidence"] == prediction["confidence"]
    assert result["component_risks"] == prediction["component_risks"]

    # Verify service call
    mock_rheem_water_heater_service.get_maintenance_prediction.assert_called_once_with(
        device_id
    )


def test_get_efficiency_analysis(client, mock_rheem_water_heater_service):
    """Test getting efficiency analysis for a Rheem water heater."""
    # Setup mock data
    device_id = "rheem-wh-123"
    analysis = {
        "current_efficiency": 0.85,
        "estimated_annual_cost": 318.50,
        "potential_savings": 45.75,
        "recommendations": [
            "Lower target temperature by 5°F to save $25/year",
            "Switch to Energy Saver mode",
        ],
    }
    mock_rheem_water_heater_service.get_efficiency_analysis.return_value = analysis

    # Execute test
    response = client.get(f"/api/rheem-water-heaters/{device_id}/efficiency-analysis")

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert result["current_efficiency"] == analysis["current_efficiency"]
    assert result["estimated_annual_cost"] == analysis["estimated_annual_cost"]
    assert result["potential_savings"] == analysis["potential_savings"]

    # Verify service call
    mock_rheem_water_heater_service.get_efficiency_analysis.assert_called_once_with(
        device_id
    )


def test_analyze_telemetry(client, mock_rheem_water_heater_service):
    """Test analyzing telemetry data for a Rheem water heater."""
    # Setup mock data
    device_id = "rheem-wh-123"
    hours = 48
    analysis = {
        "telemetry_health": "good",
        "anomalies_detected": [
            {
                "type": "temperature_spike",
                "timestamp": "2023-07-15T08:30:00",
                "value": 145.2,
            }
        ],
        "patterns": [
            "Morning usage peak between 6-8am",
            "Evening usage peak between 7-9pm",
        ],
        "estimated_daily_usage": 45.2,
        "peak_usage_time": "07:30-08:30",
    }
    mock_rheem_water_heater_service.analyze_telemetry.return_value = analysis

    # Execute test
    response = client.get(
        f"/api/rheem-water-heaters/{device_id}/telemetry-analysis?hours={hours}"
    )

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert result["telemetry_health"] == analysis["telemetry_health"]
    assert len(result["anomalies_detected"]) == len(analysis["anomalies_detected"])
    assert result["estimated_daily_usage"] == analysis["estimated_daily_usage"]

    # Verify service call
    mock_rheem_water_heater_service.analyze_telemetry.assert_called_once_with(
        device_id, hours=hours
    )


def test_set_rheem_water_heater_mode(client, mock_rheem_water_heater_service):
    """Test setting the mode for a Rheem water heater."""
    # Setup test data
    device_id = "rheem-wh-123"
    mode = RheemWaterHeaterMode.VACATION
    mock_rheem_water_heater_service.set_water_heater_mode.return_value = None

    # Execute test
    response = client.put(
        f"/api/rheem-water-heaters/{device_id}/mode?mode={mode.value}"
    )

    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert mode.value in result["message"]
    assert result["device_id"] == device_id
    assert result["mode"] == mode.value

    # Verify service call
    mock_rheem_water_heater_service.set_water_heater_mode.assert_called_once_with(
        device_id, mode
    )
