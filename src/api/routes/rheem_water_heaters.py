"""
API endpoints for Rheem water heaters.

These endpoints expose Rheem-specific features and integration points.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_rheem_water_heater_service
from src.models.rheem_water_heater import (
    RheemProductSeries,
    RheemWaterHeater,
    RheemWaterHeaterMode,
    RheemWaterHeaterType,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rheem-water-heaters",
    tags=["rheem_water_heaters"],
    responses={404: {"description": "Not found"}},
)


class EcoNetStatusResponse(BaseModel):
    """Response model for EcoNet status."""

    connected: bool = Field(
        ..., description="Whether the device is connected to EcoNet"
    )
    wifi_signal_strength: Optional[int] = Field(
        None, description="WiFi signal strength percentage"
    )
    last_connected: Optional[datetime] = Field(
        None, description="Last time device was connected to EcoNet"
    )
    firmware_version: Optional[str] = Field(
        None, description="Current EcoNet firmware version"
    )
    update_available: Optional[bool] = Field(
        None, description="Whether a firmware update is available"
    )
    remote_control_enabled: bool = Field(
        True, description="Whether remote control is enabled"
    )


class MaintenancePredictionResponse(BaseModel):
    """Response model for maintenance prediction."""

    days_until_maintenance: int = Field(
        ..., description="Estimated days until maintenance is required"
    )
    confidence: float = Field(
        ..., description="Confidence level of the prediction (0-1)"
    )
    component_risks: Dict[str, float] = Field(
        ..., description="Risk assessment for specific components (0-1)"
    )
    next_maintenance_date: str = Field(
        ..., description="Estimated date for next maintenance"
    )
    recommended_actions: List[str] = Field(
        ..., description="Recommended maintenance actions"
    )


class EfficiencyAnalysisResponse(BaseModel):
    """Response model for efficiency analysis."""

    current_efficiency: float = Field(
        ..., description="Current efficiency rating (0-1)"
    )
    estimated_annual_cost: float = Field(
        ..., description="Estimated annual operating cost in dollars"
    )
    potential_savings: float = Field(
        ..., description="Potential annual savings in dollars with improvements"
    )
    recommendations: List[str] = Field(
        ..., description="Recommendations to improve efficiency"
    )


class TelemetryAnalysisResponse(BaseModel):
    """Response model for telemetry analysis."""

    telemetry_health: str = Field(
        ..., description="Overall health assessment of the telemetry"
    )
    anomalies_detected: List[Dict[str, Any]] = Field(
        ..., description="Anomalies detected in the telemetry data"
    )
    patterns: List[str] = Field(..., description="Usage patterns detected")
    estimated_daily_usage: Optional[float] = Field(
        None, description="Estimated daily water usage in gallons"
    )
    peak_usage_time: Optional[str] = Field(
        None, description="Peak water usage time period"
    )


class HealthStatusResponse(BaseModel):
    """Response model for water heater health status."""

    overall_health: str = Field(
        ..., description="Overall health status (Good, Fair, Poor, Critical)"
    )
    last_assessment: datetime = Field(
        ..., description="Timestamp of the last health assessment"
    )
    component_health: Dict[str, str] = Field(
        ..., description="Health status of individual components"
    )
    issues_detected: List[Dict[str, Any]] = Field(
        ..., description="Issues detected during health assessment"
    )
    maintenance_required: bool = Field(
        ..., description="Whether maintenance is required"
    )
    energy_efficiency_score: float = Field(
        ..., description="Energy efficiency score (0-100)"
    )
    warranty_status: str = Field(..., description="Warranty status")


class OperationalSummaryResponse(BaseModel):
    """Response model for water heater operational summary."""

    uptime_percentage: float = Field(
        ..., description="Uptime percentage over the last 30 days"
    )
    average_daily_runtime: float = Field(
        ..., description="Average daily runtime in hours"
    )
    heating_cycles_per_day: float = Field(
        ..., description="Average heating cycles per day"
    )
    energy_usage: Dict[str, float] = Field(
        ..., description="Energy usage statistics (daily, weekly, monthly kWh)"
    )
    water_usage: Dict[str, float] = Field(
        ..., description="Water usage statistics (daily, weekly, monthly gallons)"
    )
    temperature_efficiency: float = Field(
        ..., description="Temperature efficiency percentage"
    )
    mode_usage: Dict[str, float] = Field(
        ..., description="Percentage of time spent in each operating mode"
    )


@router.get("/", response_model=List[RheemWaterHeater])
async def get_all_rheem_water_heaters(
    service=Depends(get_rheem_water_heater_service),
    heater_type: Optional[RheemWaterHeaterType] = None,
    series: Optional[RheemProductSeries] = None,
):
    """
    Get all Rheem water heaters in the system.

    Args:
        heater_type: Optional filter by water heater type
        series: Optional filter by Rheem product series

    Returns:
        List of Rheem water heaters
    """
    try:
        water_heaters = await service.get_all_water_heaters()

        # Apply filters if provided
        if heater_type:
            water_heaters = [
                wh for wh in water_heaters if wh.heater_type == heater_type
            ]

        if series:
            water_heaters = [wh for wh in water_heaters if wh.series == series]

        return water_heaters

    except Exception as e:
        logger.error(f"Error retrieving Rheem water heaters: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving water heaters: {str(e)}"
        )


@router.get("/{device_id}", response_model=RheemWaterHeater)
async def get_rheem_water_heater(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get detailed information about a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        Water heater details
    """
    try:
        water_heater = await service.get_water_heater(device_id)
        if not water_heater:
            raise HTTPException(
                status_code=404, detail=f"Water heater with ID {device_id} not found"
            )
        return water_heater

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Rheem water heater {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving water heater: {str(e)}"
        )


@router.get("/{device_id}/eco-net-status", response_model=EcoNetStatusResponse)
async def get_eco_net_status(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get EcoNet connectivity status for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        EcoNet connectivity status
    """
    try:
        status = await service.get_eco_net_status(device_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"EcoNet status for water heater {device_id} not available",
            )
        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving EcoNet status for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving EcoNet status: {str(e)}"
        )


@router.put("/{device_id}/eco-net-status")
async def update_eco_net_status(
    device_id: str,
    remote_control_enabled: bool = Query(...),
    service=Depends(get_rheem_water_heater_service),
):
    """
    Update EcoNet settings for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater
        remote_control_enabled: Whether remote control should be enabled

    Returns:
        Success message
    """
    try:
        await service.update_eco_net_settings(
            device_id, remote_control_enabled=remote_control_enabled
        )
        return {"message": "EcoNet settings updated successfully"}

    except Exception as e:
        logger.error(f"Error updating EcoNet settings for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating EcoNet settings: {str(e)}"
        )


@router.get(
    "/{device_id}/maintenance-prediction", response_model=MaintenancePredictionResponse
)
async def get_maintenance_prediction(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get maintenance prediction for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        Maintenance prediction details
    """
    try:
        prediction = await service.get_maintenance_prediction(device_id)
        return prediction

    except Exception as e:
        logger.error(f"Error getting maintenance prediction for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting maintenance prediction: {str(e)}"
        )


@router.get(
    "/{device_id}/efficiency-analysis", response_model=EfficiencyAnalysisResponse
)
async def get_efficiency_analysis(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get efficiency analysis for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        Efficiency analysis details
    """
    try:
        analysis = await service.get_efficiency_analysis(device_id)
        return analysis

    except Exception as e:
        logger.error(f"Error getting efficiency analysis for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting efficiency analysis: {str(e)}"
        )


@router.get("/{device_id}/telemetry-analysis", response_model=TelemetryAnalysisResponse)
async def analyze_telemetry(
    device_id: str,
    hours: int = Query(24, ge=1, le=720),
    service=Depends(get_rheem_water_heater_service),
):
    """
    Analyze telemetry data for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater
        hours: Number of hours of data to analyze (1-720, default: 24)

    Returns:
        Telemetry analysis details
    """
    try:
        analysis = await service.analyze_telemetry(device_id, hours=hours)
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing telemetry for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing telemetry: {str(e)}"
        )


@router.put("/{device_id}/mode")
async def set_rheem_water_heater_mode(
    device_id: str,
    mode: RheemWaterHeaterMode = Query(...),
    service=Depends(get_rheem_water_heater_service),
):
    """
    Set the operating mode for a Rheem water heater.

    Args:
        device_id: ID of the water heater
        mode: Operating mode to set

    Returns:
        Success message
    """
    try:
        await service.set_water_heater_mode(device_id, mode)
        return {
            "message": f"Water heater mode updated to {mode}",
            "device_id": device_id,
            "mode": mode,
        }

    except Exception as e:
        logger.error(f"Error setting mode for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error setting water heater mode: {str(e)}"
        )


@router.get(
    "/{device_id}/health-status",
    response_model=HealthStatusResponse,
    summary="Get health status",
    description="Get detailed health status for a specific Rheem water heater.",
)
async def get_health_status(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get health status for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        Health status details
    """
    logger.info(f"Getting health status for water heater {device_id}")

    try:
        health_status = await service.get_health_status(device_id)

        if not health_status:
            raise HTTPException(
                status_code=404,
                detail=f"Health status for water heater {device_id} not found",
            )

        return health_status

    except ValueError as e:
        logger.error(f"Error retrieving health status for {device_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error retrieving health status for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving health status: {str(e)}"
        )


@router.get(
    "/{device_id}/operational-summary",
    response_model=OperationalSummaryResponse,
    summary="Get operational summary",
    description="Get operational summary for a specific Rheem water heater.",
)
async def get_operational_summary(
    device_id: str, service=Depends(get_rheem_water_heater_service)
):
    """
    Get operational summary for a specific Rheem water heater.

    Args:
        device_id: ID of the water heater

    Returns:
        Operational summary details
    """
    logger.info(f"Getting operational summary for water heater {device_id}")

    try:
        operational_summary = await service.get_operational_summary(device_id)

        if not operational_summary:
            raise HTTPException(
                status_code=404,
                detail=f"Operational summary for water heater {device_id} not found",
            )

        return operational_summary

    except ValueError as e:
        logger.error(f"Error retrieving operational summary for {device_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error retrieving operational summary for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving operational summary: {str(e)}"
        )
