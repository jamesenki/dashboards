#!/usr/bin/env python
"""
Test script for device WebSocket endpoints.

This script tests the device state WebSocket endpoint directly with a known device ID.
"""
import asyncio
import json
import logging
import sys
from urllib.parse import urlencode

import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test token (same as in the test_websocket.sh script)
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken"

# Default server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


async def test_device_endpoint():
    """Test specific device WebSocket endpoints."""
    # Device ID to test with
    device_id = "wh-d94a7707"

    # Try multiple endpoints for this device
    endpoints = [
        f"/ws/devices/{device_id}/state",
        f"/ws/devices/{device_id}/telemetry",
        f"/ws/devices/{device_id}/alerts",
    ]

    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")

        # Build the WebSocket URL with token
        query_params = {"token": TEST_TOKEN, "debug": "true"}
        query_string = urlencode(query_params)
        ws_url = f"ws://{DEFAULT_HOST}:{DEFAULT_PORT}{endpoint}?{query_string}"

        logger.info(f"Connecting to: {ws_url}")

        try:
            # Connect to the WebSocket server with a shorter timeout
            async with websockets.connect(
                ws_url, ping_interval=None, open_timeout=5
            ) as websocket:
                logger.info("Connection established successfully!")

                # Send a test message
                test_message = {"type": "ping", "message": "Test connection"}
                await websocket.send(json.dumps(test_message))
                logger.info(f"Sent message: {test_message}")

                # Wait for a response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    try:
                        data = json.loads(response)
                        logger.info(f"Received: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError:
                        logger.info(f"Received raw message: {response}")

                    logger.info("Test successful for this endpoint!")
                except asyncio.TimeoutError:
                    logger.warning("No response received (timeout)")

        except Exception as e:
            logger.error(f"Error for endpoint {endpoint}: {e}")

        logger.info("------------------------------")

    # Also test the broadcast endpoint
    broadcast_endpoint = "/ws/broadcast"
    logger.info(f"Testing endpoint: {broadcast_endpoint}")

    # Build the WebSocket URL with token
    query_params = {"token": TEST_TOKEN, "debug": "true"}
    query_string = urlencode(query_params)
    ws_url = f"ws://{DEFAULT_HOST}:{DEFAULT_PORT}{broadcast_endpoint}?{query_string}"

    logger.info(f"Connecting to: {ws_url}")

    try:
        # Connect to the WebSocket server with a shorter timeout
        async with websockets.connect(
            ws_url, ping_interval=None, open_timeout=5
        ) as websocket:
            logger.info("Connection established successfully!")

            # Send a test message
            test_message = {"type": "ping", "message": "Test broadcast connection"}
            await websocket.send(json.dumps(test_message))
            logger.info(f"Sent message: {test_message}")

            # Wait for a response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                try:
                    data = json.loads(response)
                    logger.info(f"Received: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    logger.info(f"Received raw message: {response}")

                logger.info("Broadcast test successful!")
            except asyncio.TimeoutError:
                logger.warning("No response received from broadcast (timeout)")

    except Exception as e:
        logger.error(f"Error for broadcast endpoint: {e}")

    logger.info("------------------------------")


if __name__ == "__main__":
    """Run all device endpoint tests."""
    asyncio.run(test_device_endpoint())
