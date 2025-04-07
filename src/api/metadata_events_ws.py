"""
Metadata Events WebSocket Handler

Provides a WebSocket endpoint for subscribing to real-time
metadata changes for a specific device.
"""
import json
import logging
import asyncio
from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)

def get_asset_service():
    """
    Get the Asset Registry Service instance.
    
    Returns:
        AssetRegistryService instance
    """
    # Import here to avoid circular imports
    from src.api.asset_registry_api import get_asset_service as get_service
    return get_service()

async def metadata_events_ws_handler(request, ws):
    """
    WebSocket handler for device metadata events.
    
    Allows clients to subscribe to real-time updates for device metadata.
    Each client subscribes to updates for a specific device.
    
    Args:
        request: HTTP request that initiated the WebSocket connection
        ws: WebSocket connection
        
    Returns:
        WebSocket response
    """
    # Get device ID from request path
    device_id = request.match_info.get('device_id')
    if not device_id:
        logger.error("Missing device ID in WebSocket request")
        await ws.close(code=1003, message=b'Missing device ID')
        return ws
    
    # Get the asset service
    asset_service = get_asset_service()
    
    # Flag to track if we're still connected
    is_connected = True
    
    # Track pending messages
    pending = set()
    
    # Create a lock for thread-safe operations
    lock = asyncio.Lock()
    
    # Define the metadata change callback
    async def on_metadata_change(event_data):
        # Only process events for the device we're subscribed to
        if event_data.get('device_id') != device_id:
            return
            
        # Log the event
        logger.debug(f"Received metadata event for {device_id}: {event_data['change_type']}")
        
        # Send the event to the WebSocket client
        if is_connected:
            try:
                # Serialize the event data to JSON
                message = json.dumps(event_data)
                
                # Acquire lock before sending
                async with lock:
                    await ws.send_str(message)
                    
                logger.debug(f"Sent metadata event to client: {device_id}")
            except Exception as e:
                logger.error(f"Error sending metadata event to WebSocket: {e}")
    
    # Non-async wrapper for the callback
    def metadata_callback(event_data):
        # Create a task to handle the event
        task = asyncio.create_task(on_metadata_change(event_data))
        pending.add(task)
        task.add_done_callback(pending.discard)
    
    # Subscribe to metadata changes
    try:
        # Register our callback with the asset service
        asset_service.subscribe_to_metadata_changes(metadata_callback)
        logger.info(f"Subscribed to metadata changes for device: {device_id}")
        
        # Send initial connection message
        await ws.send_str(json.dumps({
            "type": "connection_established",
            "device_id": device_id,
            "message": "Subscribed to metadata updates"
        }))
        
        # Handle incoming WebSocket messages
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                # Handle any messages from the client
                # Currently just used for keep-alive and future extensions
                logger.debug(f"Received message from client: {msg.data}")
                
                # Echo back as acknowledgment
                if msg.data == "ping":
                    await ws.send_str("pong")
                    
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
                
            elif msg.type == WSMsgType.CLOSE:
                logger.info(f"WebSocket closed by client for device: {device_id}")
                break
    
    except asyncio.CancelledError:
        # Handle graceful shutdown
        logger.info(f"WebSocket connection cancelled for device: {device_id}")
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error in metadata WebSocket handler: {e}")
        
    finally:
        # Cleanup
        is_connected = False
        
        # Cancel any pending tasks
        for task in pending:
            task.cancel()
        
        # Unsubscribe from metadata changes
        try:
            asset_service.unsubscribe_from_metadata_changes(metadata_callback)
            logger.info(f"Unsubscribed from metadata changes for device: {device_id}")
        except Exception as e:
            logger.error(f"Error unsubscribing from metadata changes: {e}")
        
        # Ensure WebSocket is closed
        if not ws.closed:
            await ws.close()
            
    return ws

async def register_routes(app):
    """
    Register WebSocket routes with the application.
    
    Args:
        app: The aiohttp web application
    """
    app.router.add_get('/api/events/device/{device_id}/metadata', 
                      lambda r: web.WebSocketResponse()(r, metadata_events_ws_handler))
