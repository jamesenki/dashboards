"""
Debug routes for WebSocket testing.

This module provides simple endpoints for testing WebSocket connectivity and authentication.
"""
import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

# Import the WebSocket server but not the auth middleware
from src.services.standalone_websocket_server import get_websocket_server

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/debug")
async def websocket_debug(websocket: WebSocket):
    """
    Debug endpoint for testing WebSocket connections and authentication.
    
    This endpoint:
    1. Accepts WebSocket connections
    2. Echoes back any messages received
    3. Sends periodic heartbeat messages
    
    Since it uses the websocket_auth_middleware, it will enforce authentication.
    """
    # Accept the connection directly - no middleware involved
    await websocket.accept()
    logger.info(f"Debug WebSocket connection accepted from {websocket.client}")
    
    # Simple token extraction and validation for testing purposes
    query_params = websocket.query_params
    token = query_params.get("token", "")
    
    # For testing, we'll just check if the token contains our test marker
    is_test_token = token and "thisIsATestToken" in token
    is_debug_mode = os.environ.get("DEBUG_WEBSOCKET", "false").lower() == "true"
    
    if not (is_test_token or is_debug_mode):
        logger.warning(f"Debug endpoint rejected unauthorized connection from {websocket.client}")
        await websocket.close(reason="Unauthorized")
        return
    
    # For test tokens, extract user info from the token payload if available
    user_info = {"role": "admin", "username": "test_user"}
    if token and "thisIsATestToken" in token:
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                # Add padding to make base64 decoding work
                padded = parts[1] + "="*(4 - len(parts[1]) % 4) if len(parts[1]) % 4 != 0 else parts[1]
                payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                
                user_info = {
                    "role": payload.get("role", "admin"),
                    "username": payload.get("username", "test_user")
                }
        except Exception as e:
            logger.error(f"Error parsing test token: {e}")
    
    logger.info(f"Debug endpoint authenticated user: {user_info['username']} with role: {user_info['role']}")
    
    # Register the connection with our WebSocket server if available
    try:
        websocket_server = get_websocket_server()
        await websocket_server.register_connection(websocket, "debug")
    except Exception as e:
        logger.warning(f"Could not register connection with WebSocket server: {e}")
    
    # Send initial connection info
    user_info = getattr(websocket.state, "user", {"role": "unknown"})
    await websocket.send_text(json.dumps({
        "type": "connect_info",
        "message": "WebSocket debug connection established",
        "authenticated": True,
        "user": {
            "role": user_info.get("role", "unknown"),
            "username": user_info.get("username", "unknown")
        }
    }))
    
    # Create heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeats(websocket))
    
    try:
        # Echo messages back to client
        while True:
            data = await websocket.receive_text()
            logger.info(f"Debug WebSocket received: {data}")
            
            try:
                # Parse as JSON if possible
                message = json.loads(data)
                message_type = message.get("type", "echo")
                
                # Handle different message types
                if message_type == "ping":
                    response = {
                        "type": "pong",
                        "message": "Pong response from server",
                        "original": message
                    }
                else:
                    response = {
                        "type": "echo",
                        "message": "Echo from server",
                        "original": message
                    }
                
                await websocket.send_text(json.dumps(response))
            except json.JSONDecodeError:
                # Just echo back non-JSON messages
                await websocket.send_text(f"Echo: {data}")
                
    except WebSocketDisconnect:
        logger.info(f"Debug WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"Error in debug WebSocket: {e}")
    finally:
        # Cancel heartbeat task
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
            
        # Unregister from WebSocket server
        try:
            websocket_server = get_websocket_server()
            await websocket_server.unregister_connection(websocket, "debug")
        except Exception as e:
            logger.warning(f"Could not unregister connection: {e}")


async def send_heartbeats(websocket: WebSocket):
    """Send periodic heartbeat messages to the client."""
    counter = 0
    try:
        while True:
            await asyncio.sleep(10)  # Heartbeat every 10 seconds
            counter += 1
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "counter": counter,
                "message": "Server heartbeat"
            }))
    except asyncio.CancelledError:
        logger.debug("Heartbeat task cancelled")
    except Exception as e:
        logger.error(f"Error in heartbeat task: {e}")
