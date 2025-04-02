import datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.predictions.interfaces import PredictionResult
from src.predictions.maintenance.lifespan_estimation import LifespanEstimationPrediction


class TestLifespanEstimationPrediction:
    """Tests for the LifespanEstimationPrediction class."""

    @pytest.fixture
    def prediction_model(self):
        """Create a lifespan estimation prediction model for testing."""
        return LifespanEstimationPrediction()

    @pytest.fixture
    def new_device_features(self):
        """Features for a relatively new device with good indicators."""
        return {
            "device_id": "wh123",
            "installation_date": (
                datetime.datetime.now() - datetime.timedelta(days=365)
            ).isoformat(),
            "total_operation_hours": 3000,
            "usage_intensity": "normal",
            "water_hardness": 100,  # moderately hard water
            "temperature_settings": [
                55,
                55,
                60,
                55,
                55,
                55,
                55,
            ],  # mostly moderate temperature
            "heating_cycles_per_day": 4,
            "efficiency_degradation_rate": 0.02,  # slow degradation
            "component_health": {
                "heating_element": 0.9,
                "thermostat": 0.95,
                "anode_rod": 0.85,
                "pressure_relief_valve": 0.9,
                "tank_integrity": 0.95,
            },
            "maintenance_history": [
                {
                    "type": "inspection",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=90)
                    ).isoformat(),
                    "findings": "all_good",
                }
            ],
        }

    @pytest.fixture
    def aging_device_features(self):
        """Features for an aging device with moderate wear indicators."""
        return {
            "device_id": "wh456",
            "installation_date": (
                datetime.datetime.now() - datetime.timedelta(days=2190)
            ).isoformat(),  # 6 years
            "total_operation_hours": 18000,
            "usage_intensity": "heavy",
            "water_hardness": 180,  # hard water
            "temperature_settings": [
                65,
                65,
                70,
                65,
                65,
                65,
                65,
            ],  # higher temperature settings
            "heating_cycles_per_day": 6,
            "efficiency_degradation_rate": 0.05,  # moderate degradation
            "component_health": {
                "heating_element": 0.7,
                "thermostat": 0.8,
                "anode_rod": 0.5,  # anode rod showing significant wear
                "pressure_relief_valve": 0.75,
                "tank_integrity": 0.7,
            },
            "maintenance_history": [
                {
                    "type": "anode_rod_replacement",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=730)
                    ).isoformat(),  # 2 years ago
                    "findings": "moderate_corrosion",
                },
                {
                    "type": "inspection",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=365)
                    ).isoformat(),  # 1 year ago
                    "findings": "normal_wear",
                },
            ],
        }

    @pytest.fixture
    def old_device_features(self):
        """Features for an old device with significant wear indicators."""
        return {
            "device_id": "wh789",
            "installation_date": (
                datetime.datetime.now() - datetime.timedelta(days=3650)
            ).isoformat(),  # 10 years
            "total_operation_hours": 30000,
            "usage_intensity": "heavy",
            "water_hardness": 250,  # very hard water
            "temperature_settings": [
                70,
                70,
                75,
                70,
                70,
                70,
                70,
            ],  # high temperature settings
            "heating_cycles_per_day": 8,
            "efficiency_degradation_rate": 0.15,  # rapid degradation
            "component_health": {
                "heating_element": 0.4,
                "thermostat": 0.5,
                "anode_rod": 0.2,  # anode rod nearly depleted
                "pressure_relief_valve": 0.45,
                "tank_integrity": 0.35,  # potential tank issues
            },
            "maintenance_history": [
                {
                    "type": "heating_element_replacement",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=1095)
                    ).isoformat(),  # 3 years ago
                    "findings": "element_failure",
                },
                {
                    "type": "anode_rod_replacement",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=730)
                    ).isoformat(),  # 2 years ago
                    "findings": "severe_corrosion",
                },
                {
                    "type": "leak_repair",
                    "date": (
                        datetime.datetime.now() - datetime.timedelta(days=180)
                    ).isoformat(),  # 6 months ago
                    "findings": "minor_leak",
                },
            ],
        }

    @pytest.fixture
    def minimal_device_features(self):
        """Minimal features for a device with limited data."""
        return {
            "device_id": "wh999",
            "installation_date": (
                datetime.datetime.now() - datetime.timedelta(days=1825)
            ).isoformat(),  # 5 years
            "total_operation_hours": 15000,
            "water_hardness": 150,  # moderately hard water
        }

    async def test_lifespan_prediction_for_new_device(
        self, prediction_model, new_device_features
    ):
        """Test lifespan prediction for a relatively new device."""
        result = await prediction_model.predict("wh123", new_device_features)

        # Validate the prediction result
        assert isinstance(result, PredictionResult)
        assert (
            0.7 <= result.predicted_value <= 0.95
        )  # Should have high remaining lifespan
        assert len(result.recommended_actions) > 0

        # Check for expected fields in raw details
        assert "estimated_remaining_years" in result.raw_details
        assert "total_expected_lifespan_years" in result.raw_details
        assert "current_age_years" in result.raw_details
        assert "contributing_factors" in result.raw_details

        # Check that estimated remaining years is reasonable (7+ years for a 1 year old unit)
        assert result.raw_details["estimated_remaining_years"] >= 7
        assert result.raw_details["current_age_years"] == 1

    async def test_lifespan_prediction_for_aging_device(
        self, prediction_model, aging_device_features
    ):
        """Test lifespan prediction for a device showing moderate age and wear."""
        result = await prediction_model.predict("wh456", aging_device_features)

        # Validate the prediction result
        assert isinstance(result, PredictionResult)
        assert (
            0.3 <= result.predicted_value <= 0.7
        )  # Should have moderate remaining lifespan
        assert len(result.recommended_actions) > 0

        # Check factors affecting lifespan
        contributing_factors = result.raw_details["contributing_factors"]

        # Should identify anode rod as a key factor
        assert any("anode" in factor.lower() for factor in contributing_factors)

        # Estimated remaining years should be less than for a new device
        assert result.raw_details["estimated_remaining_years"] < 7
        assert (
            5 <= result.raw_details["current_age_years"] <= 6
        )  # Should be around 6 years

    async def test_lifespan_prediction_for_old_device(
        self, prediction_model, old_device_features
    ):
        """Test lifespan prediction for an old device with significant wear."""
        result = await prediction_model.predict("wh789", old_device_features)

        # Validate the prediction result
        assert isinstance(result, PredictionResult)
        assert (
            0.05 <= result.predicted_value <= 0.35
        )  # Should have low remaining lifespan
        assert len(result.recommended_actions) >= 2  # Should have multiple actions

        # Check for critical actions
        has_replacement_action = any(
            "replace" in action.description.lower()
            or "replacement" in action.description.lower()
            for action in result.recommended_actions
        )
        assert has_replacement_action

        # Check for severe factors
        assert len(result.raw_details["contributing_factors"]) >= 3

        # Check age and remaining life
        assert result.raw_details["current_age_years"] == 10
        assert result.raw_details["estimated_remaining_years"] <= 3

    async def test_lifespan_prediction_with_minimal_data(
        self, prediction_model, minimal_device_features
    ):
        """Test that prediction works with minimal data."""
        result = await prediction_model.predict("wh999", minimal_device_features)

        # Validate the prediction result
        assert isinstance(result, PredictionResult)
        assert 0 <= result.predicted_value <= 1
        assert len(result.recommended_actions) > 0

        # Should recommend getting an inspection
        has_inspection_action = any(
            "inspect" in action.description.lower()
            or "assessment" in action.description.lower()
            for action in result.recommended_actions
        )
        assert has_inspection_action

        # Should indicate that the prediction is based on limited data
        assert (
            "limited data" in str(result.raw_details).lower()
            or "limited information" in str(result.raw_details).lower()
        )

    async def test_missing_installation_date(self, prediction_model):
        """Test handling of missing installation date."""
        features = {
            "device_id": "wh000",
            "total_operation_hours": 10000,
            "water_hardness": 150,
        }

        result = await prediction_model.predict("wh000", features)

        # Should still return a valid prediction
        assert isinstance(result, PredictionResult)
        assert "estimated_installation_date" in str(result.raw_details).lower()

        # Should have a data quality recommendation
        has_data_quality_action = any(
            "data" in action.description.lower()
            and "quality" in action.description.lower()
            for action in result.recommended_actions
        )
        assert has_data_quality_action

    async def test_model_information(self, prediction_model):
        """Test retrieval of model information."""
        info = prediction_model.get_model_info()

        assert info.get("name") == "LifespanEstimationPrediction"
        assert "version" in info
        assert info.get("description") is not None
        assert "lifespan" in info.get("description").lower()
        assert "prediction_type" in info
        assert info.get("prediction_type") == "lifespan_estimation"
