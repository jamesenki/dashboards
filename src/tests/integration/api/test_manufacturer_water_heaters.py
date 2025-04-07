"""
Integration tests for the manufacturer-agnostic water heater API endpoints.

This test suite verifies that the manufacturer-based water heater API correctly
handles requests with and without manufacturer filtering, and that it works with
the existing repository layer.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.water_heater import WaterHeater, WaterHeaterMode

client = TestClient(app)


class TestManufacturerWaterHeaterApi:
    """Tests for manufacturer-agnostic water heater API endpoints."""

    def test_get_water_heaters_no_filter(self):
        """Test getting all water heaters without a manufacturer filter."""
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()
        assert isinstance(water_heaters, list)
        # Should return all water heaters, regardless of manufacturer
        assert len(water_heaters) > 0

    def test_get_water_heaters_with_filter(self):
        """Test getting water heaters with a manufacturer filter."""
        # Test with specific manufacturer (both should work because of brand-agnostic design)
        for manufacturer in ["Rheem", "AquaTherm"]:
            response = client.get(
                f"/api/manufacturer/water-heaters/?manufacturer={manufacturer}"
            )
            assert response.status_code == 200
            water_heaters = response.json()
            assert isinstance(water_heaters, list)

            # If there are results, they should all match the manufacturer
            if water_heaters:
                for heater in water_heaters:
                    assert manufacturer.lower() in heater["manufacturer"].lower()

    def test_get_water_heater_by_id(self):
        """Test getting a specific water heater by ID."""
        # First get all water heaters to find a valid ID
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()

        if water_heaters:
            # Get the ID of the first water heater
            device_id = water_heaters[0]["id"]

            # Test getting that specific water heater
            detail_response = client.get(f"/api/manufacturer/water-heaters/{device_id}")
            assert detail_response.status_code == 200
            water_heater = detail_response.json()
            assert water_heater["id"] == device_id

    def test_get_water_heater_not_found(self):
        """Test getting a non-existent water heater."""
        response = client.get("/api/manufacturer/water-heaters/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_supported_manufacturers(self):
        """Test getting the list of supported manufacturers."""
        response = client.get("/api/manufacturer/water-heaters/manufacturers/supported")
        assert response.status_code == 200
        manufacturers = response.json()
        assert isinstance(manufacturers, list)
        assert len(manufacturers) > 0

        # Check required fields are present
        for manufacturer in manufacturers:
            assert "manufacturer_id" in manufacturer
            assert "name" in manufacturer
            assert "supported_features" in manufacturer
            assert "supported_models" in manufacturer
            assert "api_version" in manufacturer

        # Verify Rheem and AquaTherm are included
        manufacturer_names = [m["name"] for m in manufacturers]
        assert "Rheem" in manufacturer_names
        assert "AquaTherm" in manufacturer_names

    def test_get_operational_summary(self):
        """Test getting the operational summary for a water heater."""
        # First get all water heaters to find a valid ID
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()

        if water_heaters:
            # Get the ID of the first water heater
            device_id = water_heaters[0]["id"]

            # Test getting operational summary
            summary_response = client.get(
                f"/api/manufacturer/water-heaters/{device_id}/operational-summary"
            )
            assert summary_response.status_code == 200
            summary = summary_response.json()

            # Check required fields
            assert "uptime_percentage" in summary
            assert "average_daily_runtime" in summary
            assert "heating_cycles_per_day" in summary
            assert "energy_usage" in summary
            assert "temperature_efficiency" in summary
            assert "mode_usage" in summary

    def test_get_maintenance_prediction(self):
        """Test getting the maintenance prediction for a water heater."""
        # First get all water heaters to find a valid ID
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()

        if water_heaters:
            # Get the ID of the first water heater
            device_id = water_heaters[0]["id"]

            # Test getting maintenance prediction
            prediction_response = client.get(
                f"/api/manufacturer/water-heaters/{device_id}/maintenance-prediction"
            )
            assert prediction_response.status_code == 200
            prediction = prediction_response.json()

            # Check required fields
            assert "days_until_service" in prediction
            assert "component_predictions" in prediction
            assert "recommendation" in prediction
            assert "confidence" in prediction

    def test_update_water_heater_mode(self):
        """Test updating the mode of a water heater."""
        # First get all water heaters to find a valid ID
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()

        if water_heaters:
            # Get the ID of the first water heater
            device_id = water_heaters[0]["id"]

            # Test updating the mode
            new_mode = "ECO"  # Using a valid WaterHeaterMode value
            update_response = client.patch(
                f"/api/manufacturer/water-heaters/{device_id}/mode?mode={new_mode}"
            )
            assert update_response.status_code == 200
            result = update_response.json()

            # Check required fields
            assert "message" in result
            assert "device_id" in result
            assert "mode" in result
            assert "timestamp" in result
            assert result["device_id"] == device_id
            assert result["mode"] == new_mode

    def test_update_water_heater_mode_invalid_mode(self):
        """Test updating the mode with an invalid mode value."""
        # First get all water heaters to find a valid ID
        response = client.get("/api/manufacturer/water-heaters/")
        assert response.status_code == 200
        water_heaters = response.json()

        if water_heaters:
            # Get the ID of the first water heater
            device_id = water_heaters[0]["id"]

            # Test updating with invalid mode
            invalid_mode = "INVALID_MODE"
            update_response = client.patch(
                f"/api/manufacturer/water-heaters/{device_id}/mode?mode={invalid_mode}"
            )
            assert update_response.status_code == 422  # Validation error
