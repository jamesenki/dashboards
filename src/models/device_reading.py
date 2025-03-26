"""
Device reading model for IoT device sensor data.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DeviceReading(BaseModel):
    """Base model for device readings/sensor data"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time when reading was taken")
    metric_name: Optional[str] = Field(None, description="Name of the metric (if single-metric reading)")
    value: Optional[Any] = Field(None, description="Value of the metric (if single-metric reading)")
    unit: Optional[str] = Field(None, description="Unit of measurement (if applicable)")
    
    # Multi-metric fields for specific device types
    # Vending machine specific fields
    temperature: Optional[float] = Field(None, description="Temperature reading")
    power_consumption: Optional[float] = Field(None, description="Power consumption in watts")
    door_status: Optional[str] = Field(None, description="Door status (OPEN/CLOSED)")
    cash_level: Optional[float] = Field(None, description="Cash level in machine")
    sales_count: Optional[int] = Field(None, description="Number of sales in period")
    
    # Water heater specific fields
    pressure: Optional[float] = Field(None, description="Water pressure reading")
    flow_rate: Optional[float] = Field(None, description="Water flow rate")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reading to dictionary format, filtering out None values"""
        result = {}
        for key, value in self.model_dump().items():
            if value is not None:
                result[key] = value
        return result
