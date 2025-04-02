"""
Polar Delight vending machine real-time operations models
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class FlavorInventory(BaseModel):
    """Flavor inventory data"""

    name: str = Field(..., description="Flavor name")
    value: int = Field(..., description="Current inventory level")


class GaugeData(BaseModel):
    """Gauge chart data model"""

    min: Union[float, str] = Field(0, description="Minimum value")
    max: Union[float, str] = Field(100, description="Maximum value")
    needleValue: float = Field(..., description="Current needle position (0-100)")


class AssetHealthData(BaseModel):
    """Asset health gauge data"""

    assetHealth: str = Field(..., description="Asset health value with unit")
    needleValue: float = Field(..., description="Current needle position (0-100)")


class FreezerTemperatureData(BaseModel):
    """Freezer temperature gauge data"""

    freezerTemperature: float = Field(..., description="Current freezer temperature")
    min: float = Field(..., description="Minimum temperature threshold")
    max: float = Field(..., description="Maximum temperature threshold")
    needleValue: float = Field(..., description="Current needle position (0-100)")


class DispensePressureData(BaseModel):
    """Dispense pressure/force gauge data"""

    dispensePressure: float = Field(..., description="Current dispense pressure")
    min: float = Field(..., description="Minimum pressure threshold")
    max: float = Field(..., description="Maximum pressure threshold")
    needleValue: float = Field(..., description="Current needle position (0-100)")


class CycleTimeData(BaseModel):
    """Cycle time gauge data"""

    cycleTime: float = Field(..., description="Current cycle time")
    min: float = Field(..., description="Minimum cycle time threshold")
    max: float = Field(..., description="Maximum cycle time threshold")
    needleValue: float = Field(..., description="Current needle position (0-100)")


class RamLoadData(BaseModel):
    """RAM load card data"""

    ramLoad: float = Field(..., description="Current RAM load")
    min: float = Field(..., description="Minimum RAM load threshold")
    max: float = Field(..., description="Maximum RAM load threshold")
    status: str = Field(..., description="Status text (OK, Warning, etc.)")


class VendingMachineOperationsData(BaseModel):
    """Real-time operations data for Polar Delight vending machine"""

    assetId: str = Field(..., description="Asset ID")
    assetLocation: str = Field(..., description="Asset location")
    machineStatus: str = Field(..., description="Machine status (Online/Offline)")
    podCode: str = Field(..., description="POD code")
    cupDetect: str = Field(..., description="Cup detection status (Yes/No)")
    podBinDoor: str = Field(..., description="POD bin door status (Open/Closed)")
    customerDoor: str = Field(..., description="Customer door status (Open/Closed)")

    # Gauge data
    assetHealthData: AssetHealthData = Field(..., description="Asset health gauge data")
    freezerTemperatureData: FreezerTemperatureData = Field(
        ..., description="Freezer temperature gauge data"
    )
    dispensePressureData: DispensePressureData = Field(
        ..., description="Dispense pressure gauge data"
    )
    cycleTimeData: CycleTimeData = Field(..., description="Cycle time gauge data")

    # Card data
    maxRamLoadData: RamLoadData = Field(..., description="Max RAM load card data")

    # Inventory data
    freezerInventory: List[FlavorInventory] = Field(
        ..., description="Freezer inventory data"
    )

    class Config:
        """Pydantic config"""

        json_encoders = {datetime: lambda v: v.isoformat()}
