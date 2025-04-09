"""
No-authentication WebSocket endpoints for testing purposes.

This module provides simple endpoints for testing WebSocket connectivity without authentication,
which is useful for isolating connection issues from authentication issues.
"""
import asyncio
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/noauth")
async def websocket_noauth(websocket: WebSocket):
    """
    Debug endpoint with no authentication for basic connectivity testing.

    This endpoint:
    1. Accepts WebSocket connections without any authentication
    2. Echoes back any messages received
    3. Sends periodic heartbeat messages

    WARNING: This endpoint should NEVER be used in production as it has no security.
    """
    await websocket.accept()
    logger.warning(
        f"NO-AUTH WebSocket connection accepted from {websocket.client} - FOR TESTING ONLY"
    )

    # Send initial connection info
    await websocket.send_text(
        json.dumps(
            {
                "type": "connect_info",
                "message": "WebSocket NO-AUTH connection established (testing only)",
                "authenticated": False,
                "warning": "This is an unauthenticated connection for testing only",
            }
        )
    )

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeats(websocket))

    try:
        # Echo messages back to client
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message from {websocket.client}: {message}")

            # Try to parse as JSON
            try:
                data = json.loads(message)
                # Echo with timestamp
                response = {
                    "type": "echo",
                    "original": data,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(response))
            except json.JSONDecodeError:
                # Not JSON, echo as string
                await websocket.send_text(f"Echo: {message}")

    except WebSocketDisconnect:
        logger.info(f"NO-AUTH WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"Error in NO-AUTH WebSocket: {e}")
    finally:
        # Cancel heartbeat task
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


async def send_heartbeats(websocket: WebSocket):
    """Send heartbeat messages to the client every 30 seconds."""
    count = 0
    while True:
        try:
            count += 1
            heartbeat = {
                "type": "heartbeat",
                "count": count,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await websocket.send_text(json.dumps(heartbeat))
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            break
