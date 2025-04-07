"""
WebSocket routes for the IoTSphere API.

This module provides WebSocket endpoints for real-time device data streaming,
state updates, and notifications.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta

from src.services.websocket_manager import WebSocketManager
from src.services.device_shadow import DeviceShadowService
from src.services.telemetry_service import TelemetryService, get_telemetry_service
from src.api.middleware.websocket_auth import (
    websocket_auth_middleware,
    verify_websocket_operation
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instances
_websocket_manager = None
_shadow_service = None
_telemetry_service = None

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_websocket_manager() -> WebSocketManager:
    """Get or create the WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def get_shadow_service() -> DeviceShadowService:
    """Get or create the Device Shadow service instance."""
    global _shadow_service
    if _shadow_service is None:
        _shadow_service = DeviceShadowService()
    return _shadow_service


def get_telemetry_service_local() -> TelemetryService:
    """Get or create the Telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = get_telemetry_service()
    return _telemetry_service


def create_default_state_for_device_type(device_id: str, device_type: str) -> Dict[str, Any]:
    """
    Create a default device state based on the device type.
    
    This function supports IoTSphere's device-agnostic approach by providing
    appropriate default states for different device types.
    
    Args:
        device_id: The device identifier
        device_type: The type of device (water_heater, vending_machine, robot, vehicle, etc.)
        
    Returns:
        A dictionary with default state values appropriate for the device type
    """
    now = datetime.now().isoformat() + "Z"
    
    # Common fields for all device types
    base_state = {
        "connection_status": "connected",
        "last_updated": now,
        "firmware_version": "1.0.0"
    }
    
    # Device-specific default states
    if device_type == "water_heater":
        return {
            **base_state,
            "temperature": 65.0,  # Default temperature in Fahrenheit
            "mode": "normal",    # Default operating mode
            "pressure": 2.1,      # Water pressure in PSI
            "flow_rate": 10.0,    # Water flow rate in GPM
            "energy_usage": 3500   # Energy usage in Watts
        }
    elif device_type == "vending_machine":
        return {
            **base_state,
            "temperature": 38.0,   # Internal temperature in Fahrenheit
            "inventory_level": 75, # Inventory level as percentage
            "cash_level": 45.50,   # Cash in machine
            "door_status": "closed",
            "last_transaction": None
        }
    elif device_type == "robot":
        return {
            **base_state,
            "battery_level": 85,    # Battery percentage
            "position": {"x": 0, "y": 0, "z": 0},
            "status": "idle",      # Operational status
            "error_code": None,     # Current error if any
            "task_progress": None   # Current task information
        }
    elif device_type == "vehicle":
        return {
            **base_state,
            "fuel_level": 75,       # Fuel percentage
            "mileage": 12500,       # Current mileage
            "engine_temp": 190,     # Engine temperature
            "tire_pressure": {      # Tire pressure in PSI
                "front_left": 32.0,
                "front_right": 32.0,
                "rear_left": 32.0,
                "rear_right": 32.0
            },
            "check_engine": False    # Check engine light status
        }
    else:
        # Generic device state
        return {
            **base_state,
            "status": "online",
            "battery_level": 100,
            "device_type": device_type
        }


# def get_auth_service() -> AuthService:
#     """Get or create the Auth service instance."""
#     global _auth_service
#     if _auth_service is None:
#         _auth_service = AuthService()
#     return _auth_service


# Authentication is now handled by the websocket_auth_middleware


@router.websocket("/ws/devices/{device_id}/state")
@websocket_auth_middleware
async def device_state(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint for device state updates.
    
    This endpoint allows clients to:
    1. Receive real-time state updates from the device shadow
    2. Get the current device state
    3. Update the desired state of the device
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to subscribe to, using manufacturer-agnostic format
    """
    # The connection is already accepted in the middleware
    # No need to call websocket.accept() again
    logger.info(f"Device state handler running for device {device_id}")
    
    # Get service instances
    manager = get_websocket_manager()
    shadow_service = get_shadow_service()
    
    # Register the connection with the WebSocket manager
    await manager.connect(websocket, device_id, "state")
    
    try:
        # Send initial state to the client
        try:
            current_state = await shadow_service.get_device_shadow(device_id)
            # Add the type field needed by the frontend and tests
            response = {
                "type": "state_update",
                "device_id": device_id,
                **current_state
            }
            logger.debug(f"Sending initial state for device {device_id}")
            await websocket.send_text(json.dumps(response))
        except ValueError as e:
            # Shadow doesn't exist yet, create a default state based on device type
            logger.info(f"No shadow exists for device {device_id}, sending default state")
            
            # Determine device type from ID prefix
            device_type = "generic"
            if device_id.startswith("wh-"):
                device_type = "water_heater"
            elif device_id.startswith("vm-"):
                device_type = "vending_machine"
            elif device_id.startswith("rb-"):
                device_type = "robot"
            elif device_id.startswith("ve-"):
                device_type = "vehicle"
            
            # Create appropriate default state based on device type
            default_state = create_default_state_for_device_type(device_id, device_type)
            
            await websocket.send_text(json.dumps({
                "type": "state_update",
                "device_id": device_id,
                "device_type": device_type,
                "reported": default_state,
                "desired": {},
                "version": 0,
                "message": f"Using default state for {device_type}"
            }))
        
        # Process messages until client disconnects
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Log received message for debugging
            logger.debug(f"Received message from {device_id}: {message}")
            
            # Process different message types
            message_type = message.get("type", "")
            
            # Echo back the message for testing/debugging purposes
            await websocket.send_text(json.dumps({
                "type": "echo",
                "device_id": device_id,
                "original": message,
                "timestamp": asyncio.get_event_loop().time()
            }))
            
            # Verify permissions for the operation
            permission_error = await verify_websocket_operation(websocket, message_type, message)
            if permission_error:
                logger.warning(f"Permission denied for {message_type} operation on device {device_id}")
                await websocket.send_text(json.dumps(permission_error))
                continue
            
            if message_type == "get_state":
                # Client is requesting the current state
                try:
                    current_state = await shadow_service.get_device_shadow(device_id)
                    # Add the type field needed by the frontend and tests
                    response = {
                        "type": "state_update",
                        **current_state
                    }
                    await websocket.send_text(json.dumps(response))
                except ValueError as e:
                    await websocket.send_text(json.dumps({
                        "error": str(e)
                    }))
            
            elif message_type == "update_desired":
                # Client is updating the desired state
                try:
                    desired_state = message.get("state", {})
                    version = message.get("version")
                    
                    result = await shadow_service.update_device_shadow(
                        device_id=device_id,
                        desired_state=desired_state,
                        version=version
                    )
                    
                    await websocket.send_text(json.dumps({
                        "type": "update_success",
                        "device_id": device_id,
                        "version": result["version"]
                    }))
                except ValueError as e:
                    await websocket.send_text(json.dumps({
                        "type": "update_error",
                        "error": str(e)
                    }))
            
            elif message_type == "get_delta":
                # Client is requesting the delta between reported and desired
                try:
                    delta = await shadow_service.get_shadow_delta(device_id)
                    await websocket.send_text(json.dumps({
                        "type": "delta",
                        "device_id": device_id,
                        "delta": delta
                    }))
                except ValueError as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "error": str(e)
                    }))
            
            else:
                # Unknown message type
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                }))
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from device {device_id} state")
    except Exception as e:
        logger.error(f"Error in device state websocket: {str(e)}")
    finally:
        # Unregister the connection
        await manager.disconnect(websocket, device_id, "state")


@router.websocket("/ws/devices/{device_id}/telemetry")
@websocket_auth_middleware
async def device_telemetry(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint for device telemetry streaming.
    
    This endpoint allows clients to:
    1. Subscribe to real-time telemetry data from a device
    2. Filter telemetry by metric types
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to subscribe to
    """
    # Connection already accepted in the middleware
    logger.info(f"Device state handler running for device {device_id}")
    
    # Get service instances
    manager = get_websocket_manager()
    telemetry_service = get_telemetry_service_local()
    
    # Register the connection
    await manager.connect(websocket, device_id, "telemetry")
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "info",
            "message": "Connected to telemetry stream for device " + device_id,
            "device_id": device_id
        }))
        
        # Mock telemetry data for development
        metrics = ["temperature", "pressure", "flow_rate", "energy_usage"]
        last_values = {
            "temperature": 65.0,
            "pressure": 2.2,
            "flow_rate": 12.0,
            "energy_usage": 4400
        }
        
        # Process subscription requests
        data = await websocket.receive_text()
        message = json.loads(data)
        
        # Check if this is a subscription request
        if message.get("type") == "subscribe":
            # Get filter settings
            filter_metrics = message.get("metrics", metrics)
            
            # Send confirmation
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "metrics": filter_metrics,
                "device_id": device_id
            }))
            
            # Start telemetry simulation in the background for testing
            # In production, this would be real telemetry data from devices
            sim_task = None
            
            # Check if we should simulate telemetry data
            simulate = websocket.query_params.get("simulate", "false").lower() == "true"
            
            if simulate:
                # Start a background task to simulate telemetry
                async def run_simulation():
                    try:
                        # Simulate telemetry by sending periodic updates
                        start_time = datetime.now()
                        end_time = start_time + timedelta(seconds=3600)  # Run for 1 hour max
                        
                        import random
                        
                        while datetime.now() < end_time:
                            # Generate random changes to each metric
                            for metric in filter_metrics:
                                if metric in last_values:
                                    # Add small random change to current value
                                    base_value = last_values[metric]
                                    if metric == "temperature":
                                        # Temperature fluctuates more slowly
                                        change = random.uniform(-0.5, 0.5)
                                    elif metric == "pressure":
                                        change = random.uniform(-0.1, 0.1)
                                    elif metric == "flow_rate":
                                        change = random.uniform(-0.3, 0.3)
                                    elif metric == "energy_usage":
                                        change = random.uniform(-50, 50)
                                    else:
                                        change = random.uniform(-1, 1)
                                        
                                    # Update the value
                                    last_values[metric] = max(0, base_value + change)
                                    
                                    # Create telemetry data
                                    telemetry_data = {
                                        "type": "telemetry_update",
                                        "device_id": device_id,
                                        "metric": metric,
                                        "value": last_values[metric],
                                        "timestamp": datetime.now().isoformat(),
                                        "simulated": True
                                    }
                                    
                                    # Send to all subscribed clients
                                    await manager.broadcast_to_device(
                                        device_id=device_id,
                                        message=telemetry_data,  # WebSocketManager will handle JSON serialization
                                        connection_type="telemetry"
                                    )
                                    
                            # Wait before next update
                            await asyncio.sleep(2.0)  # Update every 2 seconds
                                    
                    except Exception as e:
                        logger.error(f"Simulation error: {str(e)}")
                
                sim_task = asyncio.create_task(run_simulation())
                logger.info(f"Started telemetry simulation for device {device_id}")
            
            try:
                # Process messages until client disconnects
                while True:
                    # Wait for a message from the client (with timeout)
                    try:
                        data = await asyncio.wait_for(
                            websocket.receive_text(), 
                            timeout=5.0  # Check every 5 seconds
                        )
                        
                        # Process the message
                        message = json.loads(data)
                        message_type = message.get("type", "")
                        
                        # Verify permissions for the operation
                        permission_error = await verify_websocket_operation(websocket, message_type, message)
                        if permission_error:
                            await websocket.send_text(json.dumps(permission_error))
                            continue
                        
                        if message_type == "unsubscribe":
                            # Client is unsubscribing
                            metrics_to_remove = message.get("metrics", [])
                            
                            # Update subscribed metrics
                            if not metrics_to_remove:
                                # Unsubscribe from all metrics
                                websocket.state.subscribed_metrics = []
                            else:
                                # Unsubscribe from specific metrics
                                websocket.state.subscribed_metrics = [
                                    m for m in websocket.state.subscribed_metrics 
                                    if m not in metrics_to_remove
                                ]
                            
                            # Acknowledge unsubscription
                            await websocket.send_text(json.dumps({
                                "type": "unsubscription_confirmed",
                                "remaining_metrics": websocket.state.subscribed_metrics
                            }))
                        
                        elif message_type == "get_recent":
                            # Get recent telemetry data for a specific metric
                            metric = message.get("metric")
                            limit = message.get("limit", 20)
                            
                            if not metric:
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "error": "Metric name is required"
                                }))
                                continue
                            
                            # Get the data from the telemetry service
                            recent_data = await telemetry_service.get_recent_telemetry(
                                device_id=device_id,
                                metric=metric,
                                limit=limit
                            )
                            
                            # Send the data to the client
                            await websocket.send_text(json.dumps({
                                "type": "recent_telemetry",
                                "device_id": device_id,
                                "metric": metric,
                                "data": recent_data
                            }))
                    
                    except asyncio.TimeoutError:
                        # No message received, just continue
                        pass
            except Exception as e:
                logger.error(f"Error in telemetry generation: {str(e)}")
        else:
            # Not a subscription request
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "Expected subscription request"
            }))
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from device {device_id} telemetry")
    except Exception as e:
        logger.error(f"Error in device telemetry websocket: {str(e)}")
    finally:
        # Cancel any simulation task if running
        if sim_task and not sim_task.done():
            sim_task.cancel()
            try:
                await sim_task
            except asyncio.CancelledError:
                pass
        
        # Unregister the connection
        await manager.disconnect(websocket, device_id, "telemetry")


@router.websocket("/ws/devices/{device_id}/alerts")
async def device_alerts(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint for device alerts and notifications.
    
    This endpoint allows clients to:
    1. Receive real-time alerts and notifications about a device
    2. Filter alerts by severity and type
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to subscribe to
    """
    # Connection already accepted in the middleware
    logger.info(f"Device state handler running for device {device_id}")
    
    # Get service instances
    manager = get_websocket_manager()
    
    # Authenticate the connection
    if not await authenticate_connection(websocket, device_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Register the connection
    await manager.connect(websocket, device_id, "alerts")
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "info",
            "message": "Connected to alerts stream for device " + device_id
        }))
        
        # In a real implementation, we would subscribe to an alert service
        # For now, we'll just wait for disconnection
        while True:
            await asyncio.sleep(30)  # Just keep connection alive
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from device {device_id} alerts")
    except Exception as e:
        logger.error(f"Error in device alerts websocket: {str(e)}")
    finally:
        # Unregister the connection
        await manager.disconnect(websocket, device_id, "alerts")


@router.websocket("/ws/broadcast")
@websocket_auth_middleware
async def broadcast_channel(websocket: WebSocket):
    """
    WebSocket endpoint for system-wide broadcasts.
    
    This endpoint allows clients to:
    1. Subscribe to system-wide broadcasts and announcements
    2. Filter broadcasts by topic
    
    Args:
        websocket: The WebSocket connection
    """
    # Connection is already accepted in the middleware - no need to call accept() again
    logger.info("Broadcast channel handler running for system-wide messages")
    
    # Get service instances
    manager = get_websocket_manager()
    
    # Special channel ID for broadcast connections
    channel_id = "broadcast"
    
    # Register the connection with the WebSocket manager
    await manager.connect(websocket, channel_id, "broadcast")
    
    try:
        # Send initial welcome message
        await websocket.send_text(json.dumps({
            "type": "connect_info",
            "message": "Connected to broadcast channel",
            "timestamp": asyncio.get_event_loop().time()
        }))
        
        # Process messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Log received message
            logger.debug(f"Received broadcast message: {message}")
            
            # Echo back the message for testing purposes
            await websocket.send_text(json.dumps({
                "type": "echo",
                "channel": channel_id,
                "original": message,
                "timestamp": asyncio.get_event_loop().time()
            }))
            
            # Process based on message type
            message_type = message.get("type", "")
            
            if message_type == "subscribe":
                # Get topics to subscribe to
                topics = message.get("topics", ["system"])
                
                # Subscribe to each topic
                for topic in topics:
                    await manager.subscribe_to_topic(websocket, topic)
                
                # Send confirmation
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "topics": topics
                }))
            
            elif message_type == "unsubscribe":
                topics_to_unsub = message.get("topics", [])
                for topic in topics_to_unsub:
                    await manager.unsubscribe_from_topic(websocket, topic)
                
                # Send confirmation
                await websocket.send_text(json.dumps({
                    "type": "unsubscribe_confirmed",
                    "topics": topics_to_unsub
                }))
            
            elif message_type == "publish":
                # Client is publishing a message to a topic
                topic = message.get("topic", "system")
                content = message.get("content", {})
                
                # Verify user has permission to publish
                user = getattr(websocket.state, "user", None)
                if not user or user.get("role") not in ["admin", "facility_manager"]:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "error": "You do not have permission to publish messages"
                    }))
                    continue
                
                # Add metadata to the message
                broadcast_message = {
                    "type": "broadcast",
                    "topic": topic,
                    "content": content,
                    "publisher": user.get("username", "unknown"),
                    "timestamp": datetime.now().isoformat() + "Z"
                }
                
                # Broadcast to all subscribers of this topic
                await manager.broadcast_to_topic(topic, json.dumps(broadcast_message))
    
    except WebSocketDisconnect:
        logger.info("Client disconnected from broadcast channel")
    except Exception as e:
        logger.error(f"Error in broadcast websocket: {str(e)}")
        # Log detailed exception for debugging
        import traceback
        logger.debug(traceback.format_exc())
    finally:
        # Unregister the connection
        await manager.disconnect(websocket, channel_id, "broadcast")
        logger.info("Broadcast connection cleaned up")
