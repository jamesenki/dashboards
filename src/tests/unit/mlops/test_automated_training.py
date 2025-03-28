"""
Tests for the automated model training system.

These tests define the expected behaviors for the automated model
training functionality following TDD principles.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, ANY
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.mlops.automated_training import AutomatedTrainingService
from security.secure_model_loader import SecureModelLoader


class TestAutomatedTrainingService:
    """
    Test suite for the AutomatedTrainingService which handles scheduled
    and automated model training.
    """
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock dependencies
        self.training_pipeline_mock = MagicMock()
        self.feature_store_mock = MagicMock()
        self.model_registry_mock = MagicMock()
        self.db_mock = MagicMock()
        self.scheduler_mock = MagicMock()
        self.secure_model_loader_mock = MagicMock(spec=SecureModelLoader)
        
        # Create service under test
        self.service = AutomatedTrainingService(
            training_pipeline=self.training_pipeline_mock,
            feature_store=self.feature_store_mock,
            model_registry=self.model_registry_mock,
            db=self.db_mock,
            scheduler=self.scheduler_mock,
            secure_model_loader=self.secure_model_loader_mock
        )
    
    def test_init(self):
        """Test proper initialization of service."""
        assert self.service.training_pipeline == self.training_pipeline_mock
        assert self.service.feature_store == self.feature_store_mock
        assert self.service.model_registry == self.model_registry_mock
        assert self.service.db == self.db_mock
        assert self.service.scheduler == self.scheduler_mock
        assert self.service.secure_model_loader == self.secure_model_loader_mock
    
    def test_schedule_model_training(self):
        """Test scheduling a model for regular training."""
        # Arrange
        model_name = "water_heater_failure_prediction"
        schedule = "daily"
        feature_set = ["temperature", "pressure", "vibration", "age_days"]
        training_window_days = 90
        
        # Act
        schedule_id = self.service.schedule_model_training(
            model_name=model_name,
            schedule=schedule,
            feature_set=feature_set,
            training_window_days=training_window_days
        )
        
        # Assert
        assert schedule_id is not None
        self.scheduler_mock.add_job.assert_called_once()
        self.db_mock.execute.assert_called_once()
    
    def test_start_training_job(self):
        """Test starting a training job from a schedule."""
        # Arrange
        schedule_id = str(uuid.uuid4())
        model_name = "water_heater_efficiency"
        feature_set = ["temperature", "energy_consumption", "water_usage"]
        training_window_days = 60
        
        # Mock database query result
        self.db_mock.fetch_one.return_value = {
            "id": schedule_id,
            "model_name": model_name,
            "feature_set": feature_set,
            "training_window_days": training_window_days,
            "active": True,
            "last_run": None
        }
        
        # Mock training pipeline
        job_id = str(uuid.uuid4())
        self.training_pipeline_mock.trigger_model_training.return_value = job_id
        
        # Act
        result = self.service.start_training_job(schedule_id)
        
        # Assert
        assert result == job_id
        self.db_mock.fetch_one.assert_called_once()
        self.training_pipeline_mock.trigger_model_training.assert_called_once()
        self.db_mock.execute.assert_called_once()  # Update last_run timestamp
    
    def test_detect_performance_drift(self):
        """Test detection of model performance drift requiring retraining."""
        # Arrange
        model_name = "component_lifespan"
        model_version = "1.0.0"
        threshold = 0.05  # 5% drift tolerance
        
        # Mock current performance metrics
        self.model_registry_mock.get_model_metrics.return_value = {
            "accuracy": 0.92,
            "precision": 0.90,
            "recall": 0.88,
            "f1_score": 0.89
        }
        
        # Mock recent predictions metrics (worse performance)
        self.db_mock.fetch_all.return_value = [
            {
                "timestamp": datetime.now() - timedelta(days=1),
                "metrics": {
                    "accuracy": 0.85,  # 7% drop, above threshold
                    "precision": 0.87,
                    "recall": 0.82,
                    "f1_score": 0.84
                }
            }
        ]
        
        # Act
        needs_retraining, metrics_diff = self.service.detect_performance_drift(
            model_name=model_name,
            model_version=model_version,
            threshold=threshold
        )
        
        # Assert
        assert needs_retraining is True
        assert metrics_diff["accuracy"] > threshold
        self.model_registry_mock.get_model_metrics.assert_called_once()
        self.db_mock.fetch_all.assert_called_once()
    
    def test_preprocess_training_data(self):
        """Test preprocessing of training data before model training."""
        # Arrange
        raw_data = [
            {"device_id": "wh-123", "temperature": 150, "pressure": None, "age_days": 732},
            {"device_id": "wh-456", "temperature": 145, "pressure": 60, "age_days": 365},
            {"device_id": "wh-789", "temperature": None, "pressure": 55, "age_days": 180},
        ]
        self.feature_store_mock.get_training_dataset.return_value = raw_data
        
        # Act
        processed_data = self.service.preprocess_training_data(
            feature_set=["temperature", "pressure", "age_days"],
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        
        # Assert
        assert len(processed_data) <= len(raw_data)  # May be fewer rows due to filtering
        # No None values in processed data
        for record in processed_data:
            assert all(value is not None for value in record.values())
        self.feature_store_mock.get_training_dataset.assert_called_once()
    
    def test_select_best_model_configuration(self):
        """Test selection of best model configuration through hyperparameter tuning."""
        # Arrange
        model_name = "water_heater_maintenance"
        training_data = [
            {"temperature": 145, "pressure": 55, "age_days": 732, "maintenance_needed": 1},
            {"temperature": 140, "pressure": 50, "age_days": 365, "maintenance_needed": 0}
        ]
        test_data = [
            {"temperature": 148, "pressure": 58, "age_days": 700, "maintenance_needed": 1},
            {"temperature": 142, "pressure": 52, "age_days": 400, "maintenance_needed": 0}
        ]
        
        # Multiple model configs to test
        model_configs = [
            {"algorithm": "random_forest", "max_depth": 10, "n_estimators": 100},
            {"algorithm": "gradient_boosting", "max_depth": 5, "learning_rate": 0.1},
            {"algorithm": "svm", "kernel": "rbf", "C": 1.0}
        ]
        
        # Mock training results
        self.training_pipeline_mock.train_and_evaluate_model_configuration.side_effect = [
            {"accuracy": 0.88, "precision": 0.86, "recall": 0.85, "f1_score": 0.85},
            {"accuracy": 0.92, "precision": 0.91, "recall": 0.90, "f1_score": 0.90},  # Best
            {"accuracy": 0.85, "precision": 0.84, "recall": 0.83, "f1_score": 0.83}
        ]
        
        # Act
        best_config, best_metrics = self.service.select_best_model_configuration(
            model_name=model_name,
            training_data=training_data,
            test_data=test_data,
            model_configs=model_configs
        )
        
        # Assert
        assert best_config == model_configs[1]  # Should select gradient_boosting
        assert best_metrics["accuracy"] == 0.92
        assert self.training_pipeline_mock.train_and_evaluate_model_configuration.call_count == len(model_configs)
    
    def test_deploy_model_securely(self):
        """Test secure deployment of a trained model using SecureModelLoader."""
        # Arrange
        model_name = "water_heater_failure_prediction"
        model_version = "2.0.0"
        model_path = f"/models/{model_name}/{model_version}"
        
        # Mock model registry
        self.model_registry_mock.get_model_path.return_value = model_path
        
        # Mock secure model loader
        self.secure_model_loader_mock.load.return_value = MagicMock()
        
        # Act
        deployed_model = self.service.deploy_model_securely(
            model_name=model_name,
            model_version=model_version
        )
        
        # Assert
        assert deployed_model is not None
        self.model_registry_mock.get_model_path.assert_called_once_with(model_name, model_version)
        self.secure_model_loader_mock.load.assert_called_once_with(model_path)
    
    def test_handle_feedback_based_retraining(self):
        """Test retraining model based on collected feedback."""
        # Arrange
        model_name = "water_heater_efficiency"
        model_version = "1.0.0"
        feedback_threshold = 50  # Number of feedback entries to trigger retraining
        
        # Mock feedback database query
        self.db_mock.fetch_all.return_value = [{"id": i} for i in range(60)]  # 60 feedback entries
        
        # Mock training job
        job_id = str(uuid.uuid4())
        self.training_pipeline_mock.trigger_model_training.return_value = job_id
        
        # Act
        result = self.service.handle_feedback_based_retraining(
            model_name=model_name,
            model_version=model_version,
            feedback_threshold=feedback_threshold
        )
        
        # Assert
        assert result == job_id
        self.db_mock.fetch_all.assert_called_once()
        self.training_pipeline_mock.trigger_model_training.assert_called_once()
    
    def test_get_training_schedules(self):
        """Test retrieval of all model training schedules."""
        # Arrange
        expected_schedules = [
            {
                "id": str(uuid.uuid4()),
                "model_name": "water_heater_failure_prediction",
                "schedule": "daily",
                "active": True,
                "feature_set": ["temperature", "pressure", "age_days"],
                "training_window_days": 90,
                "last_run": datetime.now() - timedelta(days=1)
            },
            {
                "id": str(uuid.uuid4()),
                "model_name": "water_heater_efficiency",
                "schedule": "weekly",
                "active": True,
                "feature_set": ["temperature", "energy_consumption", "water_usage"],
                "training_window_days": 180,
                "last_run": datetime.now() - timedelta(days=5)
            }
        ]
        self.db_mock.fetch_all.return_value = expected_schedules
        
        # Act
        schedules = self.service.get_training_schedules()
        
        # Assert
        assert schedules == expected_schedules
        self.db_mock.fetch_all.assert_called_once()
    
    def test_toggle_training_schedule(self):
        """Test enabling/disabling a training schedule."""
        # Arrange
        schedule_id = str(uuid.uuid4())
        
        # Act - Disable
        self.service.toggle_training_schedule(schedule_id, active=False)
        
        # Assert
        self.db_mock.execute.assert_called_once()
        call_args = self.db_mock.execute.call_args
        
        # Check that the query contains expected substrings
        query_str = str(call_args[0][0]).lower()
        assert "update training_schedules" in query_str
        assert any([
            "active = false" in query_str,  # SQL-style boolean
            "active=false" in query_str,     # No space format
            "active = ?" in query_str        # Parameterized query
        ])
    
    def test_handle_drift_detection_job(self):
        """Test the handling of a scheduled drift detection job."""
        # Arrange
        models_to_check = [
            {"name": "water_heater_failure_prediction", "version": "1.0.0", "threshold": 0.05},
            {"name": "water_heater_efficiency", "version": "2.0.0", "threshold": 0.1}
        ]
        
        # Mock drift detection results
        self.service.detect_performance_drift = MagicMock()
        self.service.detect_performance_drift.side_effect = [
            (True, {"accuracy": 0.06}),  # First model needs retraining
            (False, {"accuracy": 0.03})   # Second model is fine
        ]
        
        # Mock training job
        job_id = str(uuid.uuid4())
        self.training_pipeline_mock.trigger_model_training.return_value = job_id
        
        # Act
        retrained_models = self.service.handle_drift_detection_job(models_to_check)
        
        # Assert
        assert len(retrained_models) == 1
        assert retrained_models[0]["name"] == "water_heater_failure_prediction"
        assert retrained_models[0]["job_id"] == job_id
        assert self.service.detect_performance_drift.call_count == len(models_to_check)
        self.training_pipeline_mock.trigger_model_training.assert_called_once()
