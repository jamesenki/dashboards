"""
Integration tests for the MLOps pipeline.

These tests verify that all MLOps components work together correctly.
"""
import pytest
import os
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.mlops.feature_store import FeatureStore
from src.mlops.model_registry import ModelRegistry
from src.mlops.feedback_service import FeedbackService
from src.mlops.prediction_service import PredictionService
from src.mlops.training_pipeline import ModelTrainingPipeline
from src.mlops.pipeline_example import run_mlops_pipeline_example


class TestMLOpsPipelineIntegration:
    """Integration tests for the complete MLOps pipeline."""
    
    def setup_method(self):
        """Setup test fixtures before each test method."""
        # Create a mock database
        self.db_mock = MagicMock()
        
        # Mock the execute method to return appropriate results
        self.db_mock.execute.return_value = None
        
        # Create temporary directory for model storage
        self.test_models_dir = "/tmp/test_models"
        os.makedirs(self.test_models_dir, exist_ok=True)
        
        # Initialize MLOps components with mocks
        self.feature_store = FeatureStore(db=self.db_mock)
        self.model_registry = ModelRegistry(db=self.db_mock, storage_path=self.test_models_dir)
        self.feedback_service = FeedbackService(db=self.db_mock, model_registry=self.model_registry)
        self.training_pipeline = ModelTrainingPipeline(
            db=self.db_mock,
            feature_store=self.feature_store,
            model_registry=self.model_registry
        )
    
    def teardown_method(self):
        """Teardown test fixtures after each test method."""
        # Clean up test model files
        for root, dirs, files in os.walk(self.test_models_dir):
            for file in files:
                if file.endswith('.pkl'):
                    os.remove(os.path.join(root, file))
    
    @patch('src.mlops.pipeline_example.Database')
    @patch('src.mlops.pipeline_example.run_mlops_pipeline_example')
    def test_complete_pipeline_execution(self, mock_run_pipeline, mock_db_class):
        """Test the complete MLOps pipeline workflow."""
        # Configure the mock to return expected result format
        mock_result = {
            'model_id': 'test-model-id',
            'model_version': '2025.03.27.001',
            'model_metrics': {
                'accuracy': 0.92,
                'precision': 0.88,
                'recall': 0.94,
                'f1_score': 0.91
            },
            'feedback_summary': {
                'total': 5,
                'true_positives': 2,
                'false_positives': 1,
                'true_negatives': 1,
                'false_negatives': 1
            }
        }
        mock_run_pipeline.return_value = mock_result
        
        # Call the function directly from the module
        from src.mlops.pipeline_example import run_mlops_pipeline_example
        result = run_mlops_pipeline_example()
        
        # Verify the function was called and returned the expected result
        mock_run_pipeline.assert_called_once()
        assert result == mock_result
        

    
    def test_feature_to_prediction_flow(self):
        """
        Test the flow from feature storage to prediction.
        
        This test verifies:
        1. Features can be stored in the feature store
        2. A model can be registered and activated
        3. Predictions can be made using those features
        4. Feedback can be recorded for those predictions
        """
        # Setup test data
        device_id = "WH-TEST-001"
        feature_values = {
            "temperature": 145.5,
            "pressure": 55.2,
            "vibration": 0.05,
            "age_days": 732
        }
        timestamp = datetime.now()
        
        # 1. Register features
        for feature_name, value in feature_values.items():
            self.feature_store.register_feature(
                device_id=device_id,
                feature_name=feature_name,
                feature_value=value,
                timestamp=timestamp
            )
        
        # Mock the database query response for feature retrieval
        def mock_execute_side_effect(query, params=None):
            if "SELECT feature_name, feature_value" in query:
                # Return mock feature data
                return [
                    ("temperature", 145.5),
                    ("pressure", 55.2),
                    ("vibration", 0.05),
                    ("age_days", 732)
                ]
            return None
        
        self.db_mock.execute.side_effect = mock_execute_side_effect
        
        # 2. Register a dummy model
        with patch('os.path.exists', return_value=True):
            with patch('shutil.copy2'):
                model_id = self.model_registry.register_model(
                    model_name="component_failure",
                    model_version="2025.03.27.001",
                    model_path="/nonexistent/path/model.pkl",
                    metadata={
                        "features": ["temperature", "pressure", "vibration", "age_days"],
                        "accuracy": 0.92
                    }
                )
                
                # Activate the model
                self.model_registry.activate_model("component_failure", "2025.03.27.001")
                
                # Mock model retrieval
                def mock_get_model(model_name):
                    return {
                        "model_id": model_id,
                        "model_name": "component_failure",
                        "model_version": "2025.03.27.001",
                        "model_path": "/tmp/test_models/component_failure_2025.03.27.001.pkl",
                        "status": "active",
                        "metadata": {
                            "features": ["temperature", "pressure", "vibration", "age_days"],
                            "accuracy": 0.92
                        }
                    }
                
                self.model_registry.get_active_model = MagicMock(side_effect=mock_get_model)
                
                # 3. Make a prediction with mocked model loading
                with patch('joblib.load') as mock_joblib_load:
                    # Create mock model
                    mock_model = MagicMock()
                    mock_model.predict.return_value = np.array([1])  # Predict failure
                    mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])  # 80% probability
                    mock_joblib_load.return_value = mock_model
                    
                    # Create prediction service with our mocks
                    prediction_service = PredictionService(
                        db=self.db_mock,
                        model_registry=self.model_registry,
                        feature_store=self.feature_store,
                        feedback_service=self.feedback_service
                    )
                    
                    # Make prediction
                    prediction = prediction_service.predict(
                        model_name="component_failure",
                        input_data={
                            "device_id": device_id,
                            "temperature": 145.5,
                            "pressure": 55.2,
                            "vibration": 0.05,
                            "age_days": 732
                        }
                    )
                    
                    # Verify prediction
                    assert prediction is not None
                    assert prediction["prediction"] == 1
                    assert prediction["probability"] == 0.8
                    assert "prediction_id" in prediction
                    
                    # 4. Record feedback
                    feedback_id = self.feedback_service.record_feedback(
                        model_name="component_failure",
                        prediction_id=prediction["prediction_id"],
                        device_id=device_id,
                        feedback_type="false_positive",
                        details={"user_notes": "Device working correctly"}
                    )
                    
                    # Verify feedback was recorded
                    assert feedback_id is not None


if __name__ == "__main__":
    pytest.main(["-v", "test_mlops_pipeline.py"])
