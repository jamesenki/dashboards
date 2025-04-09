#!/usr/bin/env python3
"""
End-to-end WebSocket authentication test for IoTSphere.

This script:
1. Authenticates with the API to get a valid JWT token
2. Tests WebSocket connections using that token
3. Provides detailed logs of the authentication and connection process
"""
import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import websockets
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("websocket-test")

# API and WebSocket configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"
LOGIN_ENDPOINT = "/api/auth/login"
TEST_USERNAME = "admin@example.com"  # Update with a valid username
TEST_PASSWORD = "admin123"  # Update with a valid password


class TokenResponse(BaseModel):
    """Model for token response"""

    access_token: str
    token_type: str
    expires_in: int


async def get_auth_token() -> Optional[str]:
    """
    Authenticate with the API and get a JWT token.

    Returns:
        JWT token string if successful, None otherwise
    """
    try:
        logger.info(f"Authenticating with {API_BASE_URL}{LOGIN_ENDPOINT}")

        async with httpx.AsyncClient() as client:
            # First try form data authentication
            form_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}

            response = await client.post(
                f"{API_BASE_URL}{LOGIN_ENDPOINT}",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                # If form data fails, try JSON authentication
                json_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}

                response = await client.post(
                    f"{API_BASE_URL}{LOGIN_ENDPOINT}", json=json_data
                )

            logger.debug(f"Auth response status: {response.status_code}")

            if response.status_code == 200:
                try:
                    # Try to parse as JSON first
                    data = response.json()
                    logger.info("Successfully authenticated")
                    logger.debug(f"Response data: {data}")

                    # Handle different token response formats
                    token = None
                    if isinstance(data, dict):
                        if "access_token" in data:
                            token = data["access_token"]
                        elif "token" in data:
                            token = data["token"]

                    if token:
                        logger.info(f"Successfully retrieved token: {token[:10]}...")
                        return token
                    else:
                        logger.error("Token not found in response")
                except Exception as e:
                    logger.error(f"Error parsing auth response: {e}")
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                logger.debug(f"Response content: {response.text}")

    except Exception as e:
        logger.error(f"Error during authentication: {e}")

    return None


async def test_websocket_connection(token: str, endpoint: str) -> bool:
    """
    Test a WebSocket connection with authentication.

    Args:
        token: JWT token for authentication
        endpoint: WebSocket endpoint to connect to

    Returns:
        True if connection was successful, False otherwise
    """
    # Add token to URL query parameters
    url = f"{WS_BASE_URL}{endpoint}"
    if "?" in url:
        url += f"&token={token}"
    else:
        url += f"?token={token}"

    logger.info(f"Testing WebSocket connection to: {url}")

    try:
        # Connect with token in URL
        headers = {"User-Agent": "WebSocketTest/1.0"}

        start_time = time.time()
        logger.debug(f"Attempting connection at {start_time}")

        async with websockets.connect(url, extra_headers=headers) as websocket:
            logger.info("WebSocket connection established successfully!")

            # Send a ping message
            ping_message = json.dumps({"type": "ping", "timestamp": time.time()})
            await websocket.send(ping_message)
            logger.info(f"Sent message: {ping_message}")

            # Wait for a response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received response: {response}")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")

            # Connection was successful since we got here
            await websocket.close()
            return True

    except websockets.exceptions.WebSocketException as e:
        duration = time.time() - start_time
        logger.error(f"WebSocket error after {duration:.2f}s: {e}")

        # Parse the error and provide more details
        if isinstance(e, websockets.exceptions.InvalidStatusCode):
            status_code = getattr(e, "status_code", None)
            if status_code:
                if status_code == 401 or status_code == 403:
                    logger.error(f"Authentication failed with status {status_code}")
                elif status_code == 404:
                    logger.error(f"Endpoint not found (404): {endpoint}")
                else:
                    logger.error(f"Server returned HTTP {status_code}")

        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


async def test_available_endpoints(token: str):
    """
    Test all available WebSocket endpoints.

    Args:
        token: JWT token for authentication
    """
    # List of endpoints to test
    endpoints = [
        "/ws/devices/wh-d94a7707/state",
        "/ws/devices/wh-d94a7707/telemetry",
        "/ws/devices/wh-d94a7707/alerts",
        "/ws/broadcast",
    ]

    # Test each endpoint
    results = {}
    for endpoint in endpoints:
        logger.info(f"\n=== Testing endpoint: {endpoint} ===")
        success = await test_websocket_connection(token, endpoint)
        results[endpoint] = "SUCCESS" if success else "FAILED"

    # Print summary
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    for endpoint, result in results.items():
        logger.info(f"{endpoint}: {result}")


async def debug_auth_flow():
    """Test the full authentication and WebSocket connection flow."""
    # Step 1: Get an authentication token
    token = await get_auth_token()
    if not token:
        logger.error("Failed to get authentication token. Test aborted.")
        return

    # Step 2: Test WebSocket connections
    await test_available_endpoints(token)


if __name__ == "__main__":
    logger.info("Starting end-to-end WebSocket test")
    asyncio.run(debug_auth_flow())
    logger.info("Test completed")
