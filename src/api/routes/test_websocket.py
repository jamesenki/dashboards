"""
Test WebSocket routes for the IoTSphere API.

This module provides simplified WebSocket endpoints for testing WebSocket functionality,
with relaxed authentication specifically for test environments.
"""
import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter()
logger = logging.getLogger(__name__)


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
        logger.warning("No test token found in connection")
        return None

    # Default user info for test tokens
    user_info = {"user_id": "test-user-001", "username": "test_user", "role": "admin"}

    # Try to extract user info from token payload
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            # Add padding to make base64 decoding work
            padded = (
                parts[1] + "=" * (4 - len(parts[1]) % 4)
                if len(parts[1]) % 4 != 0
                else parts[1]
            )
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

    logger.info(
        f"TEST AUTH: User authenticated as {user_info['username']} with role {user_info['role']}"
    )
    return user_info


@router.websocket("/ws/test/device/{device_id}")
async def test_device_endpoint(websocket: WebSocket, device_id: str):
    """
    Test WebSocket endpoint for device data.

    This endpoint allows testing of device WebSocket functionality with test tokens.

    Args:
        websocket: The WebSocket connection
        device_id: The device ID
    """
    # Accept the connection first
    await websocket.accept()
    logger.info(f"Test device endpoint connection accepted for device {device_id}")

    # Validate test token
    user_info = await extract_test_token(websocket)
    if not user_info:
        logger.warning(f"Unauthorized test connection attempt for device {device_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Send initial connection info
    await websocket.send_text(
        json.dumps(
            {
                "type": "connect_info",
                "message": f"Test device connection established for {device_id}",
                "device_id": device_id,
                "authenticated": True,
                "user": user_info,
            }
        )
    )

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeats(websocket, device_id))

    try:
        # Echo messages back to client
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message from {device_id}: {message}")

            # Try to parse as JSON
            try:
                data = json.loads(message)
                # Echo with timestamp and device info
                response = {
                    "type": "echo",
                    "device_id": device_id,
                    "original": data,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(response))

                # If it's a command, send mock response
                if data.get("type") == "command":
                    await asyncio.sleep(1)  # Simulate processing time
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "command_response",
                                "device_id": device_id,
                                "command_id": data.get("command_id", "unknown"),
                                "status": "success",
                                "timestamp": asyncio.get_event_loop().time(),
                            }
                        )
                    )
            except json.JSONDecodeError:
                # Not JSON, echo as string
                await websocket.send_text(f"Echo: {message}")

    except WebSocketDisconnect:
        logger.info(f"Test client disconnected for device {device_id}")
    except Exception as e:
        logger.error(f"Error in test device WebSocket: {e}")
    finally:
        # Cancel heartbeat task
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


@router.websocket("/ws/test/broadcast")
async def test_broadcast_endpoint(websocket: WebSocket):
    """
    Test WebSocket endpoint for broadcast messages.

    This endpoint allows testing of broadcast WebSocket functionality with test tokens.

    Args:
        websocket: The WebSocket connection
    """
    # Accept the connection first
    await websocket.accept()
    logger.info("Test broadcast endpoint connection accepted")

    # Validate test token
    user_info = await extract_test_token(websocket)
    if not user_info:
        logger.warning("Unauthorized test broadcast connection attempt")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Send initial connection info
    await websocket.send_text(
        json.dumps(
            {
                "type": "connect_info",
                "message": "Test broadcast connection established",
                "authenticated": True,
                "user": user_info,
            }
        )
    )

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeats(websocket, "broadcast"))

    try:
        # Echo messages back to client
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received broadcast message: {message}")

            # Try to parse as JSON
            try:
                data = json.loads(message)
                # Echo with timestamp
                response = {
                    "type": "echo",
                    "channel": "broadcast",
                    "original": data,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(response))
            except json.JSONDecodeError:
                # Not JSON, echo as string
                await websocket.send_text(f"Echo: {message}")

    except WebSocketDisconnect:
        logger.info("Test broadcast client disconnected")
    except Exception as e:
        logger.error(f"Error in test broadcast WebSocket: {e}")
    finally:
        # Cancel heartbeat task
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


async def send_heartbeats(websocket: WebSocket, channel: str):
    """Send heartbeat messages to the client every 30 seconds."""
    count = 0
    while True:
        try:
            count += 1
            heartbeat = {
                "type": "heartbeat",
                "channel": channel,
                "count": count,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await websocket.send_text(json.dumps(heartbeat))
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            break
