"""
Device Shadow Controller for handling HTTP requests.

DEPRECATED: This module is deprecated in favor of the Message Broker Pattern
implementation as described in ADR-0001. Please use the new components:
- ShadowPublisher
- MongoDBShadowListener
- MQTT-WebSocket Bridge
- MessageBrokerIntegrator

This module contains the FastAPI route handlers for device shadow operations.
Following Clean Architecture, controllers depend on use cases.
"""
from typing import Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from src.api.dependencies.service_provider import get_device_shadow_service
from src.api.models.device_shadow_models import DesiredStateUpdate, DeviceShadowResponse
from src.api.websocket.shadow_manager import ShadowWebSocketManager
from src.use_cases.device_shadow_service import DeviceShadowService

# Create a router instance for device shadow endpoints
router = APIRouter(prefix="/api/devices", tags=["device-shadows"])

# Create a WebSocket manager for shadow updates
shadow_ws_manager = ShadowWebSocketManager()


@router.get("/{device_id}/shadow", response_model=DeviceShadowResponse, deprecated=True)
async def get_device_shadow(
    device_id: str,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
) -> Dict[str, Any]:
    """DEPRECATED: Use the MQTT-WebSocket Bridge for real-time shadow updates instead.
    
    Get a device shadow.

    Args:
        device_id: Device ID
        shadow_service: Device shadow service injected by dependency

    Returns:
        Device shadow response model

    Raises:
        HTTPException: If device shadow not found
    """
    try:
        shadow = await shadow_service.get_device_shadow(device_id)
        return shadow
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{device_id}/shadow/desired", response_model=DeviceShadowResponse)
async def update_desired_state(
    device_id: str,
    desired_state: DesiredStateUpdate,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
) -> Dict[str, Any]:
    """Update the desired state of a device shadow.

    Args:
        device_id: Device ID
        desired_state: Desired state update data
        shadow_service: Device shadow service injected by dependency

    Returns:
        Updated device shadow response model

    Raises:
        HTTPException: If update fails or device shadow not found
    """
    try:
        # Convert Pydantic model to dictionary
        state_dict = desired_state.dict()

        # Update desired state through service
        updated_shadow = await shadow_service.update_desired_state(
            device_id, state_dict
        )

        # Notify WebSocket clients of the update
        await shadow_ws_manager.broadcast_to_device(
            device_id, {"type": "desired_state_updated", "shadow": updated_shadow}
        )

        return updated_shadow
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{device_id}/shadow/delta", response_model=Dict[str, Any])
async def get_shadow_delta(
    device_id: str,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
) -> Dict[str, Any]:
    """Get the delta between desired and reported states.

    Args:
        device_id: Device ID
        shadow_service: Device shadow service injected by dependency

    Returns:
        Delta between desired and reported states

    Raises:
        HTTPException: If device shadow not found
    """
    try:
        delta = await shadow_service.get_shadow_delta(device_id)
        return delta
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.websocket("/{device_id}/shadow/updates")
async def shadow_updates_websocket(
    websocket: WebSocket,
    device_id: str,
    shadow_service: DeviceShadowService = Depends(get_device_shadow_service),
):
    """WebSocket endpoint for receiving shadow updates in real-time.

    Args:
        websocket: WebSocket connection
        device_id: Device ID
        shadow_service: Device shadow service injected by dependency
    """
    # Accept the WebSocket connection
    await websocket.accept()

    try:
        # Register the WebSocket with the manager
        await shadow_ws_manager.connect(device_id, websocket)

        # Send the current shadow state immediately after connection
        try:
            shadow = await shadow_service.get_device_shadow(device_id)
            await websocket.send_json({"type": "initial_state", "shadow": shadow})
        except Exception as e:
            # If shadow doesn't exist, send an error but keep the connection open
            await websocket.send_json({"type": "error", "message": str(e)})

        # Keep the connection open and listen for messages
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()

            # Process messages based on type
            message_type = data.get("type")

            if message_type == "update_reported":
                # Client is updating the reported state
                try:
                    reported_state = data.get("state", {})
                    updated_shadow = await shadow_service.update_reported_state(
                        device_id, reported_state
                    )

                    # Send confirmation to the client
                    await websocket.send_json(
                        {"type": "reported_state_updated", "shadow": updated_shadow}
                    )

                    # Broadcast to other clients watching this device
                    await shadow_ws_manager.broadcast_to_device(
                        device_id,
                        {"type": "shadow_updated", "shadow": updated_shadow},
                        exclude=websocket,
                    )
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        # Handle disconnection
        await shadow_ws_manager.disconnect(device_id, websocket)
    except Exception as e:
        # Handle unexpected errors
        try:
            await websocket.send_json(
                {"type": "error", "message": f"An unexpected error occurred: {str(e)}"}
            )
        except:
            pass
        finally:
            await shadow_ws_manager.disconnect(device_id, websocket)
