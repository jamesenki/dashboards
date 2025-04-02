#!/usr/bin/env python
"""
Selenium-based testing script to verify alerts display correctly in the frontend
"""
import json
import logging
import random
import sqlite3
import string
import time
import uuid
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Application settings
APP_URL = "http://localhost:8006"
DB_PATH = "/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/data/iotsphere.db"


def generate_test_id():
    """Generate unique test identifier with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"test-selenium-{timestamp}"


def create_test_alert(test_id):
    """Create a test alert in the database for verification"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # First create an alert rule
        rule_id = f"rule-{test_id}"
        cursor = conn.cursor()

        # Create alert rule
        cursor.execute(
            """
            INSERT INTO alert_rules
            (id, model_id, metric_name, threshold, condition, severity, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule_id,
                "water-heater-model-1",
                "energy_consumption",
                0.85,
                "ABOVE",
                "WARNING",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                1,
            ),
        )

        # Create alert event
        alert_id = f"alert-{test_id}"
        cursor.execute(
            """
            INSERT INTO alert_events
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                rule_id,
                "water-heater-model-1",
                "energy_consumption",
                0.95,
                "WARNING",
                datetime.now().isoformat(),
                0,
                None,
            ),
        )

        conn.commit()
        logger.info(f"Created test alert: {alert_id}")
        return alert_id

    except Exception as e:
        logger.error(f"Error creating test alert: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()


def test_frontend_alerts_display():
    """
    Test that alerts are properly displayed in the frontend
    """
    logger.info("=== Starting Frontend Alerts Display Test ===")

    # Create a test alert in the database
    test_id = generate_test_id()
    alert_id = create_test_alert(test_id)

    if not alert_id:
        logger.error("Failed to create test alert. Aborting test.")
        return False

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        # Initialize the WebDriver
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

        # Navigate to the alerts page
        alerts_url = f"{APP_URL}/monitoring/alerts"
        logger.info(f"Navigating to alerts page: {alerts_url}")
        driver.get(alerts_url)

        # Wait for the page to load and JavaScript to execute
        logger.info("Waiting for alerts to load via JavaScript...")
        time.sleep(3)  # Initial wait for page load

        # Wait for alerts table to be populated
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "alerts-tbody"))
            )
            logger.info("Alerts table found in the page")

            # Wait a bit more for fetch to complete and DOM to update
            time.sleep(2)

            # Get page source and check for our test alert ID
            page_source = driver.page_source
            if alert_id in page_source:
                logger.info(f"✅ SUCCESS: Test alert {alert_id} found in the frontend!")

                # Save successful page source for reference
                with open("successful_frontend_test.html", "w") as f:
                    f.write(page_source)

                return True
            else:
                logger.warning(
                    f"❌ FAIL: Test alert {alert_id} not found in the frontend."
                )

                # Let's check if any alerts are displayed
                alert_elements = driver.find_elements(
                    By.CSS_SELECTOR, "#alerts-tbody tr"
                )

                if alert_elements:
                    logger.info(f"Found {len(alert_elements)} alert rows in the table:")
                    for i, elem in enumerate(
                        alert_elements[:5]
                    ):  # Show just the first 5 to avoid spam
                        logger.info(f"Alert {i+1}: {elem.text[:100]}...")
                else:
                    logger.warning(
                        "No alert rows found in the table. Check JavaScript console for errors."
                    )

                # Check JavaScript console for errors
                console_logs = driver.get_log("browser")
                if console_logs:
                    logger.warning("JavaScript console errors:")
                    for log in console_logs:
                        logger.warning(f"Console: {log}")

                # Save the page source for debugging
                with open("failed_frontend_test.html", "w") as f:
                    f.write(page_source)

                return False
        except Exception as e:
            logger.error(f"Error waiting for alerts table: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Error during Selenium test: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            driver.quit()
        except:
            pass
        logger.info("WebDriver closed")


if __name__ == "__main__":
    # Run the test
    success = test_frontend_alerts_display()

    if success:
        logger.info("✅ TEST PASSED: Frontend properly displays alerts!")
        exit(0)
    else:
        logger.error("❌ TEST FAILED: Frontend does not properly display alerts.")
        exit(1)
