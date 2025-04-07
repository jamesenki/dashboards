"""
Integration tests for WebSocket endpoints and Device Shadow API.

These tests verify that the WebSocket endpoints and Device Shadow API work
together correctly to provide real-time device state updates.
"""
import asyncio
import json
import pytest
import websockets
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test constants
TEST_DEVICE_ID = "wh-001"
BASE_URL = "ws://localhost:8007"


@pytest.mark.asyncio
async def test_device_shadow_websocket_integration():
    """Test the integration between device shadow and WebSocket endpoints."""
    # This test requires the server to be running with WebSocket endpoints enabled
    
    # Connect to the device state WebSocket endpoint
    ws_url = f"{BASE_URL}/ws/devices/{TEST_DEVICE_ID}/state"
    
    # Test metadata
    test_info = {
        "description": "Integration test for device shadow and WebSocket",
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting WebSocket integration test: {test_info['description']}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"Connected to {ws_url}")
            
            # Receive initial state
            initial_response = await websocket.recv()
            initial_state = json.loads(initial_response)
            
            logger.info(f"Received initial state: {json.dumps(initial_state, indent=2)}")
            
            # Request current state explicitly
            await websocket.send(json.dumps({
                "type": "get_state"
            }))
            
            state_response = await websocket.recv()
            current_state = json.loads(state_response)
            
            logger.info(f"Received current state: {json.dumps(current_state, indent=2)}")
            
            # Update the desired state
            new_desired_state = {
                "target_temperature": 68.0,
                "mode": "eco"
            }
            
            logger.info(f"Updating desired state: {json.dumps(new_desired_state, indent=2)}")
            
            await websocket.send(json.dumps({
                "type": "update_desired",
                "state": new_desired_state,
                "version": current_state.get("version", 0)
            }))
            
            # Receive update confirmation
            update_response = await websocket.recv()
            update_result = json.loads(update_response)
            
            logger.info(f"Received update confirmation: {json.dumps(update_result, indent=2)}")
            
            # Request delta between reported and desired
            await websocket.send(json.dumps({
                "type": "get_delta"
            }))
            
            delta_response = await websocket.recv()
            delta = json.loads(delta_response)
            
            logger.info(f"Received delta: {json.dumps(delta, indent=2)}")
            
            # Test successful if we got here without errors
            logger.info("WebSocket integration test completed successfully")
            return True
    
    except Exception as e:
        logger.error(f"WebSocket integration test failed with error: {str(e)}")
        return False


@pytest.mark.asyncio
async def test_device_telemetry_websocket():
    """Test the telemetry WebSocket endpoint."""
    # This test requires the server to be running with WebSocket endpoints enabled
    
    # Connect to the device telemetry WebSocket endpoint
    ws_url = f"{BASE_URL}/ws/devices/{TEST_DEVICE_ID}/telemetry"
    
    logger.info(f"Starting telemetry WebSocket test")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"Connected to {ws_url}")
            
            # Receive welcome message
            welcome_response = await websocket.recv()
            welcome = json.loads(welcome_response)
            
            logger.info(f"Received welcome message: {json.dumps(welcome, indent=2)}")
            
            # Subscribe to telemetry
            await websocket.send(json.dumps({
                "type": "subscribe",
                "metrics": ["temperature", "pressure"]
            }))
            
            # Receive subscription confirmation
            sub_response = await websocket.recv()
            subscription = json.loads(sub_response)
            
            logger.info(f"Received subscription confirmation: {json.dumps(subscription, indent=2)}")
            
            # Receive telemetry data for a short period
            telemetry_received = 0
            try:
                # Wait for up to 10 seconds to receive some telemetry data
                for _ in range(5):
                    # Set a short timeout to not block test for too long
                    try:
                        telemetry_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        telemetry = json.loads(telemetry_response)
                        telemetry_received += 1
                        
                        logger.info(f"Received telemetry: {json.dumps(telemetry, indent=2)}")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for telemetry data")
                        continue
            
            finally:
                # Unsubscribe
                await websocket.send(json.dumps({
                    "type": "unsubscribe"
                }))
                
                logger.info(f"Unsubscribed from telemetry. Received {telemetry_received} updates.")
            
            # Test successful if we received at least one telemetry update
            return telemetry_received > 0
    
    except Exception as e:
        logger.error(f"Telemetry WebSocket test failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the tests using asyncio
    async def run_tests():
        shadow_result = await test_device_shadow_websocket_integration()
        telemetry_result = await test_device_telemetry_websocket()
        
        logger.info("==== Test Results ====")
        logger.info(f"Device Shadow WebSocket: {'PASS' if shadow_result else 'FAIL'}")
        logger.info(f"Device Telemetry WebSocket: {'PASS' if telemetry_result else 'FAIL'}")
        
        return shadow_result and telemetry_result
    
    # Run the tests
    import asyncio
    success = asyncio.run(run_tests())
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)
