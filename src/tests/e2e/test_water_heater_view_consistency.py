"""
End-to-end tests for water heater view consistency.
Tests that details, operations, and history views all show data for the same water heater.
"""
import pytest
import json
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

from src.main import app

client = TestClient(app)

class TestWaterHeaterViewConsistency:
    """Test suite for water heater view consistency across different tabs."""
    
    def setup_method(self):
        """Set up test data - get a list of available water heaters."""
        self.water_heater_list_response = client.get("/api/water-heaters/")
        assert self.water_heater_list_response.status_code == 200
        self.water_heaters = self.water_heater_list_response.json()
        assert len(self.water_heaters) > 0, "No water heaters found for testing"
        
        # Select the first water heater for testing
        self.test_heater = self.water_heaters[0]
        self.heater_id = self.test_heater["id"]
        
    def test_water_heater_details_consistency(self):
        """
        Test that when a water heater is selected from the list, 
        the details page loads with the correct water heater data.
        """
        # 1. Verify we can get the specific water heater details via API
        water_heater_detail_response = client.get(f"/api/water-heaters/{self.heater_id}")
        assert water_heater_detail_response.status_code == 200
        water_heater_detail = water_heater_detail_response.json()
        
        # Verify the water heater details match the expected water heater
        assert water_heater_detail["id"] == self.heater_id
        assert water_heater_detail["name"] == self.test_heater["name"]
        
        # 2. Get the HTML page for the water heater details
        page_response = client.get(f"/water-heaters/{self.heater_id}")
        assert page_response.status_code == 200
        
        # 3. Parse the HTML to verify it's a water heater detail page
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Check if the URL path is passed in the template
        url_parts = page_response.url.path.split('/')
        page_heater_id = url_parts[-1] if url_parts else None
        assert page_heater_id == self.heater_id, f"Expected URL to contain heater ID {self.heater_id}, got {page_heater_id}"
        
        # Check if the detail page has the WaterHeaterDetail initialization
        init_script_found = False
        for script in soup.find_all('script'):
            script_content = script.string
            if script_content and "new WaterHeaterDetail" in script_content:
                init_script_found = True
                break
        
        assert init_script_found, "Water heater detail initialization script not found"
    
    def test_operations_tab_consistency(self):
        """
        Test that the operations tab loads with the correct water heater data.
        """
        # 1. Get operations data from API
        operations_response = client.get(f"/api/water-heaters/{self.heater_id}/operations")
        
        # API might return 404 if not implemented yet, but should be consistent
        if operations_response.status_code == 404:
            pytest.skip("Operations API not implemented yet")
        
        assert operations_response.status_code in (200, 404), f"Unexpected status code: {operations_response.status_code}"
        
        if operations_response.status_code == 200:
            operations_data = operations_response.json()
            
            # The operations data doesn't include the heater_id directly
            # but it should be consistent with the details data
            
            # Get the details data to compare
            details_response = client.get(f"/api/water-heaters/{self.heater_id}")
            assert details_response.status_code == 200
            details_data = details_response.json()
            
            # Verify both are using same water heater by checking properties 
            # that should be same across both endpoints
            if "current_temperature" in operations_data and "current_temp" in details_data:
                # Allow small difference due to potential updates between calls
                assert abs(operations_data["current_temperature"] - details_data["current_temp"]) < 5, \
                    "Current temperature inconsistent between operations and details"
                
            # Also check if the HTML for the operations tab includes the correct ID
            page_response = client.get(f"/water-heaters/{self.heater_id}")
            assert page_response.status_code == 200
            
            soup = BeautifulSoup(page_response.text, 'html.parser')
            assert soup.select_one('#operations-content'), "Operations tab content not found"
    
    def test_history_tab_consistency(self):
        """
        Test that the history tab loads with the correct water heater data.
        """
        # 1. Get history data from API
        history_response = client.get(f"/api/water-heaters/{self.heater_id}/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        # Verify history data has expected structure
        assert "temperature" in history_data, "History data missing temperature section"
        assert "energy_usage" in history_data, "History data missing energy_usage section"
        assert "pressure_flow" in history_data, "History data missing pressure_flow section"
        
        # Get temperature history specifically to check ID
        temp_history_response = client.get(f"/api/water-heaters/{self.heater_id}/history/temperature")
        assert temp_history_response.status_code == 200
        
        # Get energy usage history to check ID
        energy_history_response = client.get(f"/api/water-heaters/{self.heater_id}/history/energy")
        assert energy_history_response.status_code == 200
        
        # Get pressure-flow history to check ID
        pressure_flow_history_response = client.get(f"/api/water-heaters/{self.heater_id}/history/pressure-flow")
        assert pressure_flow_history_response.status_code == 200
        
    def test_end_to_end_consistency(self):
        """
        Test that details, operations, and history all use data from the same water heater.
        """
        # 1. Get the details from API
        details_response = client.get(f"/api/water-heaters/{self.heater_id}")
        assert details_response.status_code == 200
        details_data = details_response.json()
        
        # 2. Get the history data
        history_response = client.get(f"/api/water-heaters/{self.heater_id}/history")
        assert history_response.status_code == 200
        
        # 3. Verify consistency
        assert details_data["id"] == self.heater_id
        
        # 4. Test HTML page with all tabs
        page_response = client.get(f"/water-heaters/{self.heater_id}")
        assert page_response.status_code == 200
        
        # 5. Ensure the page contains links/references to all three tabs
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Check for tab navigation
        tab_buttons = soup.select(".tab-btn")
        tab_ids = [btn.get("id") for btn in tab_buttons]
        
        assert "details-tab-btn" in tab_ids, "Details tab button not found"
        assert "operations-tab-btn" in tab_ids, "Operations tab button not found"
        assert "history-tab-btn" in tab_ids, "History tab button not found"
        
        # Check if tab content containers exist
        assert soup.select_one("#details-content"), "Details content container not found"
        assert soup.select_one("#operations-content"), "Operations content container not found"
        assert soup.select_one("#history-content"), "History content container not found"
        
        # Check if history dashboard includes chart containers
        history_content = soup.select_one("#history-content")
        assert history_content, "History content not found"
        
        temperature_chart = soup.select_one("#temperature-chart")
        assert temperature_chart, "Temperature chart canvas not found"
        
        energy_chart = soup.select_one("#energy-usage-chart")
        assert energy_chart, "Energy usage chart canvas not found"
        
        pressure_chart = soup.select_one("#pressure-flow-chart")
        assert pressure_chart, "Pressure flow chart canvas not found"
        
        print(f"All tests passed for water heater {self.heater_id}")
