"""
Tests for the MLOps Prediction Service.
"""
import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import joblib
import numpy as np
import pandas as pd
import pytest

from src.mlops.prediction_service import PredictionService


class TestPredictionService:
    """Test suite for the prediction service implementation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.model_registry_mock = MagicMock()
        self.db_mock = MagicMock()
        self.feature_store_mock = MagicMock()

        # Create prediction service with mocked dependencies
        self.prediction_service = PredictionService(
            db=self.db_mock,
            model_registry=self.model_registry_mock,
            feature_store=self.feature_store_mock,
        )

        # Sample model info returned from registry
        self.sample_model_info = {
            "model_id": "model-123",
            "model_name": "component_failure",
            "model_version": "2025.03.27.001",
            "model_path": "/tmp/models/component_failure_model.pkl",
            "status": "active",
            "created_at": datetime(2025, 3, 27),
            "metadata": {
                "features": ["temp", "pressure", "vibration", "age_days"],
                "accuracy": 0.92,
            },
        }

        # Sample input data for prediction
        self.sample_input = {
            "device_id": "WH-1001",
            "timestamp": "2025-03-27T10:30:00",
            "temp": 65.5,
            "pressure": 32.1,
            "vibration": 0.03,
            "age_days": 720,
        }

        # Sample processed features
        self.sample_features = pd.DataFrame(
            {"temp": [65.5], "pressure": [32.1], "vibration": [0.03], "age_days": [720]}
        )

    @patch("joblib.load")
    def test_predict(self, mock_joblib_load):
        """Test making a prediction using a model."""
        # Arrange
        model_name = "component_failure"
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0])  # Not failed
        mock_model.predict_proba.return_value = np.array(
            [[0.85, 0.15]]
        )  # 15% chance of failure
        mock_joblib_load.return_value = mock_model

        # Mock the model registry to return the model path
        self.model_registry_mock.get_active_model.return_value = self.sample_model_info

        # Act
        prediction = self.prediction_service.predict(
            model_name=model_name, input_data=self.sample_input
        )

        # Assert
        assert prediction is not None
        assert "prediction" in prediction
        assert "probability" in prediction
        assert "model_version" in prediction
        assert prediction["prediction"] == 0  # Not failed
        assert prediction["probability"] == 0.15  # 15% chance of failure
        assert prediction["model_version"] == self.sample_model_info["model_version"]

        # Verify model was loaded from the correct path
        mock_joblib_load.assert_called_once_with(self.sample_model_info["model_path"])

    def test_predict_with_missing_model(self):
        """Test prediction when model is not found."""
        # Arrange
        model_name = "nonexistent_model"

        # Mock the model registry to return None (no model found)
        self.model_registry_mock.get_active_model.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="No active model found"):
            self.prediction_service.predict(
                model_name=model_name, input_data=self.sample_input
            )

    @patch("joblib.load")
    def test_batch_predict(self, mock_joblib_load):
        """Test making predictions for a batch of devices."""
        # Arrange
        model_name = "component_failure"
        mock_model = Mock()
        mock_model.predict.return_value = np.array(
            [0, 1, 0]
        )  # Second device predicted to fail
        mock_model.predict_proba.return_value = np.array(
            [
                [0.9, 0.1],  # 10% chance of failure
                [0.3, 0.7],  # 70% chance of failure
                [0.8, 0.2],  # 20% chance of failure
            ]
        )
        mock_joblib_load.return_value = mock_model

        # Create a batch of device data
        batch_data = [
            {
                "device_id": "WH-1001",
                "temp": 65.5,
                "pressure": 32.1,
                "vibration": 0.03,
                "age_days": 720,
            },
            {
                "device_id": "WH-1002",
                "temp": 78.3,
                "pressure": 34.5,
                "vibration": 0.07,
                "age_days": 980,
            },
            {
                "device_id": "WH-1003",
                "temp": 68.2,
                "pressure": 33.0,
                "vibration": 0.04,
                "age_days": 540,
            },
        ]

        # Mock the model registry to return the model path
        self.model_registry_mock.get_active_model.return_value = self.sample_model_info

        # Act
        batch_predictions = self.prediction_service.batch_predict(
            model_name=model_name, batch_data=batch_data
        )

        # Assert
        assert batch_predictions is not None
        assert len(batch_predictions) == 3
        assert batch_predictions[0]["device_id"] == "WH-1001"
        assert batch_predictions[0]["prediction"] == 0  # Not failed
        assert batch_predictions[1]["device_id"] == "WH-1002"
        assert batch_predictions[1]["prediction"] == 1  # Predicted to fail
        assert batch_predictions[1]["probability"] == 0.7  # 70% chance of failure

    @patch("joblib.load")
    def test_predict_with_feedback(self, mock_joblib_load):
        """Test making prediction and automatically recording feedback."""
        # Arrange
        model_name = "component_failure"
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0])  # Not failed
        mock_model.predict_proba.return_value = np.array(
            [[0.85, 0.15]]
        )  # 15% chance of failure
        mock_joblib_load.return_value = mock_model

        # Mock the model registry to return the model path
        self.model_registry_mock.get_active_model.return_value = self.sample_model_info

        # Set up a feedback_service mock
        feedback_service_mock = MagicMock()
        self.prediction_service.feedback_service = feedback_service_mock

        # Act
        prediction = self.prediction_service.predict_with_feedback(
            model_name=model_name,
            input_data=self.sample_input,
            actual_outcome=1,  # Actual outcome is failure, model predicted no failure
            feedback_type="false_negative",
        )

        # Assert
        assert prediction is not None
        assert prediction["prediction"] == 0  # Not failed

        # Verify feedback was recorded
        feedback_service_mock.record_feedback.assert_called_once()
        call_args = feedback_service_mock.record_feedback.call_args[1]
        assert call_args["model_name"] == model_name
        assert call_args["device_id"] == self.sample_input["device_id"]
        assert call_args["feedback_type"] == "false_negative"

    @patch("joblib.load")
    def test_get_prediction_explanation(self, mock_joblib_load):
        """Test getting an explanation for a prediction."""
        # Arrange
        model_name = "component_failure"

        # Create a mock model with SHAP-like explainer attribute
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1])  # Predicted failure
        mock_explainer = Mock()
        # Simulate SHAP values for features
        mock_explainer.shap_values.return_value = np.array([[0.01, 0.2, 0.05, 0.4]])
        mock_model.explainer = mock_explainer
        mock_joblib_load.return_value = mock_model

        # Mock the model registry to return the model path
        self.model_registry_mock.get_active_model.return_value = self.sample_model_info

        # Act
        explanation = self.prediction_service.get_prediction_explanation(
            model_name=model_name, input_data=self.sample_input
        )

        # Assert
        assert explanation is not None
        assert "feature_importance" in explanation
        assert "top_features" in explanation
        assert len(explanation["top_features"]) > 0
        assert (
            explanation["top_features"][0]["feature"] == "age_days"
        )  # Highest importance

    def test_predict_with_version(self):
        """Test making a prediction with a specific model version."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.26.001"  # Specific version

        # Create a mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0])  # Not failed
        mock_model.predict_proba.return_value = np.array(
            [[0.9, 0.1]]
        )  # 10% chance of failure

        # Mock loading the model
        with patch("joblib.load", return_value=mock_model):
            # Mock the model registry to return the model info for the specific version
            model_info = dict(self.sample_model_info)
            model_info["model_version"] = model_version
            self.model_registry_mock.get_model_info.return_value = model_info

            # Act
            prediction = self.prediction_service.predict_with_version(
                model_name=model_name,
                model_version=model_version,
                input_data=self.sample_input,
            )

            # Assert
            assert prediction is not None
            assert prediction["model_version"] == model_version
            assert prediction["prediction"] == 0  # Not failed
            assert prediction["probability"] == 0.1  # 10% chance of failure

            # Verify model registry was called with the specific version
            self.model_registry_mock.get_model_info.assert_called_once_with(
                model_name=model_name, model_version=model_version
            )
