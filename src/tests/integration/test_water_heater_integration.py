import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.main import app
from src.models.device import DeviceType, DeviceStatus
from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.utils.dummy_data import generate_water_heaters

# Integration tests will use the actual FastAPI app with a real database
# But we'll use a test database to avoid affecting production data
client = TestClient(app)


class TestWaterHeaterIntegration:
    """Integration tests for water heater functionality.
    
    These tests check the full flow from API to database and back.
    """
    
    @pytest.fixture(autouse=True)
    def setup_dummy_data(self):
        """Set up dummy data for testing."""
        # This will be executed before each test
        # Ideally, we would use a test database here
        pass
    
    def test_get_water_heaters_full_flow(self):
        """Test getting all water heaters through the API."""
        # Make a request to the API
        response = client.get("/api/water-heaters")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # Verify the structure of the first heater
            heater = data[0]
            assert "id" in heater
            assert "name" in heater
            assert "current_temperature" in heater
            assert "target_temperature" in heater
            assert "mode" in heater
            assert "heater_status" in heater
    
    def test_water_heater_creation_and_retrieval(self):
        """Test creating a water heater and then retrieving it."""
        # Create a new water heater through the API
        new_heater = {
            "name": "Integration Test Heater",
            "type": DeviceType.WATER_HEATER,
            "status": DeviceStatus.ONLINE,
            "target_temperature": 50.0,
            "current_temperature": 45.5,
            "mode": WaterHeaterMode.ECO,
            "heater_status": WaterHeaterStatus.HEATING,
            "capacity": 120.0,
            "efficiency_rating": 0.9
        }
        
        # POST the new heater
        create_response = client.post("/api/water-heaters", json=new_heater)
        assert create_response.status_code == 201
        
        created_heater = create_response.json()
        heater_id = created_heater["id"]
        
        # Retrieve the heater to verify it was saved
        get_response = client.get(f"/api/water-heaters/{heater_id}")
        assert get_response.status_code == 200
        
        retrieved_heater = get_response.json()
        assert retrieved_heater["name"] == "Integration Test Heater"
        assert retrieved_heater["target_temperature"] == 50.0
    
    def test_update_temperature_and_verify_status_change(self):
        """Test updating temperature and verifying automatic status changes."""
        # First get an existing water heater
        response = client.get("/api/water-heaters")
        assert response.status_code == 200
        
        heaters = response.json()
        if not heaters:
            pytest.skip("No water heaters available for testing")
        
        # Select a heater that's in HEATING status
        heater = None
        for h in heaters:
            if h["heater_status"] == WaterHeaterStatus.HEATING:
                heater = h
                break
        
        if not heater:
            pytest.skip("No water heaters in HEATING status available")
        
        # Update to a temperature above target to trigger status change
        new_temp = heater["target_temperature"] + 2.0
        update_response = client.post(
            f"/api/water-heaters/{heater['id']}/readings",
            json={"temperature": new_temp}
        )
        
        assert update_response.status_code == 200
        updated_heater = update_response.json()
        
        # Verify the temperature was updated
        assert updated_heater["current_temperature"] == new_temp
        
        # Verify the status changed to STANDBY
        assert updated_heater["heater_status"] == WaterHeaterStatus.STANDBY
