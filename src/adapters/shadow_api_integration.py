"""
Shadow API Integration Module

This module provides functions to integrate the ShadowApiAdapter
with the FastAPI application following Clean Architecture principles.
"""
import logging
from typing import Optional

from fastapi import FastAPI

from src.adapters.shadow_api_adapter import ShadowApiAdapter
from src.infrastructure.client.shadow_client_adapter import ShadowClientAdapter
from src.infrastructure.messaging.message_broker_adapter import MessageBrokerAdapter
from src.infrastructure.messaging.shadow_broker_integration import (
    ShadowBrokerIntegration,
)
from src.services.device_shadow import DeviceShadowService
from src.services.shadow_change_stream_listener import ShadowChangeStreamListener
from src.services.shadow_notification_service import ShadowNotificationService

logger = logging.getLogger(__name__)


def get_shadow_api_adapter() -> ShadowApiAdapter:
    """
    Factory function to create a ShadowApiAdapter instance.

    This function centralizes the creation of the adapter and its dependencies.

    Returns:
        A configured ShadowApiAdapter instance
    """
    # Get the required dependencies
    message_broker = MessageBrokerAdapter(
        host="localhost", port=5672, username="guest", password="guest"
    )

    change_stream_listener = ShadowChangeStreamListener(
        connection_uri="mongodb://localhost:27017",
        database_name="iotsphere",
        collection_name="device_shadows",
    )

    shadow_broker = ShadowBrokerIntegration(
        change_stream_listener=change_stream_listener,
        message_broker=message_broker,
        topic_prefix="iotsphere.devices",
    )

    notification_service = ShadowNotificationService()

    # Create and return the adapter
    return ShadowApiAdapter(
        shadow_broker_integration=shadow_broker,
        shadow_notification_service=notification_service,
        base_ws_url="ws://localhost:8000/api/ws/shadows",
    )


def setup_shadow_api_adapter(
    app: FastAPI, shadow_adapter: Optional[ShadowApiAdapter] = None
) -> None:
    """
    Set up the ShadowApiAdapter in a FastAPI application.

    This function integrates the adapter with the FastAPI dependency injection system.

    Args:
        app: The FastAPI application
        shadow_adapter: Optional pre-configured ShadowApiAdapter instance
    """
    logger.info("Setting up Shadow API Adapter")

    # Create or use the provided adapter
    adapter = shadow_adapter or get_shadow_api_adapter()

    # Store in the application state for dependency injection
    app.state.shadow_service = adapter

    # Set up the WebSocket manager if it doesn't exist
    if not hasattr(app.state, "ws_manager"):
        logger.info("Setting up WebSocket manager for shadow updates")
        app.state.ws_manager = adapter.notification_service

    # Register the shadow API routes to match the test expectations
    # Use the original device_shadow module's setup_routes to ensure test compatibility
    from src.api.device_shadow import setup_routes

    setup_routes(app)

    logger.info(
        "Shadow API Adapter and routes setup complete with proper test compatibility"
    )
