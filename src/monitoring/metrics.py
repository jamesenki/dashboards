"""
Metric models for model monitoring.

This module defines the data models for tracking and analyzing
machine learning model performance metrics.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of model performance metrics."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    MSE = "mse"  # Mean Squared Error
    RMSE = "rmse"  # Root Mean Squared Error
    MAE = "mae"  # Mean Absolute Error
    R2 = "r2"  # R-squared score
    INFERENCE_TIME = "inference_time"  # Inference latency


class ModelMetric(BaseModel):
    """
    Performance metric for a machine learning model.
    """

    id: Optional[str] = None
    model_id: str
    model_version: str
    metric_name: str
    metric_value: float
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class MetricHistory(BaseModel):
    """
    History of a specific metric for a model.
    """

    model_id: str
    model_version: str
    metric_name: str
    values: List[Dict[str, Any]]  # List of {timestamp, value} dictionaries

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class MetricSummary(BaseModel):
    """
    Summary statistics for a metric.
    """

    metric_name: str
    latest_value: float
    min_value: float
    max_value: float
    avg_value: float
    std_dev: Optional[float] = None
    trend: Optional[str] = None  # "improving", "declining", "stable", "unknown"

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
