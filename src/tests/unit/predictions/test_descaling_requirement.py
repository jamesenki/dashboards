"""
Tests for the descaling requirement prediction model.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.predictions.interfaces import (
    ActionSeverity,
    PredictionResult,
    RecommendedAction,
)
from src.predictions.maintenance.descaling_requirement import (
    DescalingActionRecommender,
    DescalingRequirementPrediction,
)


class TestDescalingRequirementPrediction:
    """Test suite for descaling requirement prediction model."""

    @pytest.fixture
    def descaling_model(self):
        """Fixture for descaling requirement prediction model."""
        return DescalingRequirementPrediction()

    @pytest.fixture
    def descaling_recommender(self):
        """Fixture for descaling action recommender."""
        return DescalingActionRecommender()

    @pytest.fixture
    def sample_features(self):
        """Sample features for prediction testing."""
        # Create realistic-looking water heater telemetry with efficiency degradation
        timestamps = pd.date_range(end=datetime.now(), periods=90, freq="D")

        # Energy efficiency degradation over time (increasing energy usage for same output)
        # Start relatively efficient and gradually degrade
        efficiency_trend = np.linspace(0.92, 0.78, 90) + np.random.normal(0, 0.02, 90)

        # Heating element temperature over time (higher = less efficient heat transfer)
        element_temp = np.linspace(70, 85, 90) + np.random.normal(0, 2, 90)

        # Calculated energy usage based on efficiency
        base_energy = 1200  # base energy consumption in optimal condition
        energy_usage = base_energy / efficiency_trend + np.random.normal(0, 50, 90)

        # Flow rate with gradual degradation due to scaling
        flow_rates = np.linspace(10, 8.2, 90) + np.random.normal(0, 0.2, 90)

        # Heating cycles - time to heat water increases as scale builds up
        heating_cycles = np.linspace(15, 22, 90) + np.random.normal(0, 1, 90)

        # Water hardness level (high = more scaling)
        water_hardness = 280  # ppm (relatively hard water)

        return {
            "device_id": "test-water-heater-1",
            "timestamp": timestamps.tolist(),
            "efficiency": efficiency_trend.tolist(),
            "element_temperature": element_temp.tolist(),
            "energy_usage": energy_usage.tolist(),
            "flow_rate": flow_rates.tolist(),
            "heating_cycles": heating_cycles.tolist(),
            "water_hardness": water_hardness,
            "total_operation_hours": 4380,  # 6 months
            "maintenance_history": [
                {"type": "installation", "date": datetime.now() - timedelta(days=180)},
                {"type": "regular", "date": datetime.now() - timedelta(days=90)}
                # No descaling in history - should need it based on degradation patterns
            ],
        }

    @pytest.fixture
    def recently_descaled_features(self):
        """Sample features for a recently descaled water heater."""
        # Create realistic-looking water heater telemetry with good efficiency
        timestamps = pd.date_range(end=datetime.now(), periods=30, freq="D")

        # Stable good efficiency after recent descaling
        efficiency_trend = np.ones(30) * 0.9 + np.random.normal(0, 0.01, 30)

        # Normal heating element temperature
        element_temp = np.ones(30) * 72 + np.random.normal(0, 1, 30)

        # Calculated energy usage based on efficiency
        base_energy = 1200  # base energy consumption in optimal condition
        energy_usage = base_energy / efficiency_trend + np.random.normal(0, 30, 30)

        # Good flow rate
        flow_rates = np.ones(30) * 9.8 + np.random.normal(0, 0.1, 30)

        # Normal heating cycles
        heating_cycles = np.ones(30) * 15.5 + np.random.normal(0, 0.5, 30)

        # Water hardness level (high = more scaling)
        water_hardness = 280  # ppm (relatively hard water)

        return {
            "device_id": "test-water-heater-2",
            "timestamp": timestamps.tolist(),
            "efficiency": efficiency_trend.tolist(),
            "element_temperature": element_temp.tolist(),
            "energy_usage": energy_usage.tolist(),
            "flow_rate": flow_rates.tolist(),
            "heating_cycles": heating_cycles.tolist(),
            "water_hardness": water_hardness,
            "total_operation_hours": 8760,  # 1 year
            "maintenance_history": [
                {"type": "installation", "date": datetime.now() - timedelta(days=365)},
                {
                    "type": "descaling",
                    "date": datetime.now() - timedelta(days=20),
                },  # Recent descaling
                {"type": "regular", "date": datetime.now() - timedelta(days=20)},
            ],
        }

    @pytest.mark.asyncio
    async def test_model_initialization(self, descaling_model):
        """Test that the model initializes correctly with required attributes."""
        model_info = descaling_model.get_model_info()

        assert "name" in model_info
        assert "version" in model_info
        assert "features_required" in model_info
        assert "efficiency" in model_info["features_required"]
        assert "water_hardness" in model_info["features_required"]

    @pytest.mark.asyncio
    async def test_descaling_prediction_needs_descaling(
        self, descaling_model, sample_features
    ):
        """Test descaling prediction with features indicating need for descaling."""
        # Perform prediction
        result = await descaling_model.predict(
            sample_features["device_id"], sample_features
        )

        # Verify structure and basic values
        assert result.prediction_type == "descaling_requirement"
        assert result.device_id == "test-water-heater-1"
        assert 0 <= result.predicted_value <= 1  # 1 = needs descaling soon
        assert 0 <= result.confidence <= 1
        assert result.features_used

        # Should indicate high need for descaling
        assert result.predicted_value > 0.7

        # Should have at least one action recommendation
        assert len(result.recommended_actions) > 0

        # Raw details should include specific metrics
        assert "raw_details" in result.dict()
        if result.raw_details:
            assert "efficiency_degradation" in result.raw_details
            assert "days_since_last_descaling" in result.raw_details

    @pytest.mark.asyncio
    async def test_descaling_prediction_recently_descaled(
        self, descaling_model, recently_descaled_features
    ):
        """Test prediction with features indicating recent descaling."""
        # Perform prediction
        result = await descaling_model.predict(
            recently_descaled_features["device_id"], recently_descaled_features
        )

        # Verify structure and basic values
        assert result.prediction_type == "descaling_requirement"
        assert result.device_id == "test-water-heater-2"

        # Should indicate low need for descaling
        assert result.predicted_value < 0.3

        # Should have minimal or no action recommendations
        assert len(result.recommended_actions) <= 1

    @pytest.mark.asyncio
    async def test_action_recommendations(self, descaling_recommender):
        """Test action recommendations for descaling requirement prediction."""
        # Create a sample prediction result
        prediction = PredictionResult(
            prediction_type="descaling_requirement",
            device_id="test-water-heater-1",
            predicted_value=0.85,  # High need for descaling
            confidence=0.9,
            features_used=["efficiency", "water_hardness", "heating_cycles"],
            timestamp=datetime.now(),
            recommended_actions=[],
            raw_details={
                "efficiency_degradation": 0.15,  # 15% degradation
                "days_since_last_descaling": 180,
                "water_hardness": 280,  # ppm
                "estimated_scale_thickness_mm": 2.8,
            },
        )

        # Get recommendations
        actions = await descaling_recommender.recommend_actions(prediction)

        # Verify recommendations
        assert len(actions) > 0

        # Should include descaling action
        descaling_actions = [a for a in actions if "descal" in a.description.lower()]
        assert len(descaling_actions) > 0

        # At least one action should be high or medium severity
        high_severity_actions = [
            a
            for a in actions
            if a.severity in [ActionSeverity.HIGH, ActionSeverity.MEDIUM]
        ]
        assert len(high_severity_actions) > 0

    @pytest.mark.asyncio
    async def test_missing_features_handling(self, descaling_model):
        """Test that the model handles missing features gracefully."""
        # Create minimal features
        minimal_features = {
            "device_id": "test-water-heater-3",
            "energy_usage": [1300, 1320, 1350, 1380, 1420],  # Only energy usage
            "water_hardness": 180,
            "total_operation_hours": 2000
            # Missing other features
        }

        # Perform prediction
        result = await descaling_model.predict(
            minimal_features["device_id"], minimal_features
        )

        # Should still give a prediction but with lower confidence
        assert result.prediction_type == "descaling_requirement"
        assert 0 <= result.predicted_value <= 1
        assert result.confidence < 0.7  # Lower confidence due to missing data
