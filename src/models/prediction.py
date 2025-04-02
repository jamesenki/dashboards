"""
Models for prediction functionality
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    """
    Result of a prediction operation
    """

    device_id: str = Field(..., description="ID of the device")
    prediction_type: str = Field(..., description="Type of prediction")
    prediction_time: datetime = Field(
        default_factory=datetime.now, description="Time when prediction was generated"
    )
    score: float = Field(..., description="Prediction score (0-100)")
    confidence: float = Field(..., description="Confidence level of prediction (0-100)")
    summary: str = Field(..., description="Summary of prediction")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional prediction details"
    )
    factors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Contributing factors to the prediction"
    )
    recommended_actions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recommended actions based on prediction"
    )
