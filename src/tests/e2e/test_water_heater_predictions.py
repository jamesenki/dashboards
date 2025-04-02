"""
End-to-end tests for water heater predictions functionality.
Tests that predictions load correctly on the water heater details screen.
"""
import json
import time

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestWaterHeaterPredictions:
    """Test suite for water heater predictions functionality."""

    def setup_method(self):
        """Set up test data - get a list of available water heaters."""
        self.water_heater_list_response = client.get("/api/water-heaters/")
        assert self.water_heater_list_response.status_code == 200
        self.water_heaters = self.water_heater_list_response.json()
        assert len(self.water_heaters) > 0, "No water heaters found for testing"

        # Select the first water heater for testing
        self.test_heater = self.water_heaters[0]
        self.heater_id = self.test_heater["id"]

    def test_prediction_api_endpoints(self):
        """Test that all prediction API endpoints are accessible and return data."""
        # Test lifespan estimation prediction
        lifespan_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/lifespan-estimation"
        )
        assert (
            lifespan_response.status_code == 200
        ), f"Lifespan prediction failed with status {lifespan_response.status_code}"
        lifespan_data = lifespan_response.json()
        assert lifespan_data["device_id"] == self.heater_id
        assert lifespan_data["prediction_type"] == "lifespan_estimation"

        # Test anomaly detection prediction
        anomaly_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/anomaly-detection"
        )
        assert (
            anomaly_response.status_code == 200
        ), f"Anomaly detection failed with status {anomaly_response.status_code}"
        anomaly_data = anomaly_response.json()
        assert anomaly_data["device_id"] == self.heater_id
        assert anomaly_data["prediction_type"] == "anomaly_detection"

        # Test usage patterns prediction
        usage_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/usage-patterns"
        )
        assert (
            usage_response.status_code == 200
        ), f"Usage patterns failed with status {usage_response.status_code}"
        usage_data = usage_response.json()
        assert usage_data["device_id"] == self.heater_id
        assert usage_data["prediction_type"] == "usage_patterns"

        # Test multi-factor prediction
        multi_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/multi-factor"
        )
        assert (
            multi_response.status_code == 200
        ), f"Multi-factor prediction failed with status {multi_response.status_code}"
        multi_data = multi_response.json()
        assert multi_data["device_id"] == self.heater_id
        assert multi_data["prediction_type"] == "multi_factor"

        # Test all predictions endpoint
        all_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/all"
        )
        assert (
            all_response.status_code == 200
        ), f"All predictions failed with status {all_response.status_code}"
        all_data = all_response.json()
        assert (
            len(all_data) >= 4
        ), f"Expected at least 4 predictions, got {len(all_data)}"

        # Verify that prediction types are included in the response
        prediction_types = [pred["prediction_type"] for pred in all_data]
        assert "lifespan_estimation" in prediction_types
        assert "anomaly_detection" in prediction_types
        assert "usage_patterns" in prediction_types
        assert "multi_factor" in prediction_types

    def test_prediction_data_structure(self):
        """Test that prediction data has the expected structure."""
        # Test lifespan estimation prediction structure
        lifespan_response = client.get(
            f"/api/predictions/water-heaters/{self.heater_id}/lifespan-estimation"
        )
        assert lifespan_response.status_code == 200
        lifespan_data = lifespan_response.json()

        # Check required fields
        assert "device_id" in lifespan_data
        assert "prediction_type" in lifespan_data
        assert "predicted_value" in lifespan_data
        assert "confidence" in lifespan_data
        assert "features_used" in lifespan_data
        assert "timestamp" in lifespan_data
        assert "recommended_actions" in lifespan_data
        assert "raw_details" in lifespan_data

        # Check specific lifespan prediction fields in raw_details
        raw_details = lifespan_data["raw_details"]
        assert (
            "estimated_remaining_years" in raw_details
            or "estimated_remaining_days" in raw_details
        )

    def test_prediction_ui_integration(self):
        """Test that predictions are displayed correctly in the UI."""
        # 1. Get the HTML page for the water heater details
        page_response = client.get(f"/water-heaters/{self.heater_id}")
        assert page_response.status_code == 200

        # 2. Parse the HTML to verify prediction elements exist
        soup = BeautifulSoup(page_response.text, "html.parser")

        # Check for prediction section in the details tab
        prediction_section = soup.select_one("#prediction-section") or soup.select_one(
            ".prediction-section"
        )
        assert prediction_section, "Prediction section not found in the UI"

        # Check for specific prediction widgets or components
        lifespan_widget = soup.select_one("#lifespan-prediction") or soup.select_one(
            ".lifespan-prediction"
        )
        assert lifespan_widget, "Lifespan prediction widget not found"

        anomaly_widget = soup.select_one("#anomaly-prediction") or soup.select_one(
            ".anomaly-prediction"
        )
        assert anomaly_widget, "Anomaly prediction widget not found"

        # Find any prediction loading indicators
        loading_indicators = soup.select(".prediction-loading") or soup.select(
            ".loading-indicator"
        )

        # Check for script that initializes predictions
        prediction_scripts = []
        for script in soup.find_all("script"):
            if script.string and (
                "prediction" in script.string.lower()
                or "forecast" in script.string.lower()
            ):
                prediction_scripts.append(script)

        assert len(prediction_scripts) > 0, "No prediction initialization scripts found"

        print(f"Prediction UI tests completed for water heater {self.heater_id}")
