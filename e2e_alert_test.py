"""
End-to-end test for the alerts workflow.
Following TDD principles, we will verify:
1. Alert rule creation and storage in the database
2. Alert event generation and storage
3. API retrieval of alerts
4. Frontend display of alerts

This test verifies the entire flow without changing test expectations.
"""
import os
import json
import logging
import sqlite3
import requests
import time
import uuid
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "data/iotsphere.db"
SERVER_URL = "http://localhost:8006"
TEST_MODEL_ID = "water-heater-model-1"  # Use an existing model ID
API_BASE_URL = f"{SERVER_URL}/api/monitoring"
TEST_TIME = datetime.now().strftime("%Y%m%d%H%M%S")

class AlertWorkflowTest:
    """Test the entire alert workflow end-to-end."""
    
    def __init__(self):
        """Initialize the test."""
        self.rule_id = f"test-rule-{TEST_TIME}"
        self.alert_id = f"test-alert-{TEST_TIME}"
        self.conn = None
        
        # Configure environment
        os.environ["USE_MOCK_DATA"] = "False"
    
    def db_connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row
            logger.info("Connected to database")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def db_close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def test_step1_verify_database(self):
        """Step 1: Verify database structure and existing data."""
        logger.info("=== STEP 1: Verify Database Structure ===")
        try:
            cursor = self.conn.cursor()
            
            # Check alert_rules table
            cursor.execute("PRAGMA table_info(alert_rules)")
            columns = cursor.fetchall()
            logger.info("alert_rules table columns:")
            for col in columns:
                logger.info(f"  - {col['name']} ({col['type']})")
            
            # Count existing rules
            cursor.execute("SELECT COUNT(*) as count FROM alert_rules")
            rule_count = cursor.fetchone()['count']
            logger.info(f"Existing alert rules: {rule_count}")
            
            # Count existing alerts
            cursor.execute("SELECT COUNT(*) as count FROM alert_events")
            alert_count = cursor.fetchone()['count']
            logger.info(f"Existing alert events: {alert_count}")
            
            # Verify model exists
            cursor.execute("SELECT * FROM models WHERE id = ?", (TEST_MODEL_ID,))
            model = cursor.fetchone()
            if model:
                logger.info(f"Test model exists: {TEST_MODEL_ID} ({model['name']})")
            else:
                logger.warning(f"Test model not found: {TEST_MODEL_ID}")
                # Create a test model if needed
                cursor.execute(
                    "INSERT INTO models (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                    (TEST_MODEL_ID, "Water Heater Test Model", "Test model for alerts", datetime.now().isoformat())
                )
                self.conn.commit()
                logger.info(f"Created test model: {TEST_MODEL_ID}")
            
            return True
        except Exception as e:
            logger.error(f"Error verifying database: {e}")
            return False
    
    def test_step2_create_alert_rule(self):
        """Step 2: Create an alert rule in the database."""
        logger.info("=== STEP 2: Create Alert Rule ===")
        try:
            cursor = self.conn.cursor()
            
            # First check if rule already exists
            cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (self.rule_id,))
            existing_rule = cursor.fetchone()
            
            if existing_rule:
                logger.info(f"Rule already exists: {self.rule_id}")
                return True
            
            # Create new rule
            metric_name = "energy_consumption"
            threshold = 0.85
            condition = "ABOVE"
            severity = "WARNING"
            
            cursor.execute("""
            INSERT INTO alert_rules (id, model_id, metric_name, threshold, condition, severity, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.rule_id, TEST_MODEL_ID, metric_name, threshold, condition, severity, 1))
            self.conn.commit()
            
            # Verify rule was created
            cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (self.rule_id,))
            rule = cursor.fetchone()
            if rule:
                logger.info(f"Successfully created rule: {self.rule_id}")
                logger.info(f"Rule details: {json.dumps({k: rule[k] for k in rule.keys()}, default=str)}")
                return True
            else:
                logger.error(f"Failed to create rule: {self.rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return False
    
    def test_step3_create_alert_event(self):
        """Step 3: Create an alert event in the database."""
        logger.info("=== STEP 3: Create Alert Event ===")
        try:
            cursor = self.conn.cursor()
            
            # First check if alert already exists
            cursor.execute("SELECT * FROM alert_events WHERE id = ?", (self.alert_id,))
            existing_alert = cursor.fetchone()
            
            if existing_alert:
                logger.info(f"Alert already exists: {self.alert_id}")
                return True
            
            # Get rule details
            cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (self.rule_id,))
            rule = cursor.fetchone()
            
            if not rule:
                logger.error(f"Rule not found: {self.rule_id}")
                return False
            
            # Create alert event
            now = datetime.now().isoformat()
            metric_value = rule['threshold'] + 0.1  # Value that triggers the alert
            
            cursor.execute("""
            INSERT INTO alert_events 
                (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.alert_id, 
                self.rule_id, 
                rule['model_id'], 
                rule['metric_name'], 
                metric_value, 
                rule['severity'], 
                now, 
                0
            ))
            self.conn.commit()
            
            # Verify alert was created
            cursor.execute("SELECT * FROM alert_events WHERE id = ?", (self.alert_id,))
            alert = cursor.fetchone()
            if alert:
                logger.info(f"Successfully created alert: {self.alert_id}")
                logger.info(f"Alert details: {json.dumps({k: alert[k] for k in alert.keys()}, default=str)}")
                return True
            else:
                logger.error(f"Failed to create alert: {self.alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating alert event: {e}")
            return False
    
    def test_step4_verify_api_alerts(self):
        """Step 4: Verify the alerts API returns our test alert."""
        logger.info("=== STEP 4: Verify API Alerts ===")
        try:
            alerts_url = f"{API_BASE_URL}/alerts"
            logger.info(f"Testing API endpoint: {alerts_url}")
            
            response = requests.get(alerts_url)
            if response.status_code != 200:
                logger.error(f"API request failed with status code: {response.status_code}")
                return False
            
            alerts = response.json()
            logger.info(f"API returned {len(alerts)} alerts")
            
            # Check if our test alert is in the response
            test_alert_found = False
            for alert in alerts:
                alert_id = alert.get('id')
                logger.info(f"API alert: {alert_id}")
                if alert_id == self.alert_id:
                    test_alert_found = True
                    logger.info(f"Found our test alert in API response: {json.dumps(alert)}")
                    break
            
            if not test_alert_found:
                logger.warning("Our test alert was not found in the API response")
                # Dump the first few alerts for debugging
                for i, alert in enumerate(alerts[:5]):
                    logger.info(f"Sample alert {i+1}: {json.dumps(alert)}")
                    
                # Also check model-specific alerts API
                model_alerts_url = f"{API_BASE_URL}/models/{TEST_MODEL_ID}/versions/1.0/alerts"
                logger.info(f"Testing model-specific API endpoint: {model_alerts_url}")
                
                model_response = requests.get(model_alerts_url)
                if model_response.status_code != 200:
                    logger.error(f"Model API request failed with status code: {model_response.status_code}")
                else:
                    model_alerts = model_response.json()
                    logger.info(f"Model API returned {len(model_alerts)} alerts")
                    for alert in model_alerts:
                        logger.info(f"Model API alert: {json.dumps(alert)}")
                
                return False
            
            return True
                
        except Exception as e:
            logger.error(f"Error verifying API alerts: {e}")
            return False
    
    def test_step5_check_frontend_alerts(self):
        """Step 5: Check if the frontend can display our test alert."""
        logger.info("=== STEP 5: Check Frontend Alerts ===")
        try:
            # Get the frontend HTML
            alerts_url = f"{SERVER_URL}/monitoring/alerts"
            logger.info(f"Checking frontend URL: {alerts_url}")
            
            response = requests.get(alerts_url)
            if response.status_code != 200:
                logger.error(f"Frontend request failed with status code: {response.status_code}")
                return False
            
            # Save response to a file for inspection
            frontend_html = response.text
            with open("frontend_alerts_response.html", "w") as f:
                f.write(frontend_html)
            
            logger.info("Saved frontend HTML response to frontend_alerts_response.html")
            
            # Check if our alert ID appears in the HTML
            if self.alert_id in frontend_html:
                logger.info(f"Found our test alert ID in the frontend HTML: {self.alert_id}")
                return True
            else:
                logger.warning(f"Our test alert ID was not found in the frontend HTML: {self.alert_id}")
                logger.info("This doesn't necessarily mean it won't appear - the frontend loads alerts via JavaScript")
                
                # Provide instructions for manual verification
                logger.info("\nTo manually verify the frontend display:")
                logger.info(f"1. Open {alerts_url} in your browser")
                logger.info("2. Check if the Recent Alerts section contains your test alert")
                logger.info("3. Look for the alert with ID: " + self.alert_id)
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking frontend alerts: {e}")
            return False
    
    def test_step6_debug_missing_alerts(self):
        """Step 6: Debug why alerts might not be appearing."""
        logger.info("=== STEP 6: Debug Missing Alerts ===")
        try:
            # Verify frontend code loads alerts properly
            frontend_dir = Path("frontend/templates/model-monitoring")
            alerts_html_path = frontend_dir / "alerts.html"
            
            if not alerts_html_path.exists():
                logger.error(f"Frontend file not found: {alerts_html_path}")
                return False
            
            with open(alerts_html_path, "r") as f:
                alerts_html = f.read()
            
            # Check the fetch URL
            fetch_url_line = None
            for line in alerts_html.split("\n"):
                if "fetch(" in line and "alerts" in line:
                    fetch_url_line = line.strip()
                    break
            
            if fetch_url_line:
                logger.info(f"Frontend fetch URL: {fetch_url_line}")
                
                # Make sure it matches our API endpoint
                if "/api/monitoring/alerts" not in fetch_url_line:
                    logger.warning(f"Frontend is not fetching from /api/monitoring/alerts")
                    logger.info("This could be why alerts are not showing up")
                    
                    # Fix fetch URL?
                    should_fix = input("Fix frontend fetch URL? (y/n): ")
                    if should_fix.lower() == 'y':
                        fixed_html = alerts_html.replace(
                            fetch_url_line,
                            "            fetch(`/api/monitoring/alerts`)"
                        )
                        with open(alerts_html_path, "w") as f:
                            f.write(fixed_html)
                        logger.info("Fixed frontend fetch URL")
            else:
                logger.warning("Could not find fetch URL in frontend code")
            
            # Check if the API endpoint is defined correctly
            dashboard_api_path = Path("src/monitoring/dashboard_api.py")
            if not dashboard_api_path.exists():
                logger.error(f"API file not found: {dashboard_api_path}")
                return False
                
            with open(dashboard_api_path, "r") as f:
                dashboard_api = f.read()
            
            # Check for alerts endpoint definition
            if "@app.get(\"/alerts\")" in dashboard_api:
                logger.info("Found /alerts endpoint definition in dashboard_api.py")
            else:
                logger.warning("Could not find /alerts endpoint definition in dashboard_api.py")
                
            # Check SQL query used for alerts
            if "FROM alert_events e" in dashboard_api:
                logger.info("Found alert_events query in dashboard_api.py")
            else:
                logger.warning("Could not find alert_events query in dashboard_api.py")
            
            return True
                
        except Exception as e:
            logger.error(f"Error debugging missing alerts: {e}")
            return False
    
    def run_test(self):
        """Run the full end-to-end test."""
        logger.info("=== Starting End-to-End Alert Workflow Test ===")
        
        # Connect to database
        if not self.db_connect():
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Run test steps
            steps = [
                self.test_step1_verify_database,
                self.test_step2_create_alert_rule,
                self.test_step3_create_alert_event,
                self.test_step4_verify_api_alerts,
                self.test_step5_check_frontend_alerts,
                self.test_step6_debug_missing_alerts
            ]
            
            results = []
            for i, step in enumerate(steps):
                logger.info(f"Running step {i+1}/{len(steps)}: {step.__name__}")
                result = step()
                results.append(result)
                
                if not result:
                    logger.warning(f"Step {i+1} failed: {step.__name__}")
                
                # Small delay between steps
                time.sleep(1)
            
            # Summarize results
            logger.info("\n=== Test Results Summary ===")
            for i, (step, result) in enumerate(zip(steps, results)):
                status = "PASSED" if result else "FAILED"
                logger.info(f"Step {i+1}: {step.__name__} - {status}")
            
            all_passed = all(results)
            if all_passed:
                logger.info("\n✅ All tests PASSED")
            else:
                logger.warning("\n❌ Some tests FAILED")
                
            return all_passed
            
        finally:
            # Close database connection
            self.db_close()

if __name__ == "__main__":
    test = AlertWorkflowTest()
    test.run_test()
