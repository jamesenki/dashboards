"""
Setup module for device shadow API components.

This module provides a function to set up all device shadow API components
in the FastAPI application, following the dependency injection pattern.
"""
import logging

from fastapi import FastAPI

from src.api.device_shadow import router as device_shadow_router
from src.services.device_update_handler import DeviceUpdateHandler
from src.services.frontend_request_handler import FrontendRequestHandler
from src.services.shadow_notification_service import ShadowNotificationService

logger = logging.getLogger(__name__)


def setup_shadow_api(app: FastAPI):
    """
    Set up all device shadow API components in the FastAPI application.

    This function:
    1. Registers the device shadow API router
    2. Sets up the necessary services if not already available

    Args:
        app: FastAPI application instance
    """
    logger.info("Setting up device shadow API")

    # Register the device shadow API router
    app.include_router(device_shadow_router)

    # Make sure required services are initialized
    if not hasattr(app.state, "shadow_service"):
        logger.warning(
            "Shadow service not found in app state, API will not function properly"
        )

    if not hasattr(app.state, "ws_manager"):
        logger.warning(
            "WebSocket manager not found in app state, real-time updates will not work"
        )

    # Initialize frontend request handler if not already present
    if not hasattr(app.state, "frontend_request_handler") and hasattr(
        app.state, "shadow_service"
    ):
        app.state.frontend_request_handler = FrontendRequestHandler(
            shadow_service=app.state.shadow_service
        )
        logger.info("Initialized frontend request handler")

    # Initialize device update handler if not already present
    if not hasattr(app.state, "device_update_handler") and hasattr(
        app.state, "shadow_service"
    ):
        app.state.device_update_handler = DeviceUpdateHandler(
            shadow_service=app.state.shadow_service
        )
        logger.info("Initialized device update handler")

    # Initialize shadow notification service if not already present
    if (
        not hasattr(app.state, "shadow_notification_service")
        and hasattr(app.state, "shadow_service")
        and hasattr(app.state, "ws_manager")
    ):
        app.state.shadow_notification_service = ShadowNotificationService(
            shadow_service=app.state.shadow_service, ws_manager=app.state.ws_manager
        )
        logger.info("Initialized shadow notification service")

    logger.info("Device shadow API setup complete")
