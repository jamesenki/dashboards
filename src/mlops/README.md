# IoTSphere MLOps System

This directory contains the implementation of the IoTSphere MLOps (Machine Learning Operations) system, which provides a complete pipeline for managing the machine learning lifecycle for IoT device predictions.

## System Components

The IoTSphere MLOps system consists of the following components:

### 1. FeatureStore ([feature_store.py](cci:7://file:///Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/src/mlops/feature_store.py:0:0-0:0))

The FeatureStore is responsible for:
- Managing training data for ML models
- Transforming raw data into ML-ready features
- Providing consistent feature engineering across training and prediction

### 2. ModelRegistry ([model_registry.py](cci:7://file:///Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/src/mlops/model_registry.py:0:0-0:0))

The ModelRegistry is responsible for:
- Storing and versioning ML models
- Managing model lifecycle (active, inactive, archived)
- Tracking model metadata and performance metrics
- Facilitating model comparison and selection

### 3. FeedbackService ([feedback.py](cci:7://file:///Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/src/mlops/feedback.py:0:0-0:0))

The FeedbackService is responsible for:
- Recording user feedback on model predictions
- Analyzing feedback patterns to identify problematic devices or common issues
- Generating feedback summaries for model performance monitoring
- Providing data for model retraining decisions

### 4. PredictionService ([prediction_service.py](cci:7://file:///Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/src/mlops/prediction_service.py:0:0-0:0))

The PredictionService is responsible for:
- Loading models from the registry
- Preprocessing input data
- Generating predictions
- Recording prediction details
- Providing explanation for predictions
- Handling batch prediction scenarios

## Usage Example

The `pipeline_example.py` file demonstrates a complete MLOps workflow using all components:

```python
from src.mlops.feature_store import FeatureStore
from src.mlops.model_registry import ModelRegistry
from src.mlops.feedback import FeedbackService
from src.mlops.prediction_service import PredictionService

# Initialize components
feature_store = FeatureStore(db)
model_registry = ModelRegistry(db, storage_path)
feedback_service = FeedbackService(db)
prediction_service = PredictionService(
    db=db,
    model_registry=model_registry,
    feature_store=feature_store,
    feedback_service=feedback_service
)

# Get training data from feature store
training_data = feature_store.get_training_dataset(
    features=["temperature", "pressure", "temperature_pressure_ratio", "age_days"],
    start_date=start_date,
    end_date=end_date
)

# Register and activate a model
model_id = model_registry.register_model(
    model_name="component_failure",
    model_version="2025.03.27.001",
    model_path="/path/to/model.pkl",
    metadata={"accuracy": 0.92, "features": [...]}
)
model_registry.activate_model("component_failure", "2025.03.27.001")

# Make predictions
prediction = prediction_service.predict(
    model_name="component_failure",
    input_data={"device_id": "WH-1001", "temperature": 65.5, ...}
)

# Record feedback
feedback_service.record_feedback(
    model_name="component_failure",
    prediction_id=prediction["prediction_id"],
    device_id="WH-1001",
    feedback_type="false_positive",
    details={"user_notes": "Device working correctly"}
)

# Analyze feedback patterns
patterns = feedback_service.analyze_feedback_patterns("component_failure")