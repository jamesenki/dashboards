"""
API models for device shadow endpoints.

These Pydantic models define the request and response structures for
device shadow API operations, following Clean Architecture by separating
the delivery mechanism from the use cases.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DesiredStateUpdate(BaseModel):
    """Model for updating a device shadow's desired state.

    This is a flexible model that can accept any key-value pairs
    as the desired state properties to update.
    """

    __root__: Dict[str, Any] = Field(
        ...,
        description="Key-value pairs representing the desired state properties to update",
    )

    def dict(self, **kwargs):
        """Override dict method to return the root dictionary directly."""
        return self.__root__


class ReportedStateUpdate(BaseModel):
    """Model for updating a device shadow's reported state.

    This is a flexible model that can accept any key-value pairs
    as the reported state properties to update.
    """

    __root__: Dict[str, Any] = Field(
        ...,
        description="Key-value pairs representing the reported state properties to update",
    )

    def dict(self, **kwargs):
        """Override dict method to return the root dictionary directly."""
        return self.__root__


class DeviceShadowResponse(BaseModel):
    """Model for device shadow responses."""

    device_id: str = Field(..., description="Device ID")
    reported: Dict[str, Any] = Field(
        ..., description="The last reported state from the device"
    )
    desired: Dict[str, Any] = Field(
        ..., description="The desired state to be sent to the device"
    )
    version: int = Field(
        ..., description="Version number that increments with each update"
    )
    timestamp: Optional[str] = Field(None, description="Timestamp of the last update")

    class Config:
        """Pydantic model configuration."""

        orm_mode = True
