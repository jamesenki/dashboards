import argparse
import asyncio
import logging
import os
import socket
import sys
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

# Add the parent directory to sys.path when running from src/
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Database-backed operations API
from src.api.operations_router_db import router as operations_db_router

# Prediction Storage API
from src.api.prediction_storage import router as prediction_storage_api_router

# Predictions API
from src.api.predictions import router as predictions_api_router

# Basic vending machine management API
from src.api.vending_machine import router as vending_machine_api_router

# Polar Delight Ice Cream Machine operations API
from src.api.vending_machine_operations import (
    router as ice_cream_machine_operations_api_router,
)

# Realtime operations API
from src.api.vending_machine_realtime_operations import (
    router as vending_machine_realtime_operations_api_router,
)

# Now imports will work both when running from project root or from src/
# Water heater API endpoints - standard and configurable
from src.api.water_heater import router as water_heater_api_router
from src.api.water_heater.configurable_router import (
    router as configurable_water_heater_router,
)

# Water heater history API
from src.api.water_heater_history import router as water_heater_history_api_router

# Water heater operations API
from src.api.water_heater_operations import router as water_heater_operations_api_router

# Database initialization
from src.db.migration import initialize_db

# Debug routes for development
from src.routes.debug_routes import router as debug_router

# Web UI routes
from src.web.routes import router as web_router

# Create FastAPI app
app = FastAPI(
    title="IoTSphere API",
    description="API for IoT device management and real-time operational monitoring",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {
            "name": "Water Heaters",
            "description": "Endpoints for water heater device management",
        },
        {
            "name": "Operations",
            "description": "Real-time operational monitoring endpoints",
        },
        {
            "name": "Predictions",
            "description": "Machine learning prediction endpoints for maintenance and lifespan estimation",
        },
        {
            "name": "Vending Machines",
            "description": "Endpoints for vending machine device management",
        },
    ],
)


# Custom CORS middleware to ensure preflight requests work correctly
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)

        # Add CORS headers to every response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers[
            "Access-Control-Allow-Methods"
        ] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Content-Type, Authorization, Accept, X-Requested-With, Origin"
        response.headers[
            "Access-Control-Expose-Headers"
        ] = "Content-Length, Content-Type, X-Custom-Header"
        response.headers["Access-Control-Max-Age"] = "600"

        return response


# Add our custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Also keep the built-in CORS middleware as a fallback
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "X-Requested-With",
        "Origin",
    ],
    expose_headers=["Content-Length", "Content-Type", "X-Custom-Header"],
    max_age=600,
)

# Mount static files and set up templates
project_root = Path(__file__).parent.parent
static_dir = project_root / "frontend/static"
templates_dir = project_root / "frontend/templates"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Include routers under the API prefix
# Use configurable water heater router instead of the standard one
api_router.include_router(configurable_water_heater_router)
# Keep original router for backwards compatibility but with a different prefix
water_heater_api_router.prefix = "/v0/water-heaters"
api_router.include_router(water_heater_api_router)
api_router.include_router(water_heater_operations_api_router)
api_router.include_router(water_heater_history_api_router)
api_router.include_router(predictions_api_router)
api_router.include_router(prediction_storage_api_router)
api_router.include_router(vending_machine_api_router)
api_router.include_router(ice_cream_machine_operations_api_router)
api_router.include_router(vending_machine_realtime_operations_api_router)
# Include database-backed operations router
api_router.include_router(operations_db_router)
# Include debug routes
api_router.include_router(debug_router)

# Include API router and web router
app.include_router(api_router)
app.include_router(web_router)

# Monitoring dashboard routes are defined in src/web/routes.py

import logging
import os

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.initialize_db import initialize_database
from src.db.real_database import SQLiteDatabase

# Include router for model monitoring dashboard
from src.monitoring.dashboard_api import create_dashboard_api
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService

# Use the correct database implementation based on TDD principles
database_path = "data/iotsphere.db"
db = SQLiteDatabase(database_path)
logging.info(f"Using SQLite database at {database_path}")

# Create the repository chain for model monitoring
sqlite_repo = SQLiteModelMetricsRepository(db=db)

# Use configuration system to determine if we should use mock data
from src.config import config

use_mock_data = config.get("services.water_heater.use_mock_data", False)
logging.info(f"Using mock data: {use_mock_data}")

# Create the model metrics repository with the SQL adapter
metrics_repository = ModelMetricsRepository(sql_repo=sqlite_repo, test_mode=False)

# Create the monitoring service with our repository
monitoring_service = ModelMonitoringService(metrics_repository=metrics_repository)
model_monitoring_api = create_dashboard_api(monitoring_service)
app.mount("/api/monitoring", model_monitoring_api)


def setup_environment_configuration():
    """Set up environment-based configuration."""
    import logging
    from pathlib import Path

    from src.config import config as config_service
    from src.config.env_provider import EnvironmentFileProvider

    # Parse command-line arguments for environment
    parser = argparse.ArgumentParser(description="IoTSphere Application")
    parser.add_argument(
        "--env",
        type=str,
        default=os.environ.get("APP_ENV", "development"),
        help="Environment (development, staging, production)",
    )
    args, _ = parser.parse_known_args()

    # Set APP_ENV environment variable based on arguments
    os.environ["APP_ENV"] = args.env

    # Get project root directory
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"

    # Create environment file provider
    env_provider = EnvironmentFileProvider(config_dir, default_env=args.env)

    # Register provider with config service with high priority (50)
    config_service.register_provider(env_provider, priority=50)

    # Log the active environment
    logging.info(f"Application running in {env_provider.get_environment()} environment")

    return env_provider.get_environment()


@app.on_event("startup")
async def startup_event():
    """Initialize database and connections on startup."""
    import logging

    from src.db.config import db_settings

    # Set up environment configuration
    env = setup_environment_configuration()

    # Initialize database schema
    try:
        # Use db_settings for backward compatibility
        await initialize_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        fallback_enabled = config.get("database.fallback_to_mock", True)
        if not fallback_enabled and not db_settings.SUPPRESS_DB_CONNECTION_ERRORS:
            logging.error(f"Error initializing database: {e}")
        else:
            logging.info(
                f"Using fallback storage: Database connection not available: {e}"
            )

    # Load data from dummy repository to database if in development mode
    if env != "production":
        try:
            from src.scripts.load_data_to_postgres import load_devices

            await load_devices()
            logging.info("Sample data loaded to database successfully")
        except Exception as e:
            if not db_settings.SUPPRESS_DB_CONNECTION_ERRORS:
                logging.error(f"Error loading sample data: {e}")
            else:
                logging.info(f"Using in-memory storage with JSON persistence")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="IoTSphere Application")
    parser.add_argument(
        "--env",
        type=str,
        default=os.environ.get("APP_ENV", "development"),
        help="Environment (development, staging, production)",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", type=int, default=8006, help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Set APP_ENV environment variable
    os.environ["APP_ENV"] = args.env

    # Configure logging based on environment
    log_level = "INFO" if args.env == "production" else "DEBUG"
    logging.basicConfig(level=log_level)

    # Run the application
    reload_enabled = args.reload or args.env == "development"
    uvicorn.run("main:app", host=args.host, port=args.port, reload=reload_enabled)
