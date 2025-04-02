"""
Unit tests for recommendation generation across all prediction models.

Tests that all prediction models consistently provide recommendations
and properly format their outputs.
"""
import asyncio
from datetime import datetime, timedelta

import pytest

from src.predictions.advanced.anomaly_detection import AnomalyDetectionPredictor
from src.predictions.advanced.multi_factor import MultiFactorPredictor
from src.predictions.advanced.usage_patterns import UsagePatternPredictor
from src.predictions.interfaces import PredictionResult
from src.predictions.maintenance.lifespan_estimation import LifespanEstimationPrediction


class TestRecommendationGeneration:
    """Tests for consistent recommendation generation across models."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a standard set of features for testing all predictors
        self.standard_features = {
            "temperature_readings": [
                {"timestamp": datetime.now() - timedelta(days=30), "value": 140},
                {"timestamp": datetime.now() - timedelta(days=15), "value": 145},
                {"timestamp": datetime.now(), "value": 150},
            ],
            "pressure_readings": [
                {"timestamp": datetime.now() - timedelta(days=30), "value": 50},
                {"timestamp": datetime.now() - timedelta(days=15), "value": 55},
                {"timestamp": datetime.now(), "value": 60},
            ],
            "daily_usage_liters": [
                {"date": datetime.now() - timedelta(days=30), "value": 150},
                {"date": datetime.now() - timedelta(days=15), "value": 160},
                {"date": datetime.now(), "value": 170},
            ],
            "heating_cycles_per_day": [
                {"date": datetime.now() - timedelta(days=30), "value": 5},
                {"date": datetime.now() - timedelta(days=15), "value": 6},
                {"date": datetime.now(), "value": 7},
            ],
            "installation_date": datetime.now() - timedelta(days=365),
            "maintenance_history": [
                {
                    "date": datetime.now() - timedelta(days=180),
                    "type": "routine_check",
                    "notes": "All systems normal",
                },
            ],
            "model_specifications": {
                "expected_lifespan_years": 10,
                "efficiency_rating": 0.85,
                "tank_capacity_liters": 200,
            },
        }
        self.device_id = "test-device-123"

    @pytest.mark.asyncio
    async def test_anomaly_detection_always_provides_recommendations(self):
        """Test that anomaly detection always provides at least one recommendation."""
        predictor = AnomalyDetectionPredictor()
        predict_result = predictor.predict(
            device_id=self.device_id, features=self.standard_features
        )

        # Handle both async and non-async predict methods
        if asyncio.iscoroutine(predict_result):
            result = await predict_result
        else:
            result = predict_result

        assert isinstance(result, PredictionResult)
        assert (
            len(result.recommended_actions) > 0
        ), "Anomaly detection should always provide at least one recommendation"

        # Check formatting of recommendation fields
        for action in result.recommended_actions:
            assert action.description is not None and isinstance(
                action.description, str
            )
            assert action.severity is not None
            assert action.impact is not None and isinstance(action.impact, str)

    @pytest.mark.asyncio
    async def test_usage_patterns_always_provides_recommendations(self):
        """Test that usage pattern analysis always provides at least one recommendation."""
        predictor = UsagePatternPredictor()
        result = await predictor.predict(
            device_id=self.device_id, features=self.standard_features
        )

        assert isinstance(result, PredictionResult)
        assert (
            len(result.recommended_actions) > 0
        ), "Usage patterns should always provide at least one recommendation"

        # Check formatting of recommendation fields
        for action in result.recommended_actions:
            assert action.description is not None and isinstance(
                action.description, str
            )
            assert action.severity is not None
            assert action.impact is not None and isinstance(action.impact, str)

    @pytest.mark.asyncio
    async def test_multi_factor_always_provides_recommendations(self):
        """Test that multi-factor analysis always provides at least one recommendation."""
        predictor = MultiFactorPredictor()
        predict_result = predictor.predict(
            device_id=self.device_id, features=self.standard_features
        )

        # Handle both async and non-async predict methods
        if asyncio.iscoroutine(predict_result):
            result = await predict_result
        else:
            result = predict_result

        assert isinstance(result, PredictionResult)
        assert (
            len(result.recommended_actions) > 0
        ), "Multi-factor analysis should always provide at least one recommendation"

        # Check formatting of recommendation fields
        for action in result.recommended_actions:
            assert action.description is not None and isinstance(
                action.description, str
            )
            assert action.severity is not None
            assert action.impact is not None and isinstance(action.impact, str)

    @pytest.mark.asyncio
    async def test_lifespan_estimation_always_provides_recommendations(self):
        """Test that lifespan estimation always provides at least one recommendation."""
        predictor = LifespanEstimationPrediction()

        # Get prediction result
        predict_result = predictor.predict(
            device_id=self.device_id, features=self.standard_features
        )

        # Handle both async and non-async predict methods
        if asyncio.iscoroutine(predict_result):
            result = await predict_result
        else:
            result = predict_result

        assert isinstance(result, PredictionResult)
        assert (
            len(result.recommended_actions) > 0
        ), "Lifespan estimation should always provide at least one recommendation"

        # Check formatting of recommendation fields
        for action in result.recommended_actions:
            assert action.description is not None and isinstance(
                action.description, str
            )
            assert action.severity is not None
            assert action.impact is not None and isinstance(action.impact, str)

    @pytest.mark.asyncio
    async def test_all_raw_details_properly_formatted(self):
        """Test that all models return properly formatted raw_details that avoid [object Object] display issues."""

        # Test each predictor for proper JSON serialization
        predictors = [
            AnomalyDetectionPredictor(),
            UsagePatternPredictor(),
            MultiFactorPredictor()
            # LifespanEstimationPrediction requires special async handling, tested separately
        ]

        for predictor in predictors:
            # Handle both async and non-async predict methods
            predict_result = predictor.predict(
                device_id=self.device_id, features=self.standard_features
            )

            # If the result is awaitable (coroutine), await it
            if asyncio.iscoroutine(predict_result):
                result = await predict_result
            else:
                # If it's already a PredictionResult, use it directly
                result = predict_result

            # Check specific fields that might be incorrectly formatted as objects
            if "environmental_impact" in result.raw_details:
                assert not isinstance(
                    result.raw_details["environmental_impact"], object
                ) or isinstance(
                    result.raw_details["environmental_impact"], dict
                ), f"environmental_impact should be a properly formatted dict or primitive, not a generic object in {predictor.__class__.__name__}"

            if "component_interactions" in result.raw_details:
                assert isinstance(
                    result.raw_details["component_interactions"], (list, dict)
                ), f"component_interactions should be a list or dict in {predictor.__class__.__name__}"

        # Test async lifespan estimation separately
        lifespan_predictor = LifespanEstimationPrediction()
        predict_result = lifespan_predictor.predict(
            device_id=self.device_id, features=self.standard_features
        )

        # If the result is awaitable (coroutine), await it
        if asyncio.iscoroutine(predict_result):
            lifespan_result = await predict_result
        else:
            # If it's already a PredictionResult, use it directly
            lifespan_result = predict_result

        # Check lifespan estimation raw details
        assert isinstance(lifespan_result, PredictionResult)
        if "environmental_impact" in lifespan_result.raw_details:
            assert not isinstance(
                lifespan_result.raw_details["environmental_impact"], object
            ) or isinstance(lifespan_result.raw_details["environmental_impact"], dict)

        if "component_interactions" in lifespan_result.raw_details:
            assert isinstance(
                lifespan_result.raw_details["component_interactions"], (list, dict)
            )
