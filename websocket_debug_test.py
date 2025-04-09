#!/usr/bin/env python
"""
A simple WebSocket client to test the WebSocket debug endpoint.

This script connects to the WebSocket debug endpoint and sends/receives messages.
It's designed to help debug WebSocket authentication and connection issues.
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
DEFAULT_HOST = "127.0.0.1"  # Using IPv4 address explicitly
DEFAULT_PORT = 8000
DEFAULT_PATH = "/ws/devices/wh-d94a7707/state"


async def test_websocket_connection(
    host=DEFAULT_HOST, port=DEFAULT_PORT, path=DEFAULT_PATH, token=TEST_TOKEN
):
    """Test WebSocket connection with authentication token."""
    # Build the WebSocket URL with token
    query_params = {"token": token}
    query_string = urlencode(query_params)
    ws_url = f"ws://{host}:{port}{path}?{query_string}"

    logger.info(f"Connecting to: {ws_url}")

    try:
        # Connect to the WebSocket server
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            logger.info("Connection established successfully!")

            # Send a test message
            test_message = {"type": "test", "message": "Hello from the test client!"}
            await websocket.send(json.dumps(test_message))
            logger.info(f"Sent message: {test_message}")

            # Receive messages for 5 seconds
            for _ in range(5):
                try:
                    # Set a timeout for the receive operation
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    try:
                        # Try to parse as JSON
                        data = json.loads(response)
                        logger.info(f"Received message: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError:
                        # Not JSON
                        logger.info(f"Received raw message: {response}")
                except asyncio.TimeoutError:
                    logger.info("No message received (timeout)")

            logger.info("Test completed successfully")
            return True

    except ConnectionRefusedError:
        logger.error(f"Connection refused to {ws_url}")
        logger.error(
            "Make sure the server is running and listening on the specified host and port"
        )

    except websockets.exceptions.InvalidStatusCode as e:
        status_code = getattr(e, "status_code", "unknown")
        logger.error(
            f"Server rejected WebSocket connection with status code: {status_code}"
        )
        if status_code == 403:
            logger.error("Authentication failed - check your token")
        elif status_code == 404:
            logger.error("Endpoint not found - check the path")

    except Exception as e:
        logger.error(f"Error during WebSocket connection: {e}")

    return False


async def test_multiple_endpoints():
    """Test multiple WebSocket endpoints."""
    endpoints = [
        "/ws/debug",
        "/ws/devices/wh-d94a7707/state",
        "/ws/devices/wh-d94a7707/telemetry",
        "/ws/devices/wh-d94a7707/alerts",
        "/ws/broadcast",
    ]

    successes = 0
    failures = 0

    for path in endpoints:
        logger.info(f"Testing endpoint: {path}")
        result = await test_websocket_connection(path=path)

        if result:
            successes += 1
        else:
            failures += 1

        logger.info("------------------------------")

    logger.info(f"Test Summary: {successes} successes, {failures} failures")

    return successes, failures


if __name__ == "__main__":
    """Run the WebSocket test."""
    # Check if a specific endpoint was provided
    if len(sys.argv) > 1:
        path = sys.argv[1]
        asyncio.run(test_websocket_connection(path=path))
    else:
        # Test the debug endpoint only by default
        asyncio.run(test_websocket_connection())
