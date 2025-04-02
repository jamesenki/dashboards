"""
MLOps integration for predictions module.

Provides infrastructure for model versioning, deployment, monitoring and experiment tracking.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from src.predictions.interfaces import IPredictionModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Model registry for tracking and versioning prediction models.

    Handles model metadata storage, versioning, and retrieval.
    """

    def __init__(self, registry_path: str = "models/registry"):
        """
        Initialize the model registry.

        Args:
            registry_path: Path to the model registry directory
        """
        self.registry_path = registry_path
        os.makedirs(registry_path, exist_ok=True)

    def register_model(
        self,
        model: IPredictionModel,
        model_path: str,
        model_metrics: Dict[str, Any],
        prediction_type: str,
        version: str,
    ) -> str:
        """
        Register a model in the registry.

        Args:
            model: The model to register
            model_path: Path to the serialized model
            model_metrics: Dictionary of model performance metrics
            prediction_type: Type of prediction the model makes
            version: Model version

        Returns:
            Model ID in the registry
        """
        model_id = (
            f"{prediction_type}-{version}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # Get model info
        model_info = model.get_model_info()

        # Prepare metadata
        metadata = {
            "id": model_id,
            "prediction_type": prediction_type,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "model_path": model_path,
            "metrics": model_metrics,
            "info": model_info,
        }

        # Save metadata
        metadata_path = os.path.join(self.registry_path, f"{model_id}.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Registered model {model_id} in registry")
        return model_id

    def get_model_metadata(self, model_id: str) -> Dict[str, Any]:
        """
        Get metadata for a registered model.

        Args:
            model_id: Model ID in the registry

        Returns:
            Model metadata

        Raises:
            FileNotFoundError: If model is not found in registry
        """
        metadata_path = os.path.join(self.registry_path, f"{model_id}.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Model {model_id} not found in registry")

        with open(metadata_path, "r") as f:
            return json.load(f)

    def list_models(
        self, prediction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List registered models.

        Args:
            prediction_type: Optional filter by prediction type

        Returns:
            List of model metadata
        """
        models = []

        for filename in os.listdir(self.registry_path):
            if filename.endswith(".json"):
                file_path = os.path.join(self.registry_path, filename)
                with open(file_path, "r") as f:
                    metadata = json.load(f)

                if (
                    prediction_type is None
                    or metadata.get("prediction_type") == prediction_type
                ):
                    models.append(metadata)

        return models

    def get_latest_model(self, prediction_type: str) -> Dict[str, Any]:
        """
        Get the latest version of a model by prediction type.

        Args:
            prediction_type: Type of prediction

        Returns:
            Model metadata

        Raises:
            ValueError: If no models found for the given prediction type
        """
        models = self.list_models(prediction_type)

        if not models:
            raise ValueError(f"No models found for prediction type: {prediction_type}")

        # Sort by created_at (latest first)
        models.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return models[0]


class ExperimentTracker:
    """
    Track machine learning experiments.

    Records hyperparameters, metrics, artifacts, and other experiment details.
    """

    def __init__(self, experiments_path: str = "experiments"):
        """
        Initialize the experiment tracker.

        Args:
            experiments_path: Path to the experiments directory
        """
        self.experiments_path = experiments_path
        os.makedirs(experiments_path, exist_ok=True)

    def start_experiment(
        self, name: str, prediction_type: str, config: Dict[str, Any]
    ) -> str:
        """
        Start a new experiment.

        Args:
            name: Experiment name
            prediction_type: Type of prediction
            config: Experiment configuration including hyperparameters

        Returns:
            Experiment ID
        """
        experiment_id = f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Prepare experiment metadata
        metadata = {
            "id": experiment_id,
            "name": name,
            "prediction_type": prediction_type,
            "started_at": datetime.now().isoformat(),
            "status": "running",
            "config": config,
            "metrics": {},
            "artifacts": [],
        }

        # Save metadata
        experiment_dir = os.path.join(self.experiments_path, experiment_id)
        os.makedirs(experiment_dir, exist_ok=True)

        metadata_path = os.path.join(experiment_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Started experiment {experiment_id}")
        return experiment_id

    def log_metrics(self, experiment_id: str, metrics: Dict[str, Any]) -> None:
        """
        Log metrics for an experiment.

        Args:
            experiment_id: Experiment ID
            metrics: Dictionary of metrics

        Raises:
            FileNotFoundError: If experiment is not found
        """
        experiment_dir = os.path.join(self.experiments_path, experiment_id)
        metadata_path = os.path.join(experiment_dir, "metadata.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Experiment {experiment_id} not found")

        # Load current metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Update metrics
        metadata["metrics"].update(metrics)

        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Logged metrics for experiment {experiment_id}: {metrics}")

    def log_artifact(
        self, experiment_id: str, artifact_path: str, description: str
    ) -> None:
        """
        Log an artifact for an experiment.

        Args:
            experiment_id: Experiment ID
            artifact_path: Path to the artifact
            description: Description of the artifact

        Raises:
            FileNotFoundError: If experiment is not found
        """
        experiment_dir = os.path.join(self.experiments_path, experiment_id)
        metadata_path = os.path.join(experiment_dir, "metadata.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Experiment {experiment_id} not found")

        # Load current metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Add artifact
        artifact = {
            "path": artifact_path,
            "description": description,
            "logged_at": datetime.now().isoformat(),
        }

        metadata["artifacts"].append(artifact)

        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Logged artifact for experiment {experiment_id}: {artifact_path}")

    def complete_experiment(
        self, experiment_id: str, status: str = "completed"
    ) -> None:
        """
        Mark an experiment as completed.

        Args:
            experiment_id: Experiment ID
            status: Final status (completed, failed, etc.)

        Raises:
            FileNotFoundError: If experiment is not found
        """
        experiment_dir = os.path.join(self.experiments_path, experiment_id)
        metadata_path = os.path.join(experiment_dir, "metadata.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Experiment {experiment_id} not found")

        # Load current metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Update status
        metadata["status"] = status
        metadata["completed_at"] = datetime.now().isoformat()

        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Completed experiment {experiment_id} with status: {status}")


class ModelMonitoring:
    """
    Monitor deployed prediction models.

    Tracks prediction quality, data drift, and system performance.
    """

    def __init__(self, monitoring_path: str = "monitoring"):
        """
        Initialize the model monitoring system.

        Args:
            monitoring_path: Path to the monitoring directory
        """
        self.monitoring_path = monitoring_path
        os.makedirs(monitoring_path, exist_ok=True)

    def log_prediction(
        self,
        model_id: str,
        prediction_id: str,
        features: Dict[str, Any],
        prediction: Dict[str, Any],
        prediction_time_ms: float,
    ) -> None:
        """
        Log a prediction for monitoring.

        Args:
            model_id: Model ID
            prediction_id: Unique ID for this prediction
            features: Features used for the prediction
            prediction: Prediction result
            prediction_time_ms: Time taken to make the prediction in milliseconds
        """
        log_dir = os.path.join(self.monitoring_path, model_id)
        os.makedirs(log_dir, exist_ok=True)

        # Create log entry
        log_entry = {
            "prediction_id": prediction_id,
            "timestamp": datetime.now().isoformat(),
            "features": features,
            "prediction": prediction,
            "prediction_time_ms": prediction_time_ms,
        }

        # Append to log file
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_ground_truth(
        self, model_id: str, prediction_id: str, ground_truth: Any
    ) -> None:
        """
        Log ground truth for a previous prediction.

        Args:
            model_id: Model ID
            prediction_id: Prediction ID
            ground_truth: Actual outcome
        """
        truth_dir = os.path.join(self.monitoring_path, model_id, "ground_truth")
        os.makedirs(truth_dir, exist_ok=True)

        # Create truth entry
        truth_entry = {
            "prediction_id": prediction_id,
            "timestamp": datetime.now().isoformat(),
            "ground_truth": ground_truth,
        }

        # Append to truth file
        truth_file = os.path.join(
            truth_dir, f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        with open(truth_file, "a") as f:
            f.write(json.dumps(truth_entry) + "\n")

    def compute_metrics(self, model_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Compute performance metrics for a model.

        Args:
            model_id: Model ID
            days: Number of days of data to analyze

        Returns:
            Dictionary of performance metrics
        """
        # This is a placeholder for actual metric computation
        # In a real implementation, this would analyze prediction logs and ground truth

        return {
            "model_id": model_id,
            "period": f"last {days} days",
            "computed_at": datetime.now().isoformat(),
            "metrics": {
                "accuracy": 0.92,
                "precision": 0.88,
                "recall": 0.95,
                "f1_score": 0.91,
                "avg_prediction_time_ms": 45.3,
                "prediction_count": 1253,
                "data_drift_score": 0.12,
            },
        }

    def detect_data_drift(self, model_id: str) -> Dict[str, Any]:
        """
        Detect data drift for a model.

        Args:
            model_id: Model ID

        Returns:
            Dictionary with drift detection results
        """
        # This is a placeholder for actual drift detection
        # In a real implementation, this would compare feature distributions

        return {
            "model_id": model_id,
            "detected_at": datetime.now().isoformat(),
            "drift_detected": False,
            "drift_metrics": {
                "feature_drift": {
                    "temperature": 0.05,
                    "pressure": 0.12,
                    "energy_usage": 0.08,
                    "flow_rate": 0.03,
                },
                "overall_drift_score": 0.07,
            },
        }


class MLOpsService:
    """
    Orchestrate MLOps functionality for prediction models.

    Provides a unified interface to MLOps components.
    """

    def __init__(
        self,
        model_registry: ModelRegistry,
        experiment_tracker: ExperimentTracker,
        model_monitoring: ModelMonitoring,
    ):
        """
        Initialize the MLOps service.

        Args:
            model_registry: Model registry instance
            experiment_tracker: Experiment tracker instance
            model_monitoring: Model monitoring instance
        """
        self.model_registry = model_registry
        self.experiment_tracker = experiment_tracker
        self.model_monitoring = model_monitoring

    def track_prediction(
        self,
        model_id: str,
        device_id: str,
        features: Dict[str, Any],
        prediction_result: Dict[str, Any],
        execution_time_ms: float,
    ) -> str:
        """
        Track a prediction for monitoring purposes.

        Args:
            model_id: Model ID
            device_id: Device ID
            features: Features used for prediction
            prediction_result: Prediction result
            execution_time_ms: Execution time in milliseconds

        Returns:
            Prediction tracking ID
        """
        prediction_id = (
            f"{model_id}-{device_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        self.model_monitoring.log_prediction(
            model_id=model_id,
            prediction_id=prediction_id,
            features=features,
            prediction=prediction_result,
            prediction_time_ms=execution_time_ms,
        )

        return prediction_id

    def register_feedback(
        self, prediction_id: str, model_id: str, feedback: Dict[str, Any]
    ) -> None:
        """
        Register feedback for a prediction.

        Args:
            prediction_id: Prediction ID
            model_id: Model ID
            feedback: Feedback data
        """
        # Log ground truth if available
        if "ground_truth" in feedback:
            self.model_monitoring.log_ground_truth(
                model_id=model_id,
                prediction_id=prediction_id,
                ground_truth=feedback["ground_truth"],
            )

    def check_model_health(self, model_id: str) -> Dict[str, Any]:
        """
        Check the health of a deployed model.

        Args:
            model_id: Model ID

        Returns:
            Model health report
        """
        try:
            # Get model metadata
            metadata = self.model_registry.get_model_metadata(model_id)

            # Compute performance metrics
            metrics = self.model_monitoring.compute_metrics(model_id)

            # Check for data drift
            drift = self.model_monitoring.detect_data_drift(model_id)

            # Create health report
            health_report = {
                "model_id": model_id,
                "prediction_type": metadata.get("prediction_type"),
                "version": metadata.get("version"),
                "created_at": metadata.get("created_at"),
                "metrics": metrics.get("metrics", {}),
                "drift": drift.get("drift_metrics", {}),
                "health_status": "healthy",
                "recommendations": [],
            }

            # Check for potential issues
            if drift.get("drift_detected", False):
                health_report["health_status"] = "drifting"
                health_report["recommendations"].append(
                    "Data drift detected. Consider retraining the model."
                )

            metrics_dict = metrics.get("metrics", {})
            if metrics_dict.get("accuracy", 1.0) < 0.8:
                health_report["health_status"] = "degraded"
                health_report["recommendations"].append(
                    "Model accuracy has degraded. Investigate and consider retraining."
                )

            return health_report

        except Exception as e:
            logger.error(f"Error checking model health: {str(e)}")
            return {"model_id": model_id, "health_status": "unknown", "error": str(e)}
