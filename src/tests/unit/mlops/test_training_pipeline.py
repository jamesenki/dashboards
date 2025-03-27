"""
Tests for the MLOps model training pipeline.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.mlops.training_pipeline import ModelTrainingPipeline


class TestModelTrainingPipeline:
    """Test suite for the model training pipeline."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.feature_store_mock = MagicMock()
        self.model_registry_mock = MagicMock()
        self.db_mock = MagicMock()
        self.training_pipeline = ModelTrainingPipeline(
            self.feature_store_mock, 
            self.model_registry_mock,
            self.db_mock
        )
        
    def test_trigger_model_training(self):
        """Test triggering training for a model."""
        # Arrange
        model_name = "component_failure"
        training_data_start_date = datetime.now() - timedelta(days=90)
        training_data_end_date = datetime.now()
        
        # Mock feature store response
        self.feature_store_mock.get_training_dataset.return_value = [
            {"device_id": "wh-123", "temperature": 145, "pressure": 55, "age_days": 732},
            {"device_id": "wh-456", "temperature": 140, "pressure": 50, "age_days": 365}
        ]
        
        # Act
        job_id = self.training_pipeline.trigger_model_training(
            model_name=model_name,
            training_data_start_date=training_data_start_date,
            training_data_end_date=training_data_end_date,
            test_mode=True
        )
        
        # Assert
        assert job_id is not None
        self.feature_store_mock.get_training_dataset.assert_called_once()
        self.db_mock.execute.assert_called_once()
        
    def test_schedule_regular_training(self):
        """Test scheduling regular training for a model."""
        # Arrange
        model_name = "usage_patterns"
        schedule = "weekly"
        
        # Act
        self.training_pipeline.schedule_regular_training(
            model_name=model_name,
            schedule=schedule
        )
        
        # Assert
        self.db_mock.execute.assert_called_once()
        call_args = self.db_mock.execute.call_args[0][0]
        assert "INSERT INTO training_schedules" in str(call_args)
        
    def test_evaluate_model_performance(self):
        """Test evaluating model performance on a test dataset."""
        # Arrange
        model_name = "lifespan_estimation"
        model_version = "1.2.0"
        test_dataset_id = "test-data-123"
        
        # Mock evaluation results
        self.model_registry_mock.get_model_path.return_value = "/path/to/model"
        
        # Act
        metrics = self.training_pipeline.evaluate_model_performance(
            model_name=model_name,
            model_version=model_version,
            test_dataset_id=test_dataset_id
        )
        
        # Assert
        assert metrics is not None
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        self.model_registry_mock.get_model_path.assert_called_once()


import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from src.mlops.training_pipeline import ModelTrainingPipeline


class TestModelTrainingPipelineExtended(unittest.TestCase):
    def setUp(self):
        self.feature_store = Mock()
        self.model_registry = Mock()
        self.db = Mock()
        self.pipeline = ModelTrainingPipeline(
            feature_store=self.feature_store,
            model_registry=self.model_registry,
            db=self.db
        )
    
    def test_init(self):
        """Test that the pipeline initializes correctly"""
        self.assertEqual(self.pipeline.feature_store, self.feature_store)
        self.assertEqual(self.pipeline.model_registry, self.model_registry)
        self.assertEqual(self.pipeline.db, self.db)
        self.assertIsNotNone(self.pipeline._model_trainers)
    
    @patch('src.mlops.training_pipeline.threading')
    def test_trigger_model_training(self, mock_threading):
        """Test that trigger_model_training starts a thread and returns a job ID"""
        result = self.pipeline.trigger_model_training(
            model_name="component_failure",
            training_data_start_date=datetime(2024, 1, 1),
            training_data_end_date=datetime(2024, 3, 1)
        )
        
        # Assert that a thread was started
        self.assertTrue(mock_threading.Thread.called)
        # Assert that a job ID was returned
        self.assertIsNotNone(result)
        self.assertTrue(isinstance(result, str))
        
    def test_execute_training_job_invalid_model(self):
        """Test that _execute_training_job fails correctly for invalid model"""
        # Mock dependencies
        self.pipeline._update_job_status = Mock()
        
        # Execute with invalid model name
        self.pipeline._execute_training_job(
            job_id="test-job",
            model_name="invalid_model",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1)
        )
        
        # Assert job status was updated to failed
        self.pipeline._update_job_status.assert_called_with(
            "test-job", 
            "failed", 
            {"error": "No trainer available for model type: invalid_model"}
        )
    
    def test_execute_training_job_no_data(self):
        """Test that _execute_training_job fails correctly when no training data is available"""
        # Mock dependencies
        self.pipeline._update_job_status = Mock()
        self.pipeline._get_feature_names_for_model = Mock(return_value=["feature1", "feature2"])
        self.feature_store.get_training_dataset = Mock(return_value=[])
        
        # Execute
        self.pipeline._execute_training_job(
            job_id="test-job",
            model_name="component_failure",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1)
        )
        
        # Assert job status was updated to failed
        self.pipeline._update_job_status.assert_called_with(
            "test-job", 
            "failed", 
            {"error": "No training data available"}
        )

if __name__ == '__main__':
    unittest.main()