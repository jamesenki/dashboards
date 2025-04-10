"""
Device Shadow API endpoints.

This module provides API endpoints for:
1. Getting device shadow state
2. Requesting state changes from the frontend
3. WebSocket connections for real-time shadow updates
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Define API models
class DeviceStateRequest(BaseModel):
    """Model for device state change requests from frontend"""

    class Config:
        extra = "allow"  # Allow dynamic fields based on device capabilities


class ShadowUpdateResponse(BaseModel):
    """Response model for shadow update requests"""

    success: bool
    device_id: str
    version: Optional[int] = None
    pending: Optional[List[str]] = None
    message: Optional[str] = None


# Create a single router as expected by the tests
# The test adds '/api' prefix, so paths should be relative to that
router = APIRouter(tags=["device_shadow"])


async def get_shadow_service(request: Request):
    """Dependency to get shadow service from app state"""
    if not hasattr(request.app.state, "shadow_service"):
        logger.error("Shadow service not initialized in app state")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shadow service not available",
        )
    return request.app.state.shadow_service


async def get_frontend_request_handler(request: Request):
    """Dependency to get frontend request handler from app state"""
    if not hasattr(request.app.state, "frontend_request_handler"):
        # Lazy init if not already in app state
        from src.services.frontend_request_handler import FrontendRequestHandler

        request.app.state.frontend_request_handler = FrontendRequestHandler(
            shadow_service=request.app.state.shadow_service
        )
    return request.app.state.frontend_request_handler


async def get_ws_manager(websocket: WebSocket = None, request: Request = None):
    """Dependency to get WebSocket manager from app state"""
    # Handle both WebSocket and regular request contexts
    if websocket:
        return websocket.app.state.ws_manager
    elif request:
        return request.app.state.ws_manager
    else:
        raise ValueError("Either websocket or request must be provided")


@router.get("/shadows/{device_id}", response_model=Dict[str, Any])
async def get_device_shadow(device_id: str, shadow_service=Depends(get_shadow_service)):
    """
    Get the current shadow document for a device.

    Args:
        device_id: Device identifier

    Returns:
        Shadow document with reported and desired state
    """
    try:
        shadow = await shadow_service.get_device_shadow(device_id)
        return shadow
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Shadow not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving shadow for {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shadow: {str(e)}",
        )


@router.patch("/shadows/{device_id}/desired", response_model=ShadowUpdateResponse)
async def update_desired_state(
    device_id: str,
    request: DeviceStateRequest,
    request_handler=Depends(get_frontend_request_handler),
):
    """
    Update the desired state for a device from frontend.

    Args:
        device_id: Device identifier
        request: Desired state changes

    Returns:
        Status of the update request
    """
    try:
        # Validate request has content
        # Use model_dump instead of dict for Pydantic v2 compatibility
        try:
            # Try Pydantic v2 method first
            request_dict = request.model_dump(exclude_unset=True)
        except AttributeError:
            # Fall back to Pydantic v1 method
            request_dict = request.dict(exclude_unset=True)

        if not request_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body cannot be empty",
            )

        # Process the frontend request
        success = await request_handler.handle_state_change_request(
            device_id=device_id, request=request_dict
        )

        if not success:
            # If device not found or other error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cannot update shadow for device {device_id}",
            )

        # Get the updated shadow to include pending states in response
        shadow = await request_handler.shadow_service.get_device_shadow(device_id)
        # Carefully access the returned shadow document to extract pending states
        desired = shadow.get("desired", {}) if isinstance(shadow, dict) else {}
        pending = desired.get("_pending", [])

        # Return success response with pending state info
        return ShadowUpdateResponse(
            success=True,
            device_id=device_id,
            version=shadow.get("version"),
            pending=pending,
            message="State change request submitted",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error updating desired state for {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating desired state: {str(e)}",
        )


# The test adds '/api' prefix when including the router (line 103 in the test)
# So we must define the path as '/ws/shadows/{device_id}' to result in '/api/ws/shadows/{device_id}'
@router.websocket("/ws/shadows/{device_id}")
async def websocket_shadow_updates(
    websocket: WebSocket, device_id: str, ws_manager=Depends(get_ws_manager)
):
    """
    WebSocket endpoint for real-time shadow updates.

    Clients can connect to this endpoint to receive real-time
    updates whenever the device shadow changes.

    Args:
        websocket: WebSocket connection
        device_id: Device identifier to subscribe to
    """
    try:
        # Accept the connection
        await websocket.accept()

        # Register client connection
        await ws_manager.connect(device_id, websocket)

        # Send current shadow state as initial data
        shadow_service = websocket.app.state.shadow_service

        try:
            # Retrieve shadow data using our adapter
            shadow = await shadow_service.get_device_shadow(device_id)

            # Ensure the data has the expected format
            if not isinstance(shadow, dict) or "device_id" not in shadow:
                logger.warning(
                    f"Shadow data for {device_id} has unexpected format: {shadow}"
                )
                # Format the shadow to match expected structure
                formatted_shadow = {
                    "device_id": device_id,
                    "reported": shadow.get("reported", {"status": "UNKNOWN"}),
                    "desired": shadow.get("desired", {}),
                    "version": shadow.get("version", 0),
                }
                await websocket.send_json(formatted_shadow)
            else:
                # Send the shadow data as-is
                await websocket.send_json(shadow)

        except ValueError as e:
            # If shadow doesn't exist yet, send empty state
            logger.warning(f"No shadow found for {device_id}: {e}")
            await websocket.send_json(
                {
                    "device_id": device_id,
                    "reported": {"status": "UNKNOWN"},
                    "desired": {},
                    "version": 0,
                }
            )
        except Exception as e:
            logger.error(f"Error retrieving shadow for WebSocket: {e}")
            await websocket.send_json(
                {
                    "device_id": device_id,
                    "reported": {"status": "ERROR"},
                    "desired": {},
                    "version": 0,
                    "error": str(e),
                }
            )

        # Keep connection alive until client disconnects
        try:
            while True:
                # Wait for client messages (like ping/pong)
                data = await websocket.receive_text()
                # Echo back to confirm connection is active
                if data == "ping":
                    await websocket.send_text("pong")
        except Exception:
            # Client disconnected
            pass

    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        # Close connection if not already closed
        try:
            await websocket.close()
        except:
            pass
    finally:
        # Unregister client connection when disconnected
        if ws_manager:
            await ws_manager.disconnect(device_id, websocket)


def setup_routes(app):
    """
    Set up the shadow API routes in the FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Include the router with the '/api' prefix exactly as the test does
    app.include_router(router, prefix="/api")

    logger.info("✅ Shadow API routes registered with prefix to match test expectations")


@router.get("/")
async def list_all_shadow_documents(shadow_service=Depends(get_shadow_service)):
    """
    Get a list of all available shadow documents.

    Returns:
        List of shadow documents with device information
    """
    try:
        # Get all shadow documents
        shadows = await shadow_service.list_all_shadows()
        return shadows
    except Exception as e:
        # Log and return empty array on error for better UI handling
        logger.error(f"Error listing shadow documents: {e}")
        return []


@router.get("/{device_id}/history")
async def get_device_shadow_history(
    device_id: str, shadow_service=Depends(get_shadow_service)
):
    """
    Get historical data for a device shadow.

    Args:
        device_id: Device identifier

    Returns:
        List of historical data points for the device
    """
    try:
        # Get the shadow history
        history = await shadow_service.get_device_shadow_history(device_id)
        return history
    except ValueError as e:
        # Shadow doesn't exist
        logger.warning(f"Error getting history for {device_id}: {e}")
        # Return empty history array instead of error for better UI handling
        return []
    except Exception as e:
        # Other errors
        logger.error(f"Error getting history for {device_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving shadow history: {str(e)}"
        )
