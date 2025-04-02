"""
Tests for the prediction interface and base classes.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pytest

from src.predictions.interfaces import (
    ActionSeverity,
    IPredictionModel,
    PredictionResult,
    RecommendedAction,
)


# Mock implementation for testing
class MockPredictionModel(IPredictionModel):
    """Mock implementation of IPredictionModel for testing."""

    def __init__(self, prediction_value: float = 0.75, confidence: float = 0.85):
        self.prediction_value = prediction_value
        self.confidence = confidence
        self.features_used = ["temperature", "pressure", "cycles"]

    async def predict(
        self, device_id: str, features: Dict[str, Any]
    ) -> PredictionResult:
        """Generate a mock prediction."""
        return PredictionResult(
            prediction_type="mock_prediction",
            device_id=device_id,
            predicted_value=self.prediction_value,
            confidence=self.confidence,
            features_used=self.features_used,
            timestamp=datetime.now(),
            recommended_actions=[
                RecommendedAction(
                    action_id="mock_action_1",
                    description="This is a mock action",
                    severity=ActionSeverity.MEDIUM,
                    impact="Potential impact description",
                    expected_benefit="Expected benefit description",
                )
            ],
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the model."""
        return {
            "name": "MockModel",
            "version": "1.0.0",
            "description": "A mock model for testing",
            "features_required": self.features_used,
            "last_trained": datetime.now() - timedelta(days=7),
            "performance_metrics": {"mae": 0.12, "rmse": 0.18, "r2": 0.89},
        }


class TestPredictionInterface:
    """Test suite for the prediction interface."""

    def test_prediction_result_validation(self):
        """Test that PredictionResult validates data correctly."""
        # Valid result
        result = PredictionResult(
            prediction_type="test_prediction",
            device_id="device-123",
            predicted_value=0.85,
            confidence=0.95,
            features_used=["temp", "pressure"],
            timestamp=datetime.now(),
            recommended_actions=[],
        )

        assert result.prediction_type == "test_prediction"
        assert result.device_id == "device-123"
        assert result.predicted_value == 0.85
        assert result.confidence == 0.95

    def test_recommended_action_validation(self):
        """Test that RecommendedAction validates data correctly."""
        # Valid action
        action = RecommendedAction(
            action_id="action-123",
            description="Test action",
            severity=ActionSeverity.HIGH,
            impact="High impact",
            expected_benefit="Better performance",
        )

        assert action.action_id == "action-123"
        assert action.description == "Test action"
        assert action.severity == ActionSeverity.HIGH

    @pytest.mark.asyncio
    async def test_mock_prediction_model(self):
        """Test the mock prediction model behaves as expected."""
        model = MockPredictionModel(prediction_value=0.65, confidence=0.75)
        features = {
            "temperature": [65.0, 68.0, 70.0],
            "pressure": [2.5, 2.6, 2.4],
            "cycles": 230,
        }

        result = await model.predict("test-device-1", features)

        assert result.device_id == "test-device-1"
        assert result.predicted_value == 0.65
        assert result.confidence == 0.75
        assert len(result.recommended_actions) == 1
        assert result.recommended_actions[0].severity == ActionSeverity.MEDIUM

    def test_model_info(self):
        """Test that model info is returned correctly."""
        model = MockPredictionModel()
        info = model.get_model_info()

        assert "name" in info
        assert "version" in info
        assert "features_required" in info
        assert "performance_metrics" in info
        assert len(info["features_required"]) == 3
