"""
Simple web application for the Component Failure Prediction UI.
This module provides a simplified FastAPI app for testing and demonstration.
"""
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.predictions.interfaces import (
    ActionSeverity,
    PredictionResult,
    RecommendedAction,
)
from src.web.templates.component_failure_prediction import (
    ComponentFailurePredictionComponent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(testing: bool = False) -> FastAPI:
    """Create a FastAPI application."""
    app = FastAPI(debug=True)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    async def index(
        request: Request, has_predictions: bool = False, force_error: bool = False
    ):
        """Render the main page with component failure prediction UI."""
        try:
            if force_error:
                raise ValueError("Forced error for testing")

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
                    .card {{
                        position: relative;
                        display: flex;
                        flex-direction: column;
                        background-color: #fff;
                        border: 1px solid rgba(0,0,0,.125);
                        border-radius: 0.25rem;
                    }}
                    .card-header {{
                        padding: 0.75rem 1.25rem;
                        background-color: #f8f9fa;
                        border-bottom: 1px solid rgba(0,0,0,.125);
                    }}
                    .card-body {{
                        flex: 1 1 auto;
                        padding: 1.25rem;
                    }}
                    .health-indicator {{
                        padding: 5px 10px;
                        border-radius: 20px;
                        font-weight: bold;
                    }}
                    .health-indicator.healthy {{
                        background-color: #d4edda;
                        color: #155724;
                    }}
                    .health-indicator.warning {{
                        background-color: #fff3cd;
                        color: #856404;
                    }}
                    .health-indicator.critical {{
                        background-color: #f8d7da;
                        color: #721c24;
                    }}
                    .action-item {{
                        margin-bottom: 1rem;
                        padding: 0.5rem;
                        border: 1px solid #ddd;
                        border-radius: 0.25rem;
                    }}
                    .action-item.high-severity {{
                        border-left: 4px solid #dc3545;
                    }}
                    .action-item.medium-severity {{
                        border-left: 4px solid #ffc107;
                    }}
                    .action-item.low-severity {{
                        border-left: 4px solid #17a2b8;
                    }}
                    .component-item {{
                        margin-bottom: 1rem;
                    }}
                    .progress {{
                        height: 10px;
                        background-color: #e9ecef;
                        border-radius: 0.25rem;
                        margin-bottom: 0.5rem;
                    }}
                    .progress-bar {{
                        height: 100%;
                        border-radius: 0.25rem;
                    }}
                    .bg-success {{ background-color: #28a745; }}
                    .bg-warning {{ background-color: #ffc107; }}
                    .bg-danger {{ background-color: #dc3545; }}
                </style>
            </head>
            <body>
                <div class="container mt-5">
                    <h1 class="mb-4">Water Heater Component Failure Prediction</h1>
            """

            if has_predictions:
                # Create sample prediction for demonstration
                prediction = PredictionResult(
                    prediction_type="component_failure",
                    device_id="wh-sample-123",
                    predicted_value=0.65,  # 65% overall failure probability
                    confidence=0.85,
                    features_used=["temperature", "pressure", "energy_usage"],
                    timestamp=datetime.now(),
                    recommended_actions=[
                        RecommendedAction(
                            action_id="wh-sample-123-heating-element-80",
                            description="Inspect heating element for signs of failure",
                            severity=ActionSeverity.HIGH,
                            impact="Water heater may fail to heat water properly if not addressed",
                            expected_benefit="Prevent unexpected downtime and costly emergency repairs",
                            due_date=datetime.now() + timedelta(days=7),
                            estimated_cost=75.0,
                            estimated_duration="1-2 hours",
                        ),
                        RecommendedAction(
                            action_id="wh-sample-123-pressure-valve-60",
                            description="Test pressure relief valve operation",
                            severity=ActionSeverity.MEDIUM,
                            impact="Potential safety hazard from excessive pressure buildup",
                            expected_benefit="Prevent dangerous pressure conditions and ensure safety",
                            due_date=datetime.now() + timedelta(days=14),
                            estimated_cost=40.0,
                            estimated_duration="30 minutes",
                        ),
                    ],
                    raw_details={
                        "components": {
                            "heating_element": 0.8,
                            "thermostat": 0.4,
                            "pressure_valve": 0.6,
                            "anode_rod": 0.3,
                            "tank_integrity": 0.2,
                        },
                        "heater_type": "COMMERCIAL",
                    },
                )

                # Render component with prediction data
                component = ComponentFailurePredictionComponent(prediction)
                html_content += component.render()
            else:
                html_content += """
                <div class="card">
                    <div class="card-body">
                        <p>No prediction data available. Use ?has_predictions=true to view sample predictions.</p>
                    </div>
                </div>
                """

            html_content += """
                </div>
            </body>
            </html>
            """

            return html_content
        except Exception as e:
            logger.error(f"Error rendering index page: {e}")
            logger.error(traceback.format_exc())
            return HTMLResponse(
                content=f"""
                <html>
                <body>
                    <h1>Error</h1>
                    <p>An error occurred: {e}</p>
                    <pre>{traceback.format_exc()}</pre>
                </body>
                </html>
                """,
                status_code=500,
            )

    return app


async def start_server(port: int = 8006):
    """Start the web server."""
    import uvicorn

    config = uvicorn.Config(
        create_app(),
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_server())
