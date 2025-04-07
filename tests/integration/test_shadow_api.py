"""
Integration tests for Shadow Document API
Following TDD principles - RED phase first
"""
import pytest
import requests
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Test constants
BASE_URL = "http://localhost:8006"
TEST_DEVICE_ID = "wh-test-001"

def test_shadow_document_api():
    """Test that the shadow document API works correctly"""
    # Test GET endpoint for shadow document
    response = requests.get(f"{BASE_URL}/api/device/{TEST_DEVICE_ID}/shadow")
    
    # API should return successful response
    assert response.status_code == 200, "Shadow API should return 200 status"
    
    # Response should contain valid shadow data
    shadow = response.json()
    assert "state" in shadow, "Shadow response should have state field"
    assert "reported" in shadow["state"], "Shadow should have reported state"
    
def test_temperature_history_api():
    """Test that the temperature history API works correctly"""
    # Test GET endpoint for temperature history
    params = {"days": 7}
    response = requests.get(f"{BASE_URL}/api/device/{TEST_DEVICE_ID}/telemetry/temperature", params=params)
    
    # API should return successful response
    assert response.status_code == 200, "Temperature history API should return 200 status"
    
    # Response should contain history data
    history = response.json()
    assert isinstance(history, list), "Temperature history should be a list"
    assert len(history) > 0, "Temperature history should have data points"
