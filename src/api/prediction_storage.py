"""
Prediction Storage API

This module provides endpoints for storing and retrieving water heater predictions,
enabling historical analysis and AI training capabilities.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Create router for prediction storage endpoints
router = APIRouter(prefix="/api/predictions", tags=["prediction-storage"])


# Models for prediction storage
class PredictionMetadata(BaseModel):
    """Metadata for stored predictions"""

    deviceId: str
    predictionType: str
    timestamp: str
    version: str = "1.0.0"


class StoredPrediction(BaseModel):
    """Model for a stored prediction with metadata"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: PredictionMetadata
    data: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PredictionRequest(BaseModel):
    """Model for a prediction storage request"""

    metadata: PredictionMetadata
    data: Optional[Dict[str, Any]] = {}


class PredictionResponse(BaseModel):
    """Response model for prediction operations"""

    success: bool
    message: str
    id: Optional[str] = None
    count: Optional[int] = None
    predictions: Optional[List[StoredPrediction]] = None


# Storage implementation
# For development, we'll use a simple file-based storage
# In production, this would be replaced with a database implementation
class PredictionStorage:
    """Handles the storage and retrieval of predictions"""

    def __init__(self):
        """Initialize the prediction storage"""
        # Create directory for storing predictions if it doesn't exist
        self.storage_dir = Path("./data/predictions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create device index file if it doesn't exist
        self.device_index_path = self.storage_dir / "device_index.json"
        if not self.device_index_path.exists():
            with open(self.device_index_path, "w") as f:
                json.dump({}, f)

    def store_prediction(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a prediction in the filesystem

        Args:
            prediction: The prediction data to store

        Returns:
            Dict containing operation result
        """
        try:
            # Generate a unique ID if not provided
            prediction_id = prediction.get("id", str(uuid.uuid4()))

            # Ensure prediction has required metadata
            if "metadata" not in prediction:
                raise ValueError("Prediction missing required metadata")

            # Add timestamp if not provided
            if "timestamp" not in prediction["metadata"]:
                prediction["metadata"]["timestamp"] = datetime.now().isoformat()

            # Create a StoredPrediction object
            stored_prediction = StoredPrediction(
                id=prediction_id,
                metadata=PredictionMetadata(**prediction["metadata"]),
                data=prediction.get("data", {}),
            )

            # Get device ID from metadata
            device_id = stored_prediction.metadata.deviceId
            prediction_type = stored_prediction.metadata.predictionType

            # Update device index
            self._update_device_index(device_id, prediction_id, prediction_type)

            # Save prediction to file
            prediction_path = self.storage_dir / f"{prediction_id}.json"
            with open(prediction_path, "w") as f:
                json.dump(stored_prediction.dict(), f, indent=2)

            return {
                "success": True,
                "message": f"Prediction {prediction_id} stored successfully",
                "id": prediction_id,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to store prediction: {str(e)}",
            }

    def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific prediction by ID

        Args:
            prediction_id: ID of the prediction to retrieve

        Returns:
            The prediction data if found, None otherwise
        """
        prediction_path = self.storage_dir / f"{prediction_id}.json"
        if not prediction_path.exists():
            return None

        try:
            with open(prediction_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def get_device_predictions(
        self,
        device_id: str,
        prediction_type: Optional[str] = None,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get predictions for a specific device

        Args:
            device_id: ID of the device
            prediction_type: Type of prediction to filter by
            limit: Maximum number of predictions to return
            start_date: Start date for filtering (ISO format)
            end_date: End date for filtering (ISO format)

        Returns:
            List of predictions for the device
        """
        try:
            # Load device index
            with open(self.device_index_path, "r") as f:
                device_index = json.load(f)

            # Check if device exists in index
            if device_id not in device_index:
                return []

            # Get prediction IDs for the device
            device_predictions = device_index[device_id]
            prediction_ids = []

            # Filter by prediction type if specified
            if prediction_type:
                for pred_type, ids in device_predictions.items():
                    if pred_type == prediction_type:
                        prediction_ids.extend(ids)
            else:
                # Get all prediction IDs for the device
                for pred_type, ids in device_predictions.items():
                    prediction_ids.extend(ids)

            # Sort predictions by timestamp (newest first)
            predictions = []
            for pred_id in prediction_ids:
                pred = self.get_prediction(pred_id)
                if pred:
                    predictions.append(pred)

            # Sort by timestamp
            predictions.sort(
                key=lambda x: x["metadata"]["timestamp"]
                if x and "metadata" in x
                else "",
                reverse=True,
            )

            # Apply date filtering if specified
            if start_date or end_date:
                filtered_predictions = []
                for pred in predictions:
                    timestamp = pred["metadata"]["timestamp"]
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                    filtered_predictions.append(pred)
                predictions = filtered_predictions

            # Apply limit
            return predictions[:limit]

        except Exception as e:
            print(f"Error retrieving device predictions: {str(e)}")
            return []

    def _update_device_index(
        self, device_id: str, prediction_id: str, prediction_type: str
    ):
        """
        Update the device index with a new prediction

        Args:
            device_id: ID of the device
            prediction_id: ID of the prediction
            prediction_type: Type of prediction
        """
        try:
            # Load current index
            with open(self.device_index_path, "r") as f:
                device_index = json.load(f)

            # Add device if not exists
            if device_id not in device_index:
                device_index[device_id] = {}

            # Add prediction type if not exists
            if prediction_type not in device_index[device_id]:
                device_index[device_id][prediction_type] = []

            # Add prediction ID to the list
            device_index[device_id][prediction_type].append(prediction_id)

            # Save updated index
            with open(self.device_index_path, "w") as f:
                json.dump(device_index, f, indent=2)

        except Exception as e:
            print(f"Error updating device index: {str(e)}")


# Create storage instance
prediction_storage = PredictionStorage()


# API Endpoints
@router.post("/store", response_model=PredictionResponse)
async def store_prediction(prediction: Dict[str, Any]) -> PredictionResponse:
    """
    Store a prediction in the database

    Args:
        prediction: The prediction data to store

    Returns:
        PredictionResponse with operation result
    """
    result = prediction_storage.store_prediction(prediction)
    return PredictionResponse(
        success=result["success"], message=result["message"], id=result.get("id")
    )


@router.get("/history/{device_id}", response_model=PredictionResponse)
async def get_device_predictions(
    device_id: str,
    type: Optional[str] = Query(None, description="Type of prediction to filter by"),
    limit: int = Query(10, description="Maximum number of predictions to return"),
    start_date: Optional[str] = Query(
        None, description="Start date for filtering (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date for filtering (ISO format)"
    ),
) -> PredictionResponse:
    """
    Get historical predictions for a device

    Args:
        device_id: ID of the device
        type: Type of prediction to filter by
        limit: Maximum number of predictions to return
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)

    Returns:
        PredictionResponse with list of predictions
    """
    predictions = prediction_storage.get_device_predictions(
        device_id=device_id,
        prediction_type=type,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )

    return PredictionResponse(
        success=True,
        message=f"Retrieved {len(predictions)} predictions for device {device_id}",
        count=len(predictions),
        predictions=predictions,
    )


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: str) -> PredictionResponse:
    """
    Get a specific prediction by ID

    Args:
        prediction_id: ID of the prediction to retrieve

    Returns:
        PredictionResponse with the prediction data
    """
    prediction = prediction_storage.get_prediction(prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=404, detail=f"Prediction {prediction_id} not found"
        )

    return PredictionResponse(
        success=True,
        message=f"Retrieved prediction {prediction_id}",
        predictions=[prediction],
    )
