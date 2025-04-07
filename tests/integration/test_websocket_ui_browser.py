import pytest
import asyncio
import json
import time
from playwright.async_api import Page, expect
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.services.device_shadow import DeviceShadowService
from src.services.websocket_manager import WebSocketManager

"""
Browser tests for WebSocket UI integration
These tests verify that the UI elements are correctly updated when WebSocket messages are received
"""

# Mock data for device shadow
MOCK_DEVICE_DATA = {
    "device_id": "test-device-001",
    "name": "Test Water Heater",
    "reported": {
        "temperature": 55.0,
        "mode": "ECO",
        "heater_status": "STANDBY",
        "connection_status": "online",
        "current_temperature": 52.5,
        "target_temperature": 55.0
    },
    "desired": {},
    "version": 1
}

# Mock telemetry data
MOCK_TELEMETRY = {
    "metric": "temperature",
    "value": 58.5,
    "timestamp": "2025-04-06T12:30:00Z"
}

@pytest.fixture
async def test_page(page: Page):
    """
    Setup a test page with mocked backend API and WebSocket endpoints
    """
    # Start a test server with mocked API routes
    with patch('src.api.routes.websocket.get_shadow_service') as mock_get_shadow:
        # Setup shadow service mock
        mock_service = AsyncMock()
        mock_service.get_device_shadow.return_value = MOCK_DEVICE_DATA
        mock_service.update_device_shadow.return_value = MOCK_DEVICE_DATA
        mock_get_shadow.return_value = mock_service
        
        # Setup websocket manager mock
        with patch('src.api.routes.websocket.get_websocket_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            # Create test server and configure routes
            client = TestClient(app)
            
            # Override the API endpoint for water heater details
            with patch('src.api.routes.water_heaters.get_water_heater_by_id') as mock_get_heater:
                mock_get_heater.return_value = {
                    "id": "test-device-001",
                    "name": "Test Water Heater",
                    "manufacturer": "AquaTech",
                    "model": "AT-5500",
                    "serial_number": "AT55-123456",
                    "status": "online",
                    "heater_status": "STANDBY",
                    "current_temperature": 52.5,
                    "target_temperature": 55.0,
                    "mode": "ECO",
                    "min_temperature": 40.0,
                    "max_temperature": 80.0,
                    "installation_date": "2025-01-15",
                    "last_updated": "2025-04-06T14:22:00Z"
                }
                
                # Navigate to the detail page
                await page.goto("http://localhost:8000/water-heaters/test-device-001")
                
                # Wait for the page to load
                await page.wait_for_selector(".detail-view", timeout=5000)
                
                yield page


@pytest.mark.asyncio
async def test_water_heater_detail_websocket_updates(test_page: Page):
    """
    Test that WebSocket updates are correctly reflected in the UI
    """
    # Mock websocket communication
    await test_page.evaluate("""() => {
        // Mock the WebSocket class
        window.originalWebSocket = window.WebSocket;
        window.mockSockets = {};
        
        window.WebSocket = function(url) {
            const mockSocket = {
                url: url,
                onopen: null,
                onmessage: null,
                onclose: null,
                onerror: null,
                readyState: 0, // CONNECTING
                send: function(data) {
                    console.log('Mock WebSocket send:', data);
                    // Store the data sent for later verification
                    if (!this.sentData) this.sentData = [];
                    this.sentData.push(data);
                },
                close: function() {
                    if (this.onclose) this.onclose({});
                    this.readyState = 3; // CLOSED
                }
            };
            
            // Store the mock socket for later access
            window.mockSockets[url] = mockSocket;
            
            // Simulate connection
            setTimeout(() => {
                mockSocket.readyState = 1; // OPEN
                if (mockSocket.onopen) mockSocket.onopen({});
            }, 50);
            
            return mockSocket;
        };
    }""")
    
    # Wait for WebSocket connection to be established (look for the status indicator)
    await test_page.wait_for_selector("#websocket-status.connected", timeout=5000)
    
    # Verify initial temperature is displayed
    temperature_element = test_page.locator("#temperature-value")
    await expect(temperature_element).to_have_text("52.5°C")
    
    # Simulate receiving a temperature update via WebSocket
    await test_page.evaluate("""() => {
        // Get the telemetry WebSocket
        const telemetrySocket = Object.values(window.mockSockets).find(s => 
            s.url.includes('/telemetry'));
        
        if (telemetrySocket && telemetrySocket.onmessage) {
            // Send mock telemetry data
            telemetrySocket.onmessage({
                data: JSON.stringify({
                    metric: 'temperature',
                    value: 58.5,
                    timestamp: '2025-04-06T14:23:00Z'
                })
            });
        }
    }""")
    
    # Verify the temperature display updates
    await expect(temperature_element).to_have_text("58.5°C", timeout=2000)
    
    # Simulate receiving a state update via WebSocket
    await test_page.evaluate("""() => {
        // Get the state WebSocket
        const stateSocket = Object.values(window.mockSockets).find(s => 
            s.url.includes('/state'));
        
        if (stateSocket && stateSocket.onmessage) {
            // Send mock state update
            stateSocket.onmessage({
                data: JSON.stringify({
                    reported: {
                        heater_status: 'HEATING'
                    }
                })
            });
        }
    }""")
    
    # Verify the heater status indicator updates
    heater_status_indicator = test_page.locator("#heater-status-indicator")
    await expect(heater_status_indicator).to_have_class(/status-heating/, timeout=2000)
    
    # Check the heater status label
    heater_status_label = test_page.locator("#heater-status-label")
    await expect(heater_status_label).to_have_text("Heating", timeout=2000)
    
    # Clean up mock
    await test_page.evaluate("""() => {
        window.WebSocket = window.originalWebSocket;
        delete window.mockSockets;
    }""")


@pytest.mark.asyncio
async def test_websocket_connection_indicator(test_page: Page):
    """
    Test that the WebSocket connection status indicator is updated correctly
    """
    # Verify initial connection state (should be connected after setup)
    connection_status = test_page.locator("#websocket-status")
    await expect(connection_status).to_have_class(/connected/, timeout=5000)
    
    # Simulate WebSocket disconnection
    await test_page.evaluate("""() => {
        // Get all WebSockets
        const sockets = Object.values(window.mockSockets);
        
        // Simulate disconnection for all sockets
        sockets.forEach(socket => {
            if (socket.onclose) {
                socket.readyState = 3; // CLOSED
                socket.onclose({});
            }
        });
    }""")
    
    # Verify connection indicator shows disconnected
    await expect(connection_status).to_have_class(/disconnected/, timeout=2000)
    
    # Clean up mock
    await test_page.evaluate("""() => {
        window.WebSocket = window.originalWebSocket;
        delete window.mockSockets;
    }""")
