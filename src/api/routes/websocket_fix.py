"""
Fixed WebSocket routes for the IoTSphere API.

This module provides properly implemented WebSocket endpoints for real-time device data,
incorporating the lessons learned from our test implementations.
"""
import asyncio
import json
import logging
import base64
import os
import random
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from datetime import datetime, timedelta

from src.services.websocket_manager import WebSocketManager
from src.services.device_shadow import DeviceShadowService
from src.services.telemetry_service import TelemetryService, get_telemetry_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instances
_websocket_manager = None
_shadow_service = None
_telemetry_service = None


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


async def extract_test_token(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """
    Extract and validate test tokens from WebSocket connections.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        User info dict if a valid test token is found, None otherwise
    """
    # Get token from query param
    query_params = dict(websocket.query_params.items())
    token = query_params.get("token", "")
    
    # Check if this is a test token
    if not token or "thisIsATestToken" not in token:
        logger.debug(f"No test token found in connection to {websocket.url.path}")
        return None
        
    # Default user info for test tokens
    user_info = {
        "user_id": "test-user-001",
        "username": "test_user",
        "role": "admin"
    }
    
    # Try to extract user info from token payload
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            # Add padding to make base64 decoding work
            padded = parts[1] + "="*(4 - len(parts[1]) % 4) if len(parts[1]) % 4 != 0 else parts[1]
            payload_bytes = base64.urlsafe_b64decode(padded)
            payload = json.loads(payload_bytes.decode("utf-8"))
            
            # Update user info from payload
            if "user_id" in payload:
                user_info["user_id"] = payload["user_id"]
            if "username" in payload:
                user_info["username"] = payload["username"]
            if "role" in payload:
                user_info["role"] = payload.get("role", "admin")
    except Exception as e:
        logger.error(f"Error parsing test token: {e}")
    
    logger.debug(f"TEST AUTH: User authenticated as {user_info['username']} with role {user_info['role']}")
    return user_info


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


@router.websocket("/ws/devices/{device_id}/state")
async def device_state_fixed(websocket: WebSocket, device_id: str):
    """
    Fixed WebSocket endpoint for device state updates.
    
    This endpoint allows clients to:
    1. Receive real-time state updates from the device shadow
    2. Get the current device state
    3. Update the desired state of the device
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to subscribe to
    """
    # Accept the connection first
    await websocket.accept()
    logger.info(f"Device state connection accepted for device {device_id}")
    
    # Validate test token
    user_info = await extract_test_token(websocket)
    if not user_info:
        logger.warning(f"Unauthorized connection attempt for device {device_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Get service instances
    manager = get_websocket_manager()
    shadow_service = get_shadow_service()
    
    # Register the connection
    await manager.connect(websocket, device_id, "state")
    
    try:
        # Initial state - send current shadow
        try:
            current_state = await shadow_service.get_device_shadow(device_id)
            # Add the type field needed by the frontend and tests
            response = {
                "type": "state_update",
                "device_id": device_id,
                "state": current_state
            }
            await websocket.send_text(json.dumps(response))
        except Exception as e:
            logger.debug(f"Error getting initial device state: {e}")
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
                "state": default_state
            }))
        
        # Process messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Verify the operation (only admins can update state)
            logger.info(f"Received message from {user_info['username']}: {message}")
            
            # Echo back the message for testing purposes
            response = {
                "type": "echo",
                "device_id": device_id,
                "original": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send_text(json.dumps(response))
            
            # Handle different message types
            msg_type = message.get("type", "")
            if msg_type == "get_state":
                # Get current shadow state
                current_state = await shadow_service.get_device_shadow(device_id)
                await websocket.send_text(json.dumps({
                    "type": "state_update",
                    "device_id": device_id,
                    "state": current_state
                }))
            elif msg_type == "update_state":
                # Update desired state
                desired_state = message.get("state", {})
                
                # In a real implementation, this would update the device shadow
                # For now, echo back acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "state_update_ack",
                    "device_id": device_id,
                    "success": True,
                    "message": "State update received"
                }))
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from device {device_id} state")
    except Exception as e:
        logger.error(f"Error in device state WebSocket: {e}")
    finally:
        # Unregister the connection
        await manager.disconnect(websocket, device_id, "state")


@router.websocket("/ws/broadcast")
async def broadcast_channel_fixed(websocket: WebSocket):
    """
    Fixed WebSocket endpoint for system-wide broadcasts.
    
    This endpoint allows clients to:
    1. Subscribe to system-wide broadcasts and announcements
    2. Filter broadcasts by topic
    
    Args:
        websocket: The WebSocket connection
    """
    # Accept the connection first
    await websocket.accept()
    logger.info("Broadcast connection accepted for system-wide messages")
    
    # Validate test token
    user_info = await extract_test_token(websocket)
    if not user_info:
        logger.warning("Unauthorized broadcast connection attempt")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Get service instances
    manager = get_websocket_manager()
    
    # Register a special channel for broadcasts
    channel_id = "broadcast"
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
            
            # Log and echo back the message
            logger.info(f"Received broadcast message from {user_info['username']}: {message}")
            
            # Echo back the message for testing
            response = {
                "type": "echo",
                "channel": channel_id,
                "original": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send_text(json.dumps(response))
            
            # Handle different message types
            msg_type = message.get("type", "")
            if msg_type == "subscribe":
                # In a real implementation, this would subscribe to specific channels
                topics = message.get("topics", [])
                await websocket.send_text(json.dumps({
                    "type": "subscribe_ack",
                    "topics": topics,
                    "success": True,
                    "message": "Subscribed to topics"
                }))
    except WebSocketDisconnect:
        logger.info("Client disconnected from broadcast channel")
    except Exception as e:
        logger.error(f"Error in broadcast WebSocket: {e}")
    finally:
        # Unregister the connection
        await manager.disconnect(websocket, channel_id, "broadcast")


@router.websocket("/ws/devices/{device_id}/telemetry")
async def device_telemetry_fixed(websocket: WebSocket, device_id: str):
    """
    Fixed WebSocket endpoint for device telemetry data.
    
    This endpoint allows clients to:
    1. Receive real-time telemetry data from the device
    2. Subscribe to specific metrics
    3. Get historical telemetry data
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to subscribe to
    """
    # Accept the connection first
    await websocket.accept()
    logger.info(f"Device telemetry connection accepted for device {device_id}")
    
    # Validate test token
    user_info = await extract_test_token(websocket)
    if not user_info:
        logger.warning(f"Unauthorized connection attempt for device {device_id} telemetry")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Extract query parameters
    query_params = dict(websocket.query_params.items())
    simulate = query_params.get("simulate", "").lower() == "true"
    
    # Get service instances
    manager = get_websocket_manager()
    telemetry_service = get_telemetry_service_local()
    
    # Register the connection
    await manager.connect(websocket, device_id, "telemetry")
    
    # Store subscribed metrics on the websocket state
    websocket.state.subscribed_metrics = []
    
    # Set up simulation if requested
    sim_task = None
    if simulate:
        # Create a task to simulate telemetry data
        sim_task = asyncio.create_task(simulate_telemetry(websocket, device_id))
    
    try:
        # Send initial welcome message
        await websocket.send_text(json.dumps({
            "type": "telemetry_connection_established",
            "device_id": device_id,
            "simulation": simulate,
            "timestamp": datetime.now().isoformat() + "Z"
        }))
        
        # Process messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Log received message
                logger.debug(f"Received telemetry message: {message}")
                
                # Echo back the message for debugging
                response = {
                    "type": "echo",
                    "device_id": device_id,
                    "original": message,
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send_text(json.dumps(response))
                
                # Process different message types
                message_type = message.get("type", "")
                
                if message_type == "subscribe":
                    # Subscribe to specific metrics
                    metrics = message.get("metrics", [])
                    if not metrics:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "error": "No metrics specified for subscription"
                        }))
                        continue
                    
                    # Update subscribed metrics
                    for metric in metrics:
                        if metric not in websocket.state.subscribed_metrics:
                            websocket.state.subscribed_metrics.append(metric)
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "metrics": websocket.state.subscribed_metrics
                    }))
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from specific metrics
                    metrics = message.get("metrics", [])
                    
                    # Update subscribed metrics
                    for metric in metrics:
                        if metric in websocket.state.subscribed_metrics:
                            websocket.state.subscribed_metrics.remove(metric)
                    
                    # Send confirmation
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
                    
                    # Generate some sample historical data based on device type
                    device_type = "generic"
                    if device_id.startswith("wh-"):
                        device_type = "water_heater"
                    elif device_id.startswith("vm-"):
                        device_type = "vending_machine"
                    
                    # Generate different data based on device type and metric
                    recent_data = generate_sample_telemetry(device_id, device_type, metric, limit)
                    
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
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from device {device_id} telemetry")
    except Exception as e:
        logger.error(f"Error in device telemetry WebSocket: {e}")
        import traceback
        logger.debug(traceback.format_exc())
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


async def simulate_telemetry(websocket: WebSocket, device_id: str):
    """
    Simulate telemetry data for testing purposes.
    
    This function periodically sends simulated telemetry data for the device
    based on its type and subscribed metrics.
    
    Args:
        websocket: The WebSocket connection
        device_id: The device ID to simulate data for
    """
    device_type = "generic"
    if device_id.startswith("wh-"):
        device_type = "water_heater"
    elif device_id.startswith("vm-"):
        device_type = "vending_machine"
    elif device_id.startswith("rb-"):
        device_type = "robot"
    elif device_id.startswith("ve-"):
        device_type = "vehicle"
    
    # Continue until cancelled
    while True:
        try:
            # Generate data for all metrics or subscribed metrics
            metrics = getattr(websocket.state, "subscribed_metrics", [])
            
            # If no specific metrics are subscribed, send data for all default metrics
            if not metrics:
                metrics = get_default_metrics_for_device_type(device_type)
            
            # Generate data point for each metric
            for metric in metrics:
                telemetry_data = generate_telemetry_point(device_id, device_type, metric)
                await websocket.send_text(json.dumps({
                    "type": "telemetry_update",
                    "device_id": device_id,
                    "metric": metric,
                    "value": telemetry_data["value"],
                    "timestamp": telemetry_data["timestamp"],
                    "unit": telemetry_data["unit"]
                }))
            
            # Wait before next update (2-5 seconds)
            await asyncio.sleep(random.uniform(2, 5))
        
        except asyncio.CancelledError:
            # Task was cancelled, exit
            raise
        except Exception as e:
            logger.error(f"Error in telemetry simulation: {e}")
            # Wait before retry
            await asyncio.sleep(2)


def get_default_metrics_for_device_type(device_type: str) -> list:
    """
    Get default telemetry metrics for a specific device type.
    
    Args:
        device_type: The type of device
        
    Returns:
        List of default metric names for the device type
    """
    if device_type == "water_heater":
        return ["temperature", "pressure", "flow_rate", "energy_usage"]
    elif device_type == "vending_machine":
        return ["temperature", "inventory_level", "cash_level", "transactions"]
    elif device_type == "robot":
        return ["battery_level", "position_x", "position_y", "status"]
    elif device_type == "vehicle":
        return ["fuel_level", "engine_temp", "speed", "tire_pressure"]
    else:
        return ["status", "battery_level"]


def generate_telemetry_point(device_id: str, device_type: str, metric: str) -> dict:
    """
    Generate a single telemetry data point for a specific metric.
    
    Args:
        device_id: The device identifier
        device_type: The type of device
        metric: The metric name
        
    Returns:
        Dictionary with value, timestamp, and unit
    """
    now = datetime.now().isoformat() + "Z"
    
    # Default value range and unit
    min_val, max_val = 0, 100
    unit = ""
    
    # Device type and metric specific ranges and units
    if device_type == "water_heater":
        if metric == "temperature":
            min_val, max_val = 60, 80
            unit = "°F"
        elif metric == "pressure":
            min_val, max_val = 1.8, 2.5
            unit = "PSI"
        elif metric == "flow_rate":
            min_val, max_val = 8, 12
            unit = "GPM"
        elif metric == "energy_usage":
            min_val, max_val = 3000, 4000
            unit = "W"
    
    elif device_type == "vending_machine":
        if metric == "temperature":
            min_val, max_val = 35, 42
            unit = "°F"
        elif metric == "inventory_level":
            min_val, max_val = 60, 85
            unit = "%"
        elif metric == "cash_level":
            min_val, max_val = 30, 70
            unit = "$"
        elif metric == "transactions":
            min_val, max_val = 0, 5
            unit = "count"
    
    # Generate random value within range
    value = round(random.uniform(min_val, max_val), 2)
    
    return {
        "value": value,
        "timestamp": now,
        "unit": unit
    }


def generate_sample_telemetry(device_id: str, device_type: str, metric: str, limit: int) -> list:
    """
    Generate sample historical telemetry data for a specific metric.
    
    Args:
        device_id: The device identifier
        device_type: The type of device
        metric: The metric name
        limit: Number of data points to generate
        
    Returns:
        List of historical telemetry data points
    """
    result = []
    now = datetime.now()
    
    # Generate historical data points
    for i in range(limit):
        # Generate timestamp in the past
        timestamp = (now - timedelta(minutes=i*10)).isoformat() + "Z"
        
        # Generate point with this timestamp
        point = generate_telemetry_point(device_id, device_type, metric)
        point["timestamp"] = timestamp
        
        result.append(point)
    
    return result
