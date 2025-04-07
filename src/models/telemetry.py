"""
Telemetry data models for the IoTSphere platform.

This module defines the data structures for device telemetry data,
which is used to track real-time and historical device metrics.
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AggregationType(str, Enum):
    """Types of telemetry data aggregation"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TelemetryMetadata(BaseModel):
    """
    Metadata for telemetry measurements
    
    Attributes:
        unit: The unit of measurement (e.g., celsius, psi, watts)
        sensor_id: Optional identifier for the specific sensor
        quality: Optional data quality indicator (0-100)
        tags: Optional key-value pairs for additional metadata
    """
    unit: str
    sensor_id: Optional[str] = None
    quality: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[Dict[str, Any]] = None


class TelemetryData(BaseModel):
    """
    Telemetry data model representing a single measurement
    
    Attributes:
        device_id: The ID of the device that produced the data
        metric: The type of measurement (e.g., temperature, pressure)
        value: The measured value
        timestamp: When the measurement was taken
        metadata: Additional information about the measurement
    """
    device_id: str
    metric: str
    value: float
    timestamp: datetime
    metadata: Optional[TelemetryMetadata] = None
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, value):
        """Parse string timestamps into datetime objects"""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
    
    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TelemetryBatch(BaseModel):
    """
    Batch of telemetry data points for bulk processing
    
    Attributes:
        device_id: The ID of the device that produced the data
        metrics: List of telemetry data points
    """
    device_id: str
    metrics: List[TelemetryData]


class TelemetryQuery(BaseModel):
    """
    Query parameters for retrieving telemetry data
    
    Attributes:
        device_id: The device to query data for
        metrics: List of metrics to retrieve
        start_time: Start of the time range
        end_time: End of the time range
        limit: Maximum number of records to return
        aggregation: Optional aggregation type
    """
    device_id: str
    metrics: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = Field(None, gt=0)
    aggregation: Optional[AggregationType] = None


class TelemetrySubscription(BaseModel):
    """
    Subscription parameters for real-time telemetry updates
    
    Attributes:
        device_id: The device to subscribe to
        metrics: List of metrics to receive updates for
        min_interval: Minimum interval between updates (seconds)
    """
    device_id: str
    metrics: List[str]
    min_interval: Optional[float] = Field(None, ge=0.1)  # Minimum 100ms
