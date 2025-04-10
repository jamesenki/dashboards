#!/usr/bin/env python3
"""
System Configuration API Routes

This module provides API endpoints for system configuration data including
WebSocket connection information.
"""

import os

from fastapi import APIRouter, Request

router = APIRouter(
    prefix="/api/system",
    tags=["System"],
    responses={404: {"description": "Not found"}},
)


@router.get("/websocket-config")
async def get_websocket_config(request: Request):
    """
    Get WebSocket configuration information for frontend clients.

    Returns the currently active WebSocket port and other connection details,
    which enables the frontend to connect to the correct WebSocket server
    regardless of which port was selected during server startup.

    This is especially important when the server has tried multiple ports
    due to conflicts.
    """
    # Get the active WebSocket port from environment variable or use default
    ws_port = os.environ.get("ACTIVE_WS_PORT", "9090")

    # Get the WebSocket service from app state if available
    websocket_service = getattr(request.app.state, "websocket_service", None)
    if websocket_service:
        # If service is available, get actual port from the service
        ws_port = str(websocket_service.port)

    return {"port": ws_port, "status": "active" if websocket_service else "unavailable"}
