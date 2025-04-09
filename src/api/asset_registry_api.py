"""
Asset Registry API

Provides HTTP endpoints for accessing and manipulating device metadata
stored in the Asset DB.
"""
import json
import logging
from typing import Any, Dict

from aiohttp import web

from src.services.asset_registry import AssetRegistryService

logger = logging.getLogger(__name__)

# Singleton service instance (would be better managed by dependency injection in production)
_asset_service = None


def get_asset_service() -> AssetRegistryService:
    """
    Get or create the Asset Registry Service instance.

    Returns:
        AssetRegistryService instance
    """
    global _asset_service
    if _asset_service is None:
        from src.infrastructure.events.event_bus import global_event_bus

        _asset_service = AssetRegistryService(event_bus=global_event_bus)
    return _asset_service


async def get_device_metadata(request) -> web.Response:
    """
    Get device metadata from the Asset Registry.

    Args:
        request: HTTP request containing device_id in URL path

    Returns:
        JSON response with device metadata or error
    """
    device_id = request.match_info.get("device_id")
    if not device_id:
        return web.json_response({"error": "Missing device ID"}, status=400)

    try:
        # Get asset registry service
        asset_service = get_asset_service()

        # Get device metadata
        metadata = await asset_service.get_device_info(device_id)

        # Return success response
        return web.json_response(metadata)

    except ValueError as e:
        # Handle device not found
        logger.warning(f"Device metadata not found: {device_id}")
        return web.json_response({"error": f"Device not found: {str(e)}"}, status=404)
    except Exception as e:
        # Handle other errors
        logger.error(f"Error retrieving device metadata: {e}")
        return web.json_response(
            {"error": f"Failed to retrieve device metadata: {str(e)}"}, status=500
        )


async def update_device_metadata(request) -> web.Response:
    """
    Update device metadata in the Asset Registry.

    Args:
        request: HTTP request containing device_id in URL path and metadata updates in body

    Returns:
        JSON response with updated device metadata or error
    """
    device_id = request.match_info.get("device_id")
    if not device_id:
        return web.json_response({"error": "Missing device ID"}, status=400)

    try:
        # Parse request body
        updates = await request.json()
        if not updates:
            return web.json_response({"error": "No updates provided"}, status=400)

        # Get asset registry service
        asset_service = get_asset_service()

        # Update device metadata
        updated_metadata = await asset_service.update_device_metadata(
            device_id, updates
        )

        # Return success response
        return web.json_response(updated_metadata)

    except ValueError as e:
        # Handle device not found
        logger.warning(f"Device not found for metadata update: {device_id}")
        return web.json_response({"error": f"Device not found: {str(e)}"}, status=404)
    except json.JSONDecodeError:
        # Handle invalid JSON
        logger.warning(f"Invalid JSON in request body for device: {device_id}")
        return web.json_response({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        # Handle other errors
        logger.error(f"Error updating device metadata: {e}")
        return web.json_response(
            {"error": f"Failed to update device metadata: {str(e)}"}, status=500
        )


async def register_routes(app):
    """
    Register API routes with the application.

    Args:
        app: The aiohttp web application
    """
    app.router.add_get("/api/devices/{device_id}/metadata", get_device_metadata)
    app.router.add_patch("/api/devices/{device_id}/metadata", update_device_metadata)
    app.router.add_put("/api/devices/{device_id}/metadata", update_device_metadata)
