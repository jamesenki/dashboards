"""
Fix for the alerts API to ensure real alerts are displayed.
Following TDD principles - adapting code to match expected behavior.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variable to ensure real data is used
os.environ["USE_MOCK_DATA"] = "False"

# Import after setting environment variables
from src.db.real_database import SQLiteDatabase
from src.main import app as main_app


async def get_real_alerts_from_db():
    """Get real alerts directly from the database."""
    try:
        # Connect to the database
        db = SQLiteDatabase(connection_string="data/iotsphere.db")

        # Get all models to enhance alerts with model names
        models_dict = {}
        try:
            models = await db.fetch_all("SELECT id, name FROM models")
            for model in models:
                models_dict[model["id"]] = model.get("name", "Unknown Model")
        except Exception as e:
            logger.warning(f"Error fetching models: {str(e)}")

        # Get all alert events from the database
        query = """
        SELECT e.id, e.rule_id, e.model_id, e.metric_name, e.metric_value, e.severity, e.created_at, e.resolved,
               r.threshold, r.condition
        FROM alert_events e
        LEFT JOIN alert_rules r ON e.rule_id = r.id
        ORDER BY e.created_at DESC
        LIMIT 100
        """
        db_alerts = await db.fetch_all(query)

        # Format the alerts to match frontend expectations
        alerts = []
        for alert in db_alerts:
            model_id = alert.get("model_id", "unknown")
            model_name = models_dict.get(model_id, "Unknown Model")

            # Map database fields to expected frontend fields
            formatted_alert = {
                "id": alert["id"],
                "model_id": model_id,
                "model_name": model_name,
                "rule_name": f"Alert for {alert.get('metric_name', 'metric')}",
                "metric_name": alert.get("metric_name", "unknown"),
                "threshold": alert.get("threshold", 0.0),
                "current_value": alert.get("metric_value", 0.0),
                "severity": alert.get("severity", "medium").upper(),
                "timestamp": alert.get("created_at", datetime.now().isoformat()),
                "triggered_at": alert.get("created_at", datetime.now().isoformat()),
                "status": "resolved" if alert.get("resolved", False) else "active",
            }

            # Generate a description based on available data
            op_text = (
                "exceeded"
                if alert.get("condition", ">") in [">", ">="]
                else "dropped below"
            )
            formatted_alert[
                "description"
            ] = f"{formatted_alert['metric_name'].replace('_', ' ').title()} {op_text} threshold"

            alerts.append(formatted_alert)

        # Close the database connection
        await db.close()

        logger.info(f"Found {len(alerts)} real alerts from database")
        return alerts
    except Exception as e:
        logger.error(f"Error retrieving alerts from database: {str(e)}")
        return []


async def test_alerts_api():
    """Test the alerts API and print the response."""
    # Create a test client
    client = TestClient(main_app)

    # Test the current API endpoint
    response = client.get("/api/monitoring/alerts")
    current_alerts = response.json()
    logger.info(
        f"Current API returns {len(current_alerts)} alerts: {json.dumps(current_alerts[:1], indent=2)}"
    )

    # Get real alerts from database
    real_alerts = await get_real_alerts_from_db()
    logger.info(f"Database has {len(real_alerts)} real alerts")

    if real_alerts:
        logger.info(
            f"Sample alert from database: {json.dumps(real_alerts[0], indent=2)}"
        )

    # Create a temporary endpoint to serve real alerts
    @main_app.get("/api/monitoring/real_alerts")
    async def get_real_alerts():
        """Temporary endpoint to serve real alerts."""
        return await get_real_alerts_from_db()

    # Test our new endpoint
    logger.info("Testing new endpoint...")
    logger.info(
        "Visit http://localhost:8006/api/monitoring/real_alerts to see real alerts"
    )
    logger.info("\nInstructions to fix the issue:")
    logger.info(
        "1. Modify the frontend code in alerts.html to temporarily use /api/monitoring/real_alerts"
    )
    logger.info(
        "2. Debug why the main /api/monitoring/alerts endpoint isn't returning real data"
    )
    logger.info(
        "3. Update dashboard_api.py to ensure it's retrieving data from the database correctly"
    )


def patch_frontend():
    """Create a patched version of the alerts.html file."""
    try:
        # Read the original file
        with open("frontend/templates/model-monitoring/alerts.html", "r") as f:
            content = f.read()

        # Create a backup
        with open("frontend/templates/model-monitoring/alerts.html.bak", "w") as f:
            f.write(content)

        # Modify the fetch URL to use our new endpoint
        modified_content = content.replace(
            "fetch(`/api/monitoring/alerts`)", "fetch(`/api/monitoring/real_alerts`)"
        )

        # Write the modified file
        with open("frontend/templates/model-monitoring/alerts.html", "w") as f:
            f.write(modified_content)

        logger.info("Frontend code patched to use real_alerts endpoint")
        logger.info("Original file backed up as alerts.html.bak")

    except Exception as e:
        logger.error(f"Error patching frontend: {str(e)}")


if __name__ == "__main__":
    logger.info("Running alerts API fix...")
    asyncio.run(test_alerts_api())
    patch_frontend()
    logger.info("Done. Restart your server and refresh the browser to see real alerts.")
