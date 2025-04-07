"""
End-to-End test for shadow document functionality
Following TDD principles - RED phase first
"""
import pytest
import requests
import websocket
import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Test constants
BASE_URL = "http://localhost:8006"
TEST_DEVICE_ID = "wh-test-001"
WS_URL = f"ws://localhost:8006/ws/devices/{TEST_DEVICE_ID}/state"

class TestShadowDocumentE2E:
    """End-to-end tests for shadow document functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        # Set up headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        cls.driver = webdriver.Chrome(options=chrome_options)
    
    @classmethod
    def teardown_class(cls):
        """Tear down test environment"""
        cls.driver.quit()
    
    def test_shadow_document_e2e(self):
        """Test end-to-end flow of shadow document updates"""
        # Step 1: Update shadow document via API
        shadow_data = {
            "state": {
                "reported": {
                    "temperature": 60.5,
                    "status": "online",
                    "mode": "heating"
                }
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/device/{TEST_DEVICE_ID}/shadow",
            json=shadow_data
        )
        assert response.status_code == 200, "Shadow update should succeed"
        
        # Step 2: Verify shadow document reflects updates via API
        get_response = requests.get(f"{BASE_URL}/api/device/{TEST_DEVICE_ID}/shadow")
        assert get_response.status_code == 200, "Shadow get should succeed"
        
        shadow = get_response.json()
        assert shadow["state"]["reported"]["temperature"] == 60.5, "Temperature should be updated"
        assert shadow["state"]["reported"]["status"] == "online", "Status should be updated"
        
        # Step 3: Open WebSocket connection and verify real-time updates
        # This is a simplified example, real implementation would handle the WebSocket more robustly
        ws = websocket.create_connection(WS_URL)
        
        # Step 4: Update shadow again
        new_shadow_data = {
            "state": {
                "reported": {
                    "temperature": 62.0
                }
            }
        }
        
        requests.put(
            f"{BASE_URL}/api/device/{TEST_DEVICE_ID}/shadow",
            json=new_shadow_data
        )
        
        # Step 5: Check WebSocket receives update
        result = ws.recv()
        ws.close()
        
        update = json.loads(result)
        assert update["type"] == "shadow_update", "Should receive shadow update"
        assert update["data"]["state"]["reported"]["temperature"] == 62.0, "WebSocket should receive temperature update"
        
        # Step 6: Verify UI updates (using Selenium)
        self.driver.get(f"{BASE_URL}/water-heaters/{TEST_DEVICE_ID}")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-header"))
        )
        
        # Check temperature display
        temp_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".temperature-value"))
        )
        
        # UI should show the updated temperature
        assert "62" in temp_element.text, "UI should display updated temperature"
