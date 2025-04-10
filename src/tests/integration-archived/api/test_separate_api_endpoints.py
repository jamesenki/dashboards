"""
Integration tests for the separate database and mock API endpoints.

These tests verify that:
1. The database API endpoints (/api/db/water-heaters/*) always use the database
2. The mock API endpoints (/api/mock/water-heaters/*) always use mock data
3. Both APIs implement the same interface and return compatible data structures
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)

# Create test client
client = TestClient(app)


class TestSeparateApiEndpoints:
    """Tests for the separate database and mock API endpoints."""

    @pytest.fixture(scope="function")
    def setup_test_env(self):
        """Set up test environment with a clean configuration."""
        # Store original environment values
        original_use_mock = os.environ.get("USE_MOCK_DATA")
        original_db_path = os.environ.get("DATABASE_PATH")

        # Configure a test-specific database
        test_db_path = "test_separated_api.db"
        os.environ["DATABASE_PATH"] = test_db_path

        # Yield control to test
        yield

        # Clean up environment
        if original_use_mock is not None:
            os.environ["USE_MOCK_DATA"] = original_use_mock
        else:
            os.environ.pop("USE_MOCK_DATA", None)

        if original_db_path is not None:
            os.environ["DATABASE_PATH"] = original_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)

    def test_db_api_source_info(self, setup_test_env):
        """Test that the database API endpoint returns database source info."""
        # Make a request to the database API
        response = client.get("/api/db/water-heaters/data-source")

        # Verify the response
        assert response.status_code == 200
        data = response.json()

        # Verify it's using the database
        assert data["source_type"] == "database"
        assert "SQLite" in data["repository_type"]

    def test_mock_api_source_info(self, setup_test_env):
        """Test that the mock API endpoint returns mock source info."""
        # Make a request to the mock API
        response = client.get("/api/mock/water-heaters/data-source")

        # Verify the response
        assert response.status_code == 200
        data = response.json()

        # Verify it's using mock data
        assert data["source_type"] == "mock"
        assert "Mock" in data["repository_type"]
        assert data["is_simulated_data"] == True

    def test_both_apis_return_water_heaters(self, setup_test_env):
        """Test that both APIs return a list of water heaters with the same structure."""
        # Make requests to both APIs
        db_response = client.get("/api/db/water-heaters")
        mock_response = client.get("/api/mock/water-heaters")

        # Both should return 200 OK
        assert db_response.status_code == 200
        assert mock_response.status_code == 200

        # Both should return lists
        db_data = db_response.json()
        mock_data = mock_response.json()
        assert isinstance(db_data, list)
        assert isinstance(mock_data, list)

        # The mock API should have data by default
        assert len(mock_data) > 0

        # If the mock has data, verify the first item's structure
        if len(mock_data) > 0:
            mock_heater = mock_data[0]
            # Verify required fields exist based on the WaterHeater model
            assert "id" in mock_heater, "ID field missing"
            assert "name" in mock_heater, "Name field missing"
            assert "type" in mock_heater, "Type field missing"
            assert (
                "target_temperature" in mock_heater
            ), "Target temperature field missing"
            assert (
                "current_temperature" in mock_heater
            ), "Current temperature field missing"

    def test_consistent_interface_for_get_by_id(self, setup_test_env):
        """Test that both APIs handle the get-by-id endpoint consistently."""
        # Try to get a non-existent water heater
        test_id = "non-existent-id-12345"

        # Both should return 404 for non-existent IDs
        db_response = client.get(f"/api/db/water-heaters/{test_id}")
        mock_response = client.get(f"/api/mock/water-heaters/{test_id}")

        assert db_response.status_code == 404
        assert mock_response.status_code == 404

    def test_create_water_heater_in_mock(self, setup_test_env):
        """Test creating a water heater via the mock API."""
        # Prepare test data according to the WaterHeaterCreate schema
        test_heater = {
            "name": "Test Mock Heater",
            "target_temperature": 50.0,
            "min_temperature": 40.0,
            "max_temperature": 80.0,
            "mode": WaterHeaterMode.ECO.value,
        }

        # Create via mock API
        response = client.post("/api/mock/water-heaters", json=test_heater)

        # Verify creation was successful
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Mock Heater"
        assert "id" in data

        # Verify we can retrieve it
        heater_id = data["id"]
        get_response = client.get(f"/api/mock/water-heaters/{heater_id}")
        assert get_response.status_code == 200

        # The water heater should NOT be available via the DB API
        db_response = client.get(f"/api/db/water-heaters/{heater_id}")
        assert db_response.status_code == 404

    def test_original_api_still_works(self, setup_test_env):
        """Test that the original API endpoints still work for backward compatibility."""
        # Original endpoint should still return data
        response = client.get("/api/water-heaters")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_mock_api_simulation_controls(self, setup_test_env):
        """Test the mock API simulation controls."""
        # Enable network failure simulation
        response = client.post(
            "/api/mock/water-heaters/simulate/failure?failure_type=network"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Get simulation status
        status_response = client.get("/api/mock/water-heaters/simulation/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["simulation_type"] == "network"

        # Disable simulation
        disable_response = client.post(
            "/api/mock/water-heaters/simulate/failure?failure_type=none"
        )
        assert disable_response.status_code == 200
        disable_data = disable_response.json()
        assert "Disabled" in disable_data["message"]
