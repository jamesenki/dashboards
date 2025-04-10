"""
Main API router for the IoTSphere application.

This module integrates all API controllers into a single router
following Clean Architecture principles.
"""
from fastapi import APIRouter

from src.api.controllers.device_shadow_controller import router as device_shadow_router
from src.api.controllers.water_heater_controller import router as water_heater_router

# Create the main API router
api_router = APIRouter()

# Include all controller routers
api_router.include_router(water_heater_router)
api_router.include_router(device_shadow_router)
