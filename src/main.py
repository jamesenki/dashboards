import sys
import os
import sys
import uvicorn
import socket
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path

# Add the parent directory to sys.path when running from src/
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Now imports will work both when running from project root or from src/
# Water heater API endpoints
from src.api.water_heater import router as water_heater_api_router
# Basic vending machine management API
from src.api.vending_machine import router as vending_machine_api_router
# Polar Delight Ice Cream Machine operations API
from src.api.vending_machine_operations import router as ice_cream_machine_operations_api_router
# Realtime operations API
from src.api.vending_machine_realtime_operations import router as vending_machine_realtime_operations_api_router
# Web UI routes
from src.web.routes import router as web_router

# Create FastAPI app
app = FastAPI(title="IoTSphere API", description="API for IoT device management")

# Custom CORS middleware to ensure preflight requests work correctly
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)
        
        # Add CORS headers to every response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With, Origin"
        response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Type, X-Custom-Header"
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
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
    expose_headers=["Content-Length", "Content-Type", "X-Custom-Header"],
    max_age=600,
)

# Mount static files
project_root = Path(__file__).parent.parent
static_dir = project_root / "frontend/static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Include routers under the API prefix
api_router.include_router(water_heater_api_router)
api_router.include_router(vending_machine_api_router)
api_router.include_router(ice_cream_machine_operations_api_router)
api_router.include_router(vending_machine_realtime_operations_api_router)

# Include API router and web router
app.include_router(api_router)
app.include_router(web_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
