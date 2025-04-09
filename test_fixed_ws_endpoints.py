#!/usr/bin/env python
"""
Test script for the fixed IoTSphere WebSocket endpoints.

This script tests the fixed WebSocket endpoints that incorporate the lessons learned
from our test implementations.
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

# Test token (same as in other test scripts)
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken"

# Default server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


async def test_endpoint(endpoint_path, test_message=None):
    """Test a specific WebSocket endpoint."""
    logger.info(f"Testing endpoint: {endpoint_path}")

    # Build the WebSocket URL with token
    query_params = {"token": TEST_TOKEN}
    query_string = urlencode(query_params)
    ws_url = f"ws://{DEFAULT_HOST}:{DEFAULT_PORT}{endpoint_path}?{query_string}"

    logger.info(f"Connecting to: {ws_url}")

    try:
        # Connect to the WebSocket server with a shorter timeout
        async with websockets.connect(
            ws_url, ping_interval=None, open_timeout=5
        ) as websocket:
            logger.info("Connection established successfully!")

            # Wait for initial messages (connection info, state updates, etc.)
            try:
                connect_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                try:
                    data = json.loads(connect_message)
                    logger.info(
                        f"Received initial message: {json.dumps(data, indent=2)}"
                    )
                except json.JSONDecodeError:
                    logger.info(f"Received raw initial message: {connect_message}")
            except asyncio.TimeoutError:
                logger.warning("No initial message received (timeout)")

            # Send a test message if provided
            if test_message:
                await websocket.send(json.dumps(test_message))
                logger.info(f"Sent message: {json.dumps(test_message, indent=2)}")

                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    try:
                        data = json.loads(response)
                        logger.info(f"Received response: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError:
                        logger.info(f"Received raw response: {response}")
                except asyncio.TimeoutError:
                    logger.warning("No response received (timeout)")

            logger.info("Test successful for this endpoint!")
            return True
    except Exception as e:
        logger.error(f"Error for endpoint {endpoint_path}: {e}")
        return False
    finally:
        logger.info("------------------------------")


async def test_device_state():
    """Test the fixed device state endpoint with specific state operations."""
    endpoint = "/ws/fixed/devices/wh-d94a7707/state"

    # First test basic connection
    if not await test_endpoint(endpoint):
        return False

    # Then test specific state operations
    operations = [
        {
            "name": "Get current state",
            "message": {"type": "get_state", "device_id": "wh-d94a7707"},
        },
        {
            "name": "Update device state",
            "message": {
                "type": "update_state",
                "device_id": "wh-d94a7707",
                "state": {"temperature": 140.0, "mode": "vacation"},
            },
        },
    ]

    success_count = 0
    for op in operations:
        logger.info(f"Testing operation: {op['name']}")
        if await test_endpoint(endpoint, op["message"]):
            success_count += 1

    return success_count == len(operations)


async def test_fixed_endpoints():
    """Test all fixed WebSocket endpoints."""
    # Define test endpoints
    fixed_endpoints = ["/ws/fixed/devices/wh-d94a7707/state", "/ws/fixed/broadcast"]

    successes = 0
    failures = 0

    # Test message to send to each endpoint
    test_message = {
        "type": "test",
        "message": "Hello from fixed test client!",
        "timestamp": asyncio.get_event_loop().time(),
    }

    # Test each endpoint
    for endpoint in fixed_endpoints:
        result = await test_endpoint(endpoint, test_message)
        if result:
            successes += 1
        else:
            failures += 1

    # Special test for device state operations
    logger.info("=== Testing device state operations ===")
    if await test_device_state():
        logger.info("Device state operations test PASSED")
        successes += 1
    else:
        logger.info("Device state operations test FAILED")
        failures += 1

    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Successes: {successes}")
    logger.info(f"Failures: {failures}")
    logger.info(f"Total: {successes + failures}")

    return successes, failures


if __name__ == "__main__":
    """Run the fixed WebSocket endpoint tests."""
    # Run all tests by default
    asyncio.run(test_fixed_endpoints())
