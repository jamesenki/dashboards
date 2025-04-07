"""
API Routes Configuration

Registers all API routes with the application.
"""
import logging

logger = logging.getLogger(__name__)

async def register_all_routes(app):
    """
    Register all API routes with the application.
    
    Args:
        app: The aiohttp web application
    """
    # Import route registrars
    from src.api.shadow_document_api import register_routes as register_shadow_routes
    from src.api.asset_registry_api import register_routes as register_asset_routes
    from src.api.metadata_events_ws import register_routes as register_metadata_ws_routes
    
    # Register routes
    await register_shadow_routes(app)
    await register_asset_routes(app)
    await register_metadata_ws_routes(app)
    
    logger.info("All API routes registered")
