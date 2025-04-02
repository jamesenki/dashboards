"""
API endpoints for predictions.

This module contains FastAPI endpoints for generating and retrieving predictions.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.predictions.interfaces import (
    IPredictionModel,
    PredictionResult,
    PredictionService,
)
from src.predictions.mlops.integration import MLOpsService


def create_prediction_router(prediction_service: PredictionService) -> APIRouter:
    """
    Create a FastAPI router for prediction endpoints.

    Args:
        prediction_service: The prediction service to use for predictions

    Returns:
        FastAPI router with prediction endpoints
    """
    router = APIRouter(tags=["Predictions"])

    @router.get("/types")
    def list_prediction_types():
        """List available prediction types."""
        return {"prediction_types": prediction_service.model_registry.list_models()}

    @router.post("/generate")
    async def generate_prediction(
        request: Dict[str, Any],
        background_tasks: BackgroundTasks,
        mlops_service: MLOpsService = Depends(get_mlops_service),
    ):
        """
        Generate a prediction for a device.

        Args:
            request: Prediction request containing device_id, prediction_type, and features
            background_tasks: FastAPI background tasks for async tracking
            mlops_service: MLOps service for tracking predictions

        Returns:
            Prediction result
        """
        device_id = request.get("device_id")
        prediction_type = request.get("prediction_type")
        features = request.get("features", {})
        model_version = request.get("model_version")

        if not device_id or not prediction_type or not features:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: device_id, prediction_type, and features are required",
            )

        try:
            # Track execution time
            start_time = datetime.now()

            # Generate prediction
            result = await prediction_service.generate_prediction(
                prediction_type=prediction_type,
                device_id=device_id,
                features=features,
                model_version=model_version,
            )

            # Calculate execution time
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Track prediction in background
            background_tasks.add_task(
                track_prediction,
                mlops_service=mlops_service,
                model_id=f"{prediction_type}-{model_version if model_version else 'latest'}",
                device_id=device_id,
                features=features,
                prediction_result=result.dict(),
                execution_time_ms=execution_time_ms,
            )

            return result

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error generating prediction: {str(e)}"
            )

    @router.get("/health/{model_id}")
    def get_model_health(
        model_id: str, mlops_service: MLOpsService = Depends(get_mlops_service)
    ):
        """
        Get health status for a deployed prediction model.

        Args:
            model_id: ID of the model to check
            mlops_service: MLOps service for checking model health

        Returns:
            Model health report
        """
        try:
            return mlops_service.check_model_health(model_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Model not found or error checking health: {str(e)}",
            )

    @router.get("/device/{device_id}")
    def get_device_predictions(device_id: str):
        """
        Get all predictions for a specific device.

        Args:
            device_id: ID of the device

        Returns:
            List of predictions for the device
        """
        try:
            # Currently a placeholder - in a real implementation, this would
            # retrieve predictions from a database
            return {"device_id": device_id, "predictions": []}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving predictions: {str(e)}"
            )

    return router


async def track_prediction(
    mlops_service: MLOpsService,
    model_id: str,
    device_id: str,
    features: Dict[str, Any],
    prediction_result: Dict[str, Any],
    execution_time_ms: float,
):
    """
    Track a prediction for monitoring.

    Args:
        mlops_service: MLOps service for tracking
        model_id: Model ID
        device_id: Device ID
        features: Features used for prediction
        prediction_result: Prediction result
        execution_time_ms: Execution time in milliseconds
    """
    try:
        mlops_service.track_prediction(
            model_id=model_id,
            device_id=device_id,
            features=features,
            prediction_result=prediction_result,
            execution_time_ms=execution_time_ms,
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error tracking prediction: {str(e)}")


def get_mlops_service():
    """
    Dependency for getting the MLOps service.

    Returns:
        MLOps service instance
    """
    # In a real implementation, this would be a singleton or dependency injection
    from src.predictions.mlops.integration import (
        ExperimentTracker,
        MLOpsService,
        ModelMonitoring,
        ModelRegistry,
    )

    model_registry = ModelRegistry()
    experiment_tracker = ExperimentTracker()
    model_monitoring = ModelMonitoring()

    return MLOpsService(
        model_registry=model_registry,
        experiment_tracker=experiment_tracker,
        model_monitoring=model_monitoring,
    )
