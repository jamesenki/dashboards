"""
Example demonstrating the complete MLOps pipeline.
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.db.database import Database  # Adjust based on your actual database connector
from src.mlops.feature_store import FeatureStore
from src.mlops.feedback_service import FeedbackService
from src.mlops.model_registry import ModelRegistry
from src.mlops.prediction_service import PredictionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_mlops_pipeline_example():
    """
    Demonstrates a complete MLOps pipeline:
    1. Feature preparation using FeatureStore
    2. Model registration using ModelRegistry
    3. Making predictions using PredictionService
    4. Recording feedback using FeedbackService
    5. Analyzing feedback patterns
    """
    # Initialize database connection
    db = Database()  # Adjust based on your actual implementation

    # Initialize MLOps components
    feature_store = FeatureStore(db)
    model_registry = ModelRegistry(db, storage_path="/tmp/model_registry")
    feedback_service = FeedbackService(db)
    prediction_service = PredictionService(
        db=db,
        model_registry=model_registry,
        feature_store=feature_store,
        feedback_service=feedback_service,
    )

    # Step 1: Feature Preparation
    logger.info("Step 1: Preparing features for model training")
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()

    # Register custom feature transformers
    feature_store.register_feature_transformer(
        "temperature_pressure_ratio", lambda df: df["temperature"] / df["pressure"]
    )

    # Get training dataset with transformed features
    features = ["temperature", "pressure", "temperature_pressure_ratio", "age_days"]
    training_data = feature_store.get_training_dataset(
        features=features, start_date=start_date, end_date=end_date
    )
    logger.info(f"Retrieved {len(training_data)} training examples")

    # Step 2: Model Registration (simulated - in a real scenario you would train a model first)
    logger.info("Step 2: Registering trained model")
    model_name = "component_failure"
    model_version = datetime.now().strftime("%Y.%m.%d.001")

    # Simulate model training and saving
    # In a real scenario, you would train a model and save it to a file
    import joblib
    import sklearn
    from sklearn.ensemble import RandomForestClassifier

    # Simulate training data and labels
    X = np.random.rand(100, len(features))
    y = np.random.randint(0, 2, 100)  # Binary classification: 0=no failure, 1=failure

    # Train a simple model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    # Save model to temporary location
    temp_model_path = "/tmp/temp_model.pkl"
    joblib.dump(model, temp_model_path)

    # Register model with metadata
    model_id = model_registry.register_model(
        model_name=model_name,
        model_version=model_version,
        model_path=temp_model_path,
        metadata={
            "features": features,
            "accuracy": 0.92,
            "precision": 0.88,
            "training_date": datetime.now().isoformat(),
            "training_data_size": len(training_data),
        },
    )
    logger.info(f"Registered model with ID: {model_id}")

    # Activate the model
    model_registry.activate_model(model_name, model_version)
    logger.info(f"Activated model {model_name} version {model_version}")

    # Step 3: Making Predictions
    logger.info("Step 3: Making predictions with the model")
    # Sample input data for a device
    input_data = {
        "device_id": "WH-1001",
        "temperature": 65.5,
        "pressure": 32.1,
        "age_days": 720,
    }

    # Make a prediction
    prediction = prediction_service.predict(
        model_name=model_name, input_data=input_data
    )
    logger.info(f"Prediction for device {input_data['device_id']}: {prediction}")

    # Make batch predictions for multiple devices
    batch_data = [
        {
            "device_id": "WH-1001",
            "temperature": 65.5,
            "pressure": 32.1,
            "age_days": 720,
        },
        {
            "device_id": "WH-1002",
            "temperature": 78.3,
            "pressure": 34.5,
            "age_days": 980,
        },
        {
            "device_id": "WH-1003",
            "temperature": 68.2,
            "pressure": 33.0,
            "age_days": 540,
        },
    ]
    batch_predictions = prediction_service.batch_predict(
        model_name=model_name, batch_data=batch_data
    )
    logger.info(f"Made predictions for {len(batch_predictions)} devices")

    # Step 4: Recording Feedback
    logger.info("Step 4: Recording user feedback on predictions")
    # Simulate user feedback on a prediction
    feedback_service.record_feedback(
        model_name=model_name,
        prediction_id=prediction["prediction_id"],
        device_id=input_data["device_id"],
        feedback_type="false_positive",
        details={
            "user_notes": "Device is working correctly",
            "actual_status": "operational",
        },
    )
    logger.info(f"Recorded feedback for prediction {prediction['prediction_id']}")

    # Step 5: Analyzing Feedback Patterns
    logger.info("Step 5: Analyzing feedback patterns")
    # Get all feedback for the model
    model_feedback = feedback_service.get_feedback_for_model(model_name)
    logger.info(f"Retrieved {len(model_feedback)} feedback records")

    # Analyze feedback patterns
    feedback_patterns = feedback_service.analyze_feedback_patterns(model_name)
    logger.info(f"Found feedback patterns across {len(feedback_patterns)} devices")

    # Get feedback summary
    feedback_summary = feedback_service.get_feedback_summary(model_name)
    logger.info(f"Feedback summary: {feedback_summary}")

    logger.info("MLOps pipeline example completed successfully")
    return {
        "model_id": model_id,
        "predictions": batch_predictions,
        "feedback_summary": feedback_summary,
    }


if __name__ == "__main__":
    results = run_mlops_pipeline_example()
    print(f"Pipeline execution complete. Results: {results}")
