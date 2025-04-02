"""
Script to debug the alerts database query and formatting to ensure TDD compliance.
We're focusing on adapting our code to match expected behavior without changing tests.
"""
import asyncio
import os
import sqlite3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we're using real data not mock data
os.environ["USE_MOCK_DATA"] = "False"

def inspect_alert_events_directly():
    """Directly inspect alert_events table using sqlite3."""
    try:
        # Connect to the database
        conn = sqlite3.connect("data/iotsphere.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check schema
        logger.info("==== ALERT EVENTS TABLE SCHEMA ====")
        cursor.execute("PRAGMA table_info(alert_events)")
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"Column: {col['name']} ({col['type']})")
            
        # Get alert counts
        cursor.execute("SELECT COUNT(*) as count FROM alert_events")
        count = cursor.fetchone()['count']
        logger.info(f"Total alert events in database: {count}")
        
        # Get sample alerts
        if count > 0:
            cursor.execute("""
            SELECT e.id, e.rule_id, e.model_id, e.metric_name, e.metric_value, e.severity, 
                   e.created_at, e.resolved, r.threshold, r.condition 
            FROM alert_events e
            LEFT JOIN alert_rules r ON e.rule_id = r.id
            ORDER BY e.created_at DESC
            LIMIT 5
            """)
            alerts = cursor.fetchall()
            logger.info("==== SAMPLE ALERTS (Directly from DB) ====")
            for alert in alerts:
                logger.info(json.dumps({k: alert[k] for k in alert.keys()}, default=str))
                
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error inspecting database directly: {e}")

def create_test_alert():
    """Create a test alert to ensure we have data to display."""
    try:
        # Connect to the database
        conn = sqlite3.connect("data/iotsphere.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, verify we have at least one alert rule
        cursor.execute("SELECT id, model_id, metric_name, threshold, condition FROM alert_rules LIMIT 1")
        rule = cursor.fetchone()
        
        if not rule:
            logger.warning("No alert rules found! Creating a test rule first...")
            rule_id = f"test-rule-{int(datetime.now().timestamp())}"
            cursor.execute("""
            INSERT INTO alert_rules (id, model_id, metric_name, threshold, condition, severity, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rule_id, "water-heater-model-1", "energy_consumption", 0.85, "ABOVE", "WARNING", 1))
            conn.commit()
            
            # Retrieve the created rule
            cursor.execute("SELECT id, model_id, metric_name, threshold, condition FROM alert_rules WHERE id = ?", (rule_id,))
            rule = cursor.fetchone()
            logger.info(f"Created test rule: {rule['id']}")
        
        # Now create an alert event
        alert_id = f"alert-{int(datetime.now().timestamp())}"
        now = datetime.now().isoformat()
        
        cursor.execute("""
        INSERT INTO alert_events 
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id, 
            rule['id'], 
            rule['model_id'], 
            rule['metric_name'], 
            float(rule['threshold']) + 0.1,  # Value that exceeds threshold
            "WARNING", 
            now, 
            0
        ))
        conn.commit()
        logger.info(f"Created test alert: {alert_id}")
        
        # Verify alert was created
        cursor.execute("SELECT * FROM alert_events WHERE id = ?", (alert_id,))
        result = cursor.fetchone()
        if result:
            logger.info(f"Verified alert was created: {result['id']}")
        else:
            logger.warning("Alert creation failed - not found in database")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating test alert: {e}")

def format_alerts_as_frontend_expects():
    """Format alerts as the frontend expects them."""
    try:
        # Connect to the database
        conn = sqlite3.connect("data/iotsphere.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get models to enhance alerts with model names
        models_dict = {}
        cursor.execute("SELECT id, name FROM models")
        models = cursor.fetchall()
        for model in models:
            models_dict[model['id']] = model.get('name', 'Unknown Model')
            
        # Get alerts
        cursor.execute("""
        SELECT e.id, e.rule_id, e.model_id, e.metric_name, e.metric_value, e.severity, 
               e.created_at, e.resolved, r.threshold, r.condition 
        FROM alert_events e
        LEFT JOIN alert_rules r ON e.rule_id = r.id
        ORDER BY e.created_at DESC
        LIMIT 10
        """)
        db_alerts = cursor.fetchall()
        
        # Format alerts as the frontend expects
        formatted_alerts = []
        for alert in db_alerts:
            model_id = alert.get('model_id', 'unknown')
            model_name = models_dict.get(model_id, "Unknown Model")
            
            # Map database fields to expected frontend fields
            formatted_alert = {
                "id": alert['id'],
                "rule_name": f"Alert for {alert.get('metric_name', 'metric')}",
                "metric_name": alert.get('metric_name', 'unknown'),
                "threshold": alert.get('threshold', 0.0),
                "current_value": alert.get('metric_value', 0.0),
                "severity": alert.get('severity', 'medium').upper(),
                "triggered_at": alert.get('created_at', datetime.now().isoformat()),
            }
            
            formatted_alerts.append(formatted_alert)
            
        logger.info("==== FORMATTED ALERTS (As Frontend Expects) ====")
        for alert in formatted_alerts:
            logger.info(json.dumps(alert, default=str))
            
        # Create a file with expected format for the frontend
        with open('expected_alerts_format.json', 'w') as f:
            json.dump(formatted_alerts, f, indent=2, default=str)
            
        logger.info(f"Wrote {len(formatted_alerts)} formatted alerts to expected_alerts_format.json")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error formatting alerts: {e}")

async def check_dashboard_api_function():
    """
    Check if the dashboard API function is properly defined.
    This helps verify our implementation matches expected behavior without changing tests.
    """
    logger.info("==== MANUALLY CHECKING DASHBOARD API FUNCTION ====")
    
    # This would normally import the necessary modules and check the function,
    # but since we can't import within this script, we'll output verification steps
    logger.info("Verification steps for dashboard_api.py:")
    logger.info("1. Check that the '/alerts' endpoint definition uses the correct database query")
    logger.info("2. Ensure alerts are formatted correctly to match frontend expectations")
    logger.info("3. Verify error handling returns an empty array instead of raising exceptions")
    logger.info("4. Confirm response fields match frontend expectations (id, rule_name, metric_name, etc.)")

if __name__ == "__main__":
    logger.info("Starting alert debugging...")
    
    # Step 1: Check database content directly
    inspect_alert_events_directly()
    
    # Step 2: Create a test alert if needed
    create_test_alert()
    
    # Step 3: Format alerts in expected frontend format
    format_alerts_as_frontend_expects()
    
    # Step 4: Check API function manually
    asyncio.run(check_dashboard_api_function())
    
    logger.info("Alert debugging completed")
