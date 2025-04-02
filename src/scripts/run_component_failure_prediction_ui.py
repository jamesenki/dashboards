"""
Demo script to visualize component failure prediction UI.

This script starts a FastAPI server that displays the component failure prediction
UI with real water heater data from the database.
"""
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.db.connection import get_db_session
from src.db.models import DeviceModel, DiagnosticCodeModel
from src.models.device import DeviceType
from src.models.water_heater import WaterHeater, WaterHeaterType
from src.predictions.interfaces import PredictionResult
from src.predictions.maintenance.component_failure import ComponentFailurePrediction
from src.web.templates.component_failure_prediction import (
    ComponentFailurePredictionComponent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(debug=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Current time function for templates
def get_current_time():
    return datetime.now()

# Store prediction results to avoid recomputing for demo
prediction_cache: Dict[str, PredictionResult] = {}


async def get_all_water_heaters():
    """Retrieve all water heaters from the database."""
    async with get_db_session() as session:
        stmt = (
            DeviceModel.__table__.select()
            .where(DeviceModel.type == DeviceType.WATER_HEATER.value)
        )
        result = await session.execute(stmt)
        return result.fetchall()


async def get_device_details(device_id: str) -> Dict[str, Any]:
    """Get detailed device information including diagnostic codes."""
    async with get_db_session() as session:
        # Get device info
        stmt = DeviceModel.__table__.select().where(DeviceModel.id == device_id)
        result = await session.execute(stmt)
        device = result.fetchone()

        if not device:
            return {}

        # Get diagnostic codes
        stmt = DiagnosticCodeModel.__table__.select().where(
            DiagnosticCodeModel.device_id == device_id
        )
        result = await session.execute(stmt)
        diagnostic_codes = result.fetchall()

        return {
            "device": device,
            "diagnostic_codes": diagnostic_codes,
        }


async def generate_prediction_for_device(device_id: str) -> PredictionResult:
    """Generate component failure prediction for a device."""
    # Use cached prediction if available
    if device_id in prediction_cache:
        return prediction_cache[device_id]

    # Get device details
    details = await get_device_details(device_id)
    device = details.get("device")

    if not device:
        logger.warning(f"Device {device_id} not found")
        return None

    try:
        # Create predictor
        predictor = ComponentFailurePrediction()

        # Generate telemetry features (simplified for demo)
        features = {
            "temperature": np.random.normal(60, 5, 24).tolist(),  # Last 24 hours of temp readings
            "pressure": np.random.normal(2.5, 0.2, 24).tolist(),  # Last 24 hours of pressure readings
            "energy_usage": np.random.normal(1200, 100, 24).tolist(),  # Last 24 hours of energy usage
            "flow_rate": np.random.normal(8, 1, 24).tolist(),  # Last 24 hours of flow rate
            "heating_cycles": np.random.normal(15, 2, 24).tolist(),  # Last 24 hours of heating cycles
            "total_operation_hours": float(device.properties.get("total_operation_hours", 8760)),  # Default to 1 year
            "water_heater_type": device.properties.get("heater_type", WaterHeaterType.RESIDENTIAL.value),
        }

        # Predict component failure
        prediction = await predictor.predict(device_id, features)

        # Cache prediction
        prediction_cache[device_id] = prediction

        return prediction
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        # Return a default prediction with error information
        return PredictionResult(
            prediction_type="component_failure",
            device_id=device_id,
            predicted_value=0.5,  # Default 50% probability
            confidence=0.5,
            features_used=[],
            timestamp=datetime.now(),
            recommended_actions=[],
            raw_details={
                "components": {
                    "heating_element": 0.5,
                    "thermostat": 0.5,
                    "pressure_valve": 0.5,
                    "anode_rod": 0.5,
                    "tank_integrity": 0.5
                },
                "error": str(e)
            }
        )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with the list of water heaters."""
    try:
        water_heaters = await get_all_water_heaters()

        html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Water Heater Component Failure Prediction</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1140px;
                margin: 0 auto;
                padding: 0 15px;
            }}
            .mt-5 {{ margin-top: 3rem; }}
            .mb-4 {{ margin-bottom: 1.5rem; }}
            .mb-2 {{ margin-bottom: 0.5rem; }}
            .mb-3 {{ margin-bottom: 1rem; }}
            .mb-1 {{ margin-bottom: 0.25rem; }}
            .mt-4 {{ margin-top: 1.5rem; }}
            .ms-2 {{ margin-left: 0.5rem; }}
            .me-2 {{ margin-right: 0.5rem; }}
            .me-1 {{ margin-right: 0.25rem; }}
            .py-4 {{ padding-top: 1.5rem; padding-bottom: 1.5rem; }}
            .py-2 {{ padding-top: 0.5rem; padding-bottom: 0.5rem; }}
            .pt-2 {{ padding-top: 0.5rem; }}
            .row {{ display: flex; flex-wrap: wrap; margin-right: -15px; margin-left: -15px; }}
            .col-md-4, .col-md-8 {{ position: relative; width: 100%; padding-right: 15px; padding-left: 15px; }}
            @media (min-width: 768px) {{ .col-md-4 {{ flex: 0 0 33.333333%; max-width: 33.333333%; }} }}
            @media (min-width: 768px) {{ .col-md-8 {{ flex: 0 0 66.666667%; max-width: 66.666667%; }} }}
            h1, h5, h6 {{ margin-top: 0; }}
            .card {{ position: relative; display: flex; flex-direction: column; min-width: 0; word-wrap: break-word; background-color: #fff; background-clip: border-box; border: 1px solid rgba(0,0,0,.125); border-radius: 0.25rem; margin-bottom: 1rem; }}
            .card-header {{ padding: 0.75rem 1.25rem; margin-bottom: 0; background-color: rgba(0,0,0,.03); border-bottom: 1px solid rgba(0,0,0,.125); display: flex; justify-content: space-between; align-items: center; }}
            .card-body {{ flex: 1 1 auto; padding: 1.25rem; }}
            .card-title {{ margin-bottom: 0; }}
            .list-group {{ display: flex; flex-direction: column; padding-left: 0; margin-bottom: 0; border-radius: 0.25rem; }}
            .list-group-item {{ position: relative; display: block; padding: 0.75rem 1.25rem; background-color: #fff; border: 1px solid rgba(0,0,0,.125); }}
            .list-group-item:first-child {{ border-top-left-radius: inherit; border-top-right-radius: inherit; }}
            .list-group-item:last-child {{ border-bottom-right-radius: inherit; border-bottom-left-radius: inherit; }}
            .list-group-item-primary {{ color: #004085; background-color: #b8daff; }}
            .list-group-item-action {{ width: 100%; color: #495057; text-align: inherit; text-decoration: none; }}
            .list-group-item-action:hover {{ color: #495057; background-color: #f8f9fa; }}
            .badge {{ display: inline-block; padding: 0.25em 0.4em; font-size: 75%; font-weight: 700; line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: 0.25rem; }}
            .bg-secondary {{ background-color: #6c757d; color: white; }}
            .bg-primary {{ background-color: #007bff; color: white; }}
            .bg-danger {{ background-color: #dc3545; color: white; }}
            .bg-warning {{ background-color: #ffc107; color: #212529; }}
            .bg-success {{ background-color: #28a745; color: white; }}
            .bg-info {{ background-color: #17a2b8; color: white; }}
            .bg-dark {{ background-color: #343a40; color: white; }}
            .text-white {{ color: white; }}
            .text-muted {{ color: #6c757d; }}
            .text-center {{ text-align: center; }}
            .text-end {{ text-align: right; }}
            .text-nowrap {{ white-space: nowrap; }}
            .alert {{ position: relative; padding: 0.75rem 1.25rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: 0.25rem; }}
            .alert-warning {{ color: #856404; background-color: #fff3cd; border-color: #ffeeba; }}
            .alert-danger {{ color: #721c24; background-color: #f8d7da; border-color: #f5c6cb; }}
            .alert-info {{ color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb; }}
            .float-end {{ float: right; }}
            .small {{ font-size: 80%; font-weight: 400; }}
            .progress {{ display: flex; height: 1rem; overflow: hidden; font-size: 0.75rem; background-color: #e9ecef; border-radius: 0.25rem; }}
            .progress-bar {{ display: flex; flex-direction: column; justify-content: center; color: #fff; text-align: center; white-space: nowrap; background-color: #007bff; transition: width 0.6s ease; }}
            .d-flex {{ display: flex; }}
            .flex-grow-1 {{ flex-grow: 1; }}
            .align-items-center {{ align-items: center; }}
            .justify-content-between {{ justify-content: space-between; }}
            .health-indicator {{ padding: 5px 10px; border-radius: 20px; font-weight: bold; }}
            .health-indicator.healthy {{ background-color: #d4edda; color: #155724; }}
            .health-indicator.warning {{ background-color: #fff3cd; color: #856404; }}
            .health-indicator.critical {{ background-color: #f8d7da; color: #721c24; }}
            .action-item.high-severity, .action-item.critical-severity {{ border-left: 4px solid #dc3545; }}
            .action-item.medium-severity {{ border-left: 4px solid #ffc107; }}
            .action-item.low-severity {{ border-left: 4px solid #17a2b8; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="mb-4">Water Heater Component Failure Prediction</h1>
            <div class="row">
                <div class="col-md-4">
                    <div class="list-group">
                        <div class="list-group-item list-group-item-primary">Select a Water Heater</div>
    """

    # Add water heater list items
    for device in water_heaters:
        name = device.name or f"Water Heater {device.id}"
        html_content += f"""
        <a href="/?device_id={device.id}" class="list-group-item list-group-item-action">
            {name}
            <span class="badge bg-secondary float-end">{device.id}</span>
        </a>
        """

    html_content += """
                    </div>
                </div>
                <div class="col-md-8">
    """

    # If a device is selected, show its prediction
    selected_device_id = request.query_params.get("device_id")
    if selected_device_id:
        details = await get_device_details(selected_device_id)
        device = details.get("device")

        if device:
            name = device.name or f"Water Heater {device.id}"
            prediction = await generate_prediction_for_device(selected_device_id)

            html_content += f"""
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">{name}</h5>
                </div>
                <div class="card-body">
                    <p><strong>ID:</strong> {device.id}</p>
                    <p><strong>Type:</strong> {device.properties.get("model", "Unknown")}</p>
                    <p><strong>Location:</strong> {device.location or "Unknown"}</p>
                </div>
            </div>
            """

            if prediction:
                # Render the component failure prediction component
                component = ComponentFailurePredictionComponent(prediction)
                html_content += component.render()
            else:
                html_content += """
                <div class="alert alert-warning">
                    No prediction data available for this device.
                </div>
                """
        else:
            html_content += """
            <div class="alert alert-danger">
                Device not found.
            </div>
            """
    else:
        html_content += """
        <div class="alert alert-info">
            Select a water heater from the list to view its component failure prediction.
        </div>
        """

    html_content += """
                </div>
            </div>
        </div>
        <!-- No external scripts needed -->
    </body>
    </html>
    """

        return html_content
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        logger.error(traceback.format_exc())
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>An error occurred: {e}</p><pre>{traceback.format_exc()}</pre></body></html>",
            status_code=500
        )


async def main():
    """Main function to run the web server."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8006,  # Using port 8006 as requested
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
