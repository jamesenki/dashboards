"""
Shadow Document API for IoTSphere platform.
Part of the GREEN phase implementation in our TDD cycle.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from src.models.telemetry import TelemetryData
from src.services.device_shadow import DeviceShadowService
from src.services.telemetry_service import get_telemetry_service

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/shadows",
    tags=["device-shadow"],
    responses={404: {"description": "Device not found"}},
)

# Create shadow service instance
shadow_service = DeviceShadowService()
telemetry_service = get_telemetry_service()


@router.get("/{device_id}")
async def get_device_shadow(
    device_id: str = Path(..., description="The ID of the device")
) -> Dict[str, Any]:
    """
    Get the current shadow document for a device.

    Args:
        device_id: The ID of the device to get the shadow for

    Returns:
        The shadow document

    Raises:
        HTTPException: If the shadow document does not exist
    """
    try:
        # Check if shadow exists
        if not await shadow_service.shadow_exists(device_id):
            logger.warning(f"Shadow document does not exist for device {device_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No shadow document exists for device {device_id}",
            )

        # Get shadow document
        shadow = await shadow_service.get_device_shadow(device_id)
        return shadow

    except Exception as e:
        logger.error(f"Error getting shadow for device {device_id}: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500, detail=f"Error getting shadow document: {str(e)}"
        )


@router.put("/{device_id}")
async def update_device_shadow(
    shadow_data: Dict[str, Any],
    device_id: str = Path(..., description="The ID of the device"),
) -> Dict[str, Any]:
    """
    Update the shadow document for a device.

    Args:
        device_id: The ID of the device to update
        shadow_data: The shadow data to update

    Returns:
        The updated shadow document

    Raises:
        HTTPException: If the update fails
    """
    try:
        # Get reported and desired state from request body
        reported_state = shadow_data.get("state", {}).get("reported", {})
        desired_state = shadow_data.get("state", {}).get("desired", {})

        # Check if shadow exists
        if not await shadow_service.shadow_exists(device_id):
            # Create new shadow
            shadow = await shadow_service.create_device_shadow(
                device_id=device_id,
                reported_state=reported_state,
                desired_state=desired_state,
            )
        else:
            # Update existing shadow
            shadow = await shadow_service.update_device_shadow(
                device_id=device_id,
                reported_state=reported_state,
                desired_state=desired_state,
            )

        return shadow

    except Exception as e:
        logger.error(f"Error updating shadow for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating shadow document: {str(e)}"
        )


@router.get("/{device_id}/history")
async def get_shadow_history(
    device_id: str = Path(..., description="The ID of the device"),
    days: int = Query(7, description="Number of days of history to return"),
    limit: int = Query(1000, description="Maximum number of data points to return"),
) -> List[Dict[str, Any]]:
    """
    Get historical data for a device shadow.

    Args:
        device_id: The ID of the device
        days: Number of days of history to return
        limit: Maximum number of data points to return

    Returns:
        List of shadow history data points

    Raises:
        HTTPException: If retrieving shadow history fails
    """
    try:
        # Check if shadow exists
        if not await shadow_service.shadow_exists(device_id):
            logger.warning(f"Shadow document does not exist for device {device_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No shadow document exists for device {device_id}",
            )

        # Get shadow history
        try:
            history = await shadow_service.get_device_shadow_history(device_id)

            # Filter by date if needed
            if days > 0:
                now = datetime.utcnow()
                cutoff = now - timedelta(days=days)

                # Filter history entries by timestamp
                filtered_history = []
                for entry in history:
                    try:
                        # Handle both string and datetime timestamps
                        if isinstance(entry.get("timestamp"), str):
                            entry_time = datetime.fromisoformat(
                                entry.get("timestamp").rstrip("Z")
                            )
                        else:
                            entry_time = entry.get("timestamp")

                        if entry_time >= cutoff:
                            filtered_history.append(entry)
                    except (ValueError, TypeError, AttributeError):
                        # Keep entries with invalid timestamps
                        filtered_history.append(entry)

                history = filtered_history

            # Limit the number of data points if necessary
            if len(history) > limit:
                # Sample data points evenly
                step = len(history) // limit
                history = history[::step][:limit]

            return history

        except Exception as history_error:
            logger.error(
                f"Error getting shadow history for device {device_id}: {str(history_error)}"
            )
            # Return empty list instead of error if history not found
            return []

    except Exception as e:
        logger.error(f"Error getting shadow history for device {device_id}: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500, detail=f"Error getting shadow history: {str(e)}"
        )


@router.get("/{device_id}/telemetry/{metric}")
async def get_device_telemetry(
    device_id: str = Path(..., description="The ID of the device"),
    metric: str = Path(..., description="The metric to get data for"),
    days: int = Query(7, description="Number of days of history to return"),
    limit: int = Query(1000, description="Maximum number of data points to return"),
) -> List[Dict[str, Any]]:
    """
    Get telemetry data for a device.

    Args:
        device_id: The ID of the device
        metric: The metric to get data for (e.g., temperature)
        days: Number of days of history to return
        limit: Maximum number of data points to return

    Returns:
        List of telemetry data points

    Raises:
        HTTPException: If retrieving telemetry data fails
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        # Get telemetry data
        telemetry_data = await telemetry_service.get_historical_telemetry(
            device_id=device_id, metric=metric, start_time=start_time, end_time=end_time
        )

        # Limit number of data points if necessary
        if len(telemetry_data) > limit:
            # Sample data points evenly
            step = len(telemetry_data) // limit
            telemetry_data = telemetry_data[::step][:limit]

        return telemetry_data

    except Exception as e:
        logger.error(f"Error getting telemetry for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting telemetry data: {str(e)}"
        )
