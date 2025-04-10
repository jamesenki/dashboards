"""
Shadow API Routes Integration

This module provides API route handlers that use our Shadow API Adapter
while maintaining the same route structure expected by the tests.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, status

from src.adapters.shadow_api_adapter import ShadowApiAdapter

logger = logging.getLogger(__name__)

# Create router with the structure expected by tests
# Note: The test includes this router with prefix "/api", so our paths should not include that prefix
router = APIRouter()


async def get_shadow_adapter(request: Request) -> ShadowApiAdapter:
    """
    Get the Shadow API Adapter from the application state.

    Args:
        request: The FastAPI request

    Returns:
        The Shadow API Adapter instance
    """
    if not hasattr(request.app.state, "shadow_service"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shadow service not initialized",
        )
    return request.app.state.shadow_service


async def get_ws_manager(websocket: WebSocket = None, request: Request = None):
    """
    Get the WebSocket manager from the application state.

    Args:
        websocket: Optional WebSocket instance
        request: Optional Request instance

    Returns:
        The WebSocket manager
    """
    if websocket:
        return websocket.app.state.ws_manager
    elif request:
        return request.app.state.ws_manager
    else:
        raise ValueError("Either websocket or request must be provided")


@router.get("/shadows/{device_id}", response_model=Dict[str, Any])
async def get_device_shadow(
    device_id: str, shadow_adapter: ShadowApiAdapter = Depends(get_shadow_adapter)
):
    """
    Get the current shadow document for a device.

    Args:
        device_id: Device identifier

    Returns:
        Shadow document with reported and desired state
    """
    try:
        shadow = await shadow_adapter.get_device_shadow(device_id)
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


@router.patch("/shadows/{device_id}/desired", response_model=Dict[str, Any])
async def update_desired_state(
    device_id: str,
    request: Dict[str, Any],
    shadow_adapter: ShadowApiAdapter = Depends(get_shadow_adapter),
):
    """
    Update the desired state for a device.

    Args:
        device_id: Device identifier
        request: Desired state changes

    Returns:
        Status of the update request
    """
    try:
        if not request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No changes specified"
            )

        result = await shadow_adapter.update_device_shadow(device_id, request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Shadow not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating desired state for {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating desired state: {str(e)}",
        )


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
        shadow_adapter = websocket.app.state.shadow_service
        try:
            shadow = await shadow_adapter.get_device_shadow(device_id)

            # Send shadow as initial data
            await websocket.send_json(shadow)

            # Wait for messages or disconnection
            while True:
                try:
                    # Receive and discard client messages (if any)
                    data = await websocket.receive_text()
                    logger.debug(f"Received WebSocket message: {data}")
                except Exception:
                    break

        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
            if websocket.client_state.CONNECTED:
                await websocket.close(code=1011, reason=str(e))

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        # Unregister client on disconnect
        try:
            await ws_manager.disconnect(device_id, websocket)
        except Exception as e:
            logger.error(f"Error disconnecting client: {e}")


def setup_routes(app):
    """
    Set up the shadow API routes in the FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Include the router with the "/api" prefix to match test expectations
    # This is crucial for the test paths to work correctly
    app.include_router(router, prefix="/api")

    logger.info("✅ Shadow API routes registered with /api prefix")
