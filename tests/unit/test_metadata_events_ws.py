#!/usr/bin/env python3
"""
Unit tests for the metadata events WebSocket handler.
Testing the WebSocket endpoint that provides real-time metadata updates.
"""
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Import the WebSocket handler
from src.api.metadata_events_ws import metadata_events_ws_handler


class TestMetadataEventsWebSocket:
    """Tests for the metadata events WebSocket endpoint."""
    
    @pytest.fixture
    def mock_asset_service(self):
        """Create a mock asset registry service."""
        service = MagicMock()
        return service
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = MagicMock()
        ws.send_str = AsyncMock()
        ws.receive = AsyncMock()
        return ws
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock()
        request.match_info = {"device_id": "wh-test-001"}
        return request
    
    @pytest.mark.asyncio
    async def test_metadata_ws_subscription(self, mock_asset_service, mock_websocket, mock_request):
        """Test WebSocket subscription to metadata changes."""
        # Setup the mock service to track callbacks
        callbacks = []
        
        def subscribe_side_effect(callback):
            callbacks.append(callback)
            
        mock_asset_service.subscribe_to_metadata_changes.side_effect = subscribe_side_effect
        
        # Setup receive message to return close message after one normal message
        mock_websocket.receive.side_effect = [
            MagicMock(type="websocket.receive", data="ping"),
            MagicMock(type="websocket.close")
        ]
        
        # Patch the asset service getter
        with patch('src.api.metadata_events_ws.get_asset_service', 
                  return_value=mock_asset_service):
            # Start the handler in a task so we can interrupt it
            handler_task = asyncio.create_task(
                metadata_events_ws_handler(mock_request, mock_websocket)
            )
            
            # Give the handler time to set up the subscription
            await asyncio.sleep(0.1)
            
            # Verify the service method was called
            mock_asset_service.subscribe_to_metadata_changes.assert_called_once()
            
            # Should have one subscriber
            assert len(callbacks) == 1
            
            # Simulate a metadata change event
            event_data = {
                "device_id": "wh-test-001",
                "change_type": "location_update",
                "old_value": {"room": "304B"},
                "new_value": {"room": "401A"},
                "timestamp": 1712511490.123  # Example timestamp
            }
            
            # Call the callback that was registered
            callbacks[0](event_data)
            
            # Give time for the event to be processed
            await asyncio.sleep(0.1)
            
            # Verify the message was sent to the WebSocket
            mock_websocket.send_str.assert_called_once()
            sent_message = mock_websocket.send_str.call_args[0][0]
            sent_data = json.loads(sent_message)
            
            assert sent_data["device_id"] == "wh-test-001"
            assert sent_data["change_type"] == "location_update"
            assert sent_data["new_value"]["room"] == "401A"
            
            # Simulate a message from the client (ping)
            # The handler is already set up to receive this in the side_effect
            
            # Unsubscribe by closing the task
            handler_task.cancel()
            try:
                await handler_task
            except asyncio.CancelledError:
                pass
            
            # Verify unsubscribe was called
            mock_asset_service.unsubscribe_from_metadata_changes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metadata_ws_device_filter(self, mock_asset_service, mock_websocket, mock_request):
        """Test that WebSocket only receives events for the subscribed device."""
        # Setup the mock service to track callbacks
        callbacks = []
        
        def subscribe_side_effect(callback):
            callbacks.append(callback)
            
        mock_asset_service.subscribe_to_metadata_changes.side_effect = subscribe_side_effect
        
        # Setup to close after receiving
        mock_websocket.receive.side_effect = [
            MagicMock(type="websocket.close")
        ]
        
        # Patch the asset service getter
        with patch('src.api.metadata_events_ws.get_asset_service', 
                  return_value=mock_asset_service):
            # Start the handler in a task so we can control when it ends
            handler_task = asyncio.create_task(
                metadata_events_ws_handler(mock_request, mock_websocket)
            )
            
            # Give the handler time to set up the subscription
            await asyncio.sleep(0.1)
            
            # Simulate a metadata change event for a different device
            # This should be filtered out and not sent
            wrong_device_event = {
                "device_id": "wh-test-002",  # Different device ID
                "change_type": "firmware_update",
                "old_value": "1.0.0",
                "new_value": "1.1.0",
                "timestamp": 1712511490.123
            }
            
            # Call the callback that was registered
            callbacks[0](wrong_device_event)
            
            # Give time for the event to be processed
            await asyncio.sleep(0.1)
            
            # Verify that no message was sent to the WebSocket
            mock_websocket.send_str.assert_not_called()
            
            # Now try with the correct device ID
            correct_device_event = {
                "device_id": "wh-test-001",  # Matching device ID
                "change_type": "firmware_update",
                "old_value": "1.0.0",
                "new_value": "1.1.0",
                "timestamp": 1712511490.123
            }
            
            # Call the callback again
            callbacks[0](correct_device_event)
            
            # Give time for the event to be processed
            await asyncio.sleep(0.1)
            
            # Verify that this time a message was sent
            mock_websocket.send_str.assert_called_once()
            
            # Unsubscribe by closing the task
            handler_task.cancel()
            try:
                await handler_task
            except asyncio.CancelledError:
                pass
