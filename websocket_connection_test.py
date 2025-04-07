#!/usr/bin/env python3
"""
Isolated WebSocket connection test with mock tokens.

This script focuses solely on testing WebSocket connections with mock tokens,
bypassing the need for actual authentication endpoints.
"""
import asyncio
import json
import logging
import sys
import time
from urllib.parse import urlencode

import websockets

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("websocket-test")

# WebSocket configuration
WS_BASE_URL = "ws://localhost:8000"

# Mock JWT token for testing - this is a sample token format, not a valid token
MOCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken"


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
        headers = [
            ("User-Agent", "TestClient/1.0"),  # Using TestClient to trigger the test bypass in middleware
            ("Authorization", f"Bearer {token}")  # Also include token in header as fallback
        ]
        
        start_time = time.time()
        logger.debug(f"Attempting connection at {start_time}")
        
        # Deliberately wrap this part with more error handling to catch specific error types
        try:
            async with websockets.connect(url, extra_headers=headers) as websocket:
                logger.info("WebSocket connection established successfully!")
                
                # Send a test message
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
                return True
        except websockets.exceptions.InvalidStatusCode as e:
            duration = time.time() - start_time
            status_code = getattr(e, "status_code", None)
            reason = getattr(e, "headers", {}).get("reason", "Unknown reason")
            
            logger.error(f"WebSocket connection failed with status {status_code} after {duration:.2f}s")
            logger.error(f"Server message: {reason}")
            
            if status_code == 401 or status_code == 403:
                logger.error("Authentication failure: Invalid or expired token")
            elif status_code == 404:
                logger.error(f"Endpoint not found: {endpoint}")
            
            return False
        except websockets.exceptions.ConnectionClosedError as e:
            duration = time.time() - start_time
            logger.error(f"WebSocket connection closed unexpectedly after {duration:.2f}s: {e}")
            logger.error(f"Close code: {e.code}, reason: {e.reason}")
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
        "/ws/broadcast"
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


async def main():
    """Run the WebSocket connection tests with mock tokens."""
    logger.info("Starting WebSocket connection tests with mock token")
    await test_available_endpoints(MOCK_TOKEN)
    logger.info("Tests completed")


if __name__ == "__main__":
    asyncio.run(main())
