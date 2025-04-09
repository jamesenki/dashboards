"""
Base device model
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    """Device type enumeration"""

    WATER_HEATER = "water_heater"
    VENDING_MACHINE = "vending_machine"
    ELECTRIC_VEHICLE = "electric_vehicle"
    PLANT_EQUIPMENT = "plant_equipment"
    THERMOSTAT = "thermostat"


class DeviceStatus(str, Enum):
    """Device status enumeration"""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"


class ManufacturerType(str, Enum):
    """Device manufacturer enumeration"""

    RHEEM = "Rheem"
    AQUATHERM = "AquaTherm"
    GENERIC = "Generic"


class Device(BaseModel):
    """Base device model"""

    id: str = Field(..., description="Device unique identifier")
    name: str = Field(..., description="Device name")
    manufacturer: Optional[str] = Field(
        None, description="Device manufacturer (e.g., Rheem, AquaTherm)"
    )
    brand: Optional[str] = Field(None, description="Device brand")
    model: Optional[str] = Field(None, description="Device model number")
    type: DeviceType = Field(..., description="Device type")
    status: DeviceStatus = Field(
        DeviceStatus.OFFLINE, description="Current device status"
    )
    location: Optional[str] = Field(None, description="Physical location of the device")
    last_seen: datetime = Field(
        default_factory=datetime.now, description="Last time the device was seen online"
    )
