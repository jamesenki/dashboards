"""
Device Shadows API Routes

This module provides API routes for accessing device shadow data.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.services.device_shadow import DeviceShadowService, get_device_shadow_service

# Setup logging first
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/device-shadows", tags=["device-shadows"])
logger.info("✅ Device Shadow API router initialized with prefix: /api/device-shadows")


@router.get("/{device_id}")
async def get_device_shadow(
    device_id: str,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
) -> Dict[str, Any]:
    """
    Get the full shadow document for a device.

    Args:
        device_id: The ID of the device to get shadow data for

    Returns:
        The complete shadow document
    """
    logger.info(f"Retrieving shadow document for device {device_id}")
    try:
        # Ensure MongoDB is initialized
        await shadow_service.ensure_initialized()

        # Get the shadow document
        shadow = await shadow_service.get_device_shadow(device_id)
        if not shadow:
            raise HTTPException(
                status_code=404,
                detail=f"No shadow document exists for device {device_id}",
            )

        return shadow
    except Exception as e:
        logger.error(f"Error retrieving shadow document for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving shadow document: {str(e)}"
        )


@router.get("/{device_id}/temperature-history")
async def get_temperature_history(
    device_id: str,
    limit: Optional[int] = 100,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
) -> List[Dict[str, Any]]:
    """
    Get temperature history for a device.

    Args:
        device_id: The ID of the device to get temperature history for
        limit: Optional limit on the number of history entries to return

    Returns:
        List of temperature history entries
    """
    logger.info(f"Retrieving temperature history for device {device_id}, limit={limit}")
    try:
        # Ensure MongoDB is initialized
        await shadow_service.ensure_initialized()

        # Get the shadow document
        shadow = await shadow_service.get_device_shadow(device_id)
        if not shadow:
            raise HTTPException(
                status_code=404,
                detail=f"No shadow document exists for device {device_id}",
            )

        # Extract history
        history = shadow.get("history", [])

        # Process history for temperature data, handling both direct and nested format
        temperature_history = []
        for entry in history:
            timestamp = entry.get("timestamp")

            # Check both formats for temperature
            temperature = None
            if "temperature" in entry:
                temperature = entry["temperature"]
            elif "metrics" in entry and "temperature" in entry["metrics"]:
                temperature = entry["metrics"]["temperature"]

            if timestamp and temperature is not None:
                temperature_history.append(
                    {"timestamp": timestamp, "temperature": temperature}
                )

        # Sort by timestamp (newest first) and apply limit
        temperature_history.sort(key=lambda x: x["timestamp"], reverse=True)
        if limit:
            temperature_history = temperature_history[:limit]

        return temperature_history
    except Exception as e:
        logger.error(f"Error retrieving temperature history for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving temperature history: {str(e)}"
        )
