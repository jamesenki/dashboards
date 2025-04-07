"""
Manufacturer-agnostic API for water heater history.

This module provides history endpoints for water heaters from any manufacturer,
following the manufacturer-agnostic API pattern for consistency.
"""
import logging
import os
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Path, Query

from src.services.water_heater_history import WaterHeaterHistoryService
from src.api.utils.mock_history import (
    create_mock_history_dashboard,
    create_mock_temperature_history,
    create_mock_energy_history,
    create_mock_pressure_flow_history
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/manufacturer/water-heaters",
    tags=["water_heater_history", "manufacturer"],
    responses={
        404: {"description": "Water heater not found or history unavailable"},
        500: {"description": "Server error"},
    },
)


@router.get(
    "/{device_id}/history/dashboard", 
    response_model=Dict[str, Any],
    summary="Get History Dashboard Data",
    description="Returns complete history dashboard data for a water heater",
)
async def get_history_dashboard(
    device_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get the complete history dashboard data for a water heater

    Args:
        device_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Complete history dashboard data
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_history_dashboard(device_id, days)
        
        # In development mode, return mock data if real data is not available
        if not result and os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock history dashboard for {device_id}")
            return create_mock_history_dashboard(device_id, days)
            
        return result
    except Exception as e:
        logger.error(f"Error retrieving history for device {device_id}: {str(e)}")
        
        # In development mode, return mock data when there's an error
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock history dashboard after error for {device_id}")
            return create_mock_history_dashboard(device_id, days)
            
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )


@router.get(
    "/{device_id}/history/temperature", 
    response_model=Dict[str, Any],
    summary="Get Temperature History",
    description="Returns temperature history data for a water heater",
)
async def get_temperature_history(
    device_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get temperature history data for a water heater

    Args:
        device_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for temperature history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_temperature_history(device_id, days)
        
        # In development mode, return mock data if real data is not available
        if not result and os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock temperature history for {device_id}")
            return create_mock_temperature_history(device_id, days)
            
        return result
    except Exception as e:
        logger.error(f"Error retrieving temperature history for device {device_id}: {str(e)}")
        
        # In development mode, return mock data when there's an error
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock temperature history after error for {device_id}")
            return create_mock_temperature_history(device_id, days)
            
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )


@router.get(
    "/{device_id}/history/energy-usage", 
    response_model=Dict[str, Any],
    summary="Get Energy Usage History",
    description="Returns energy usage history data for a water heater",
)
async def get_energy_usage_history(
    device_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get energy usage history data for a water heater

    Args:
        device_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for energy usage history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_energy_usage_history(device_id, days)
        
        # In development mode, return mock data if real data is not available
        if not result and os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock energy usage history for {device_id}")
            return create_mock_energy_history(device_id, days)
            
        return result
    except Exception as e:
        logger.error(f"Error retrieving energy usage history for device {device_id}: {str(e)}")
        
        # In development mode, return mock data when there's an error
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock energy usage history after error for {device_id}")
            return create_mock_energy_history(device_id, days)
            
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )


@router.get(
    "/{device_id}/history", 
    response_model=Dict[str, Any],
    summary="Get All History Data",
    description="Returns all history data for a water heater, including temperature, energy usage, and pressure/flow",
)
async def get_all_history(
    device_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get all history data for a water heater

    Args:
        device_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Complete history data including all metrics
    """
    try:
        # Create combined history data from all metrics
        response = {
            "device_id": device_id,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
        }
        
        # Get all individual history components
        # For development environment, always use mock data to ensure proper format
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Using consistent mock data format for history data for {device_id}")
            dashboard = create_mock_history_dashboard(device_id, days)
            temperature = create_mock_temperature_history(device_id, days)
            energy = create_mock_energy_history(device_id, days)
            pressure_flow = create_mock_pressure_flow_history(device_id, days)
        else:
            try:
                history_service = WaterHeaterHistoryService()
                # Try to get real data first
                dashboard = await history_service.get_history_dashboard(device_id, days)
                temperature = await history_service.get_temperature_history(device_id, days)
                energy = await history_service.get_energy_usage_history(device_id, days)
                pressure_flow = await history_service.get_pressure_flow_history(device_id, days)
                
                # If any component is missing, use mock data
                if not dashboard or not temperature or not energy or not pressure_flow:
                    logger.info(f"Some history data missing for {device_id}, using mock data")
                    dashboard = create_mock_history_dashboard(device_id, days)
                    temperature = create_mock_temperature_history(device_id, days)
                    energy = create_mock_energy_history(device_id, days)
                    pressure_flow = create_mock_pressure_flow_history(device_id, days)
            except Exception as e:
                logger.warning(f"Error getting history data: {e}. Using mock data.")
                dashboard = create_mock_history_dashboard(device_id, days)
                temperature = create_mock_temperature_history(device_id, days)
                energy = create_mock_energy_history(device_id, days)
                pressure_flow = create_mock_pressure_flow_history(device_id, days)
        
        # Combine all data into one response
        response["dashboard"] = dashboard
        response["temperature"] = temperature
        response["energy_usage"] = energy
        response["pressure_flow"] = pressure_flow
        
        return response
    except Exception as e:
        logger.error(f"Error retrieving combined history for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve history data for {device_id}"
        )


@router.get(
    "/{device_id}/history/pressure-flow", 
    response_model=Dict[str, Any],
    summary="Get Pressure Flow History",
    description="Returns pressure and flow rate history data for a water heater",
)
async def get_pressure_flow_history(
    device_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get pressure and flow rate history data for a water heater

    Args:
        device_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for pressure and flow rate history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_pressure_flow_history(device_id, days)
        
        # In development mode, return mock data if real data is not available
        if not result and os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock pressure flow history for {device_id}")
            return create_mock_pressure_flow_history(device_id, days)
            
        return result
    except Exception as e:
        logger.error(f"Error retrieving pressure flow history for device {device_id}: {str(e)}")
        
        # In development mode, return mock data when there's an error
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            logger.info(f"Returning mock pressure flow history after error for {device_id}")
            return create_mock_pressure_flow_history(device_id, days)
            
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )
