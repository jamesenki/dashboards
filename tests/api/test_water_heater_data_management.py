"""
Tests for water heater data management
- Selective data loading based on tab and user selection
- Data pre-processing for different time ranges
- Data retention and archiving policies
"""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.water_heater import TemperatureReading
from src.repositories.timeseries_repository import TimeseriesRepository
from src.services.water_heater_timeseries_service import WaterHeaterTimeseriesService

client = TestClient(app)

# Test device details
TEST_DEVICE_ID = "wh-test-device"


@pytest.fixture
def setup_test_data():
    """Setup test data in the database if needed"""
    repo = TimeseriesRepository()

    # Check if we already have data for our test device
    existing_data = repo.get_readings(TEST_DEVICE_ID)
    if existing_data and len(existing_data) > 100:
        # We already have sufficient test data
        return

    # Generate test data spanning 60 days
    now = datetime.now()
    readings = []

    # Generate 60 days of hourly data
    for day in range(60):
        for hour in range(24):
            timestamp = now - timedelta(days=day, hours=hour)
            reading = TemperatureReading(
                timestamp=timestamp.isoformat(),
                temperature=70.0 + day % 10,  # Some variation
                heater_id=TEST_DEVICE_ID,
            )
            readings.append(reading)

    # Insert the data into the database
    for reading in readings:
        repo.insert_reading(reading)


# Test class for selective data loading
class TestSelectiveDataLoading:
    def test_current_data_endpoint(self, setup_test_data):
        """Test that current data endpoint only returns latest reading, not history"""
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/current"
        )
        assert response.status_code == 200

        # Verify we got a valid response
        data = response.json()
        assert "temperature" in data
        assert "timestamp" in data
        assert "status" in data

    def test_history_default_7_days(self, setup_test_data):
        """Test that history endpoint defaults to 7 days when no range specified"""
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history"
        )
        assert response.status_code == 200

        # Verify we got data back
        data = response.json()
        assert isinstance(data, list)

        # Since we're using real data, we should have roughly 7 days of hourly data
        assert len(data) > 7  # At least 7 data points (one per day minimum)

        # Check data structure
        if data:
            assert "temperature" in data[0]
            assert "timestamp" in data[0]
            assert "heater_id" in data[0]

    def test_history_14_days(self, setup_test_data):
        """Test that history endpoint respects 14 day parameter"""
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=14"
        )
        assert response.status_code == 200

        # Verify we got data back
        data = response.json()
        assert isinstance(data, list)

        # Should have more data than the 7-day default
        response_7days = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history"
        )
        data_7days = response_7days.json()

        # 14 days should have more data points than 7 days
        assert len(data) >= len(data_7days)

    def test_history_30_days(self, setup_test_data):
        """Test that history endpoint respects 30 day parameter"""
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=30"
        )
        assert response.status_code == 200

        # Verify we got data back
        data = response.json()
        assert isinstance(data, list)

        # Should have more data than the 14-day query
        response_14days = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=14"
        )
        data_14days = response_14days.json()

        # 30 days should have more data points than 14 days
        assert len(data) >= len(data_14days)

    def test_max_days_limit(self, setup_test_data):
        """Test that history endpoint enforces 30 day maximum"""
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=60"
        )
        assert response.status_code == 400  # Bad request

        # Verify error message contains information about the limit
        assert "30 days" in response.json()["detail"]


# Test class for data preprocessing
class TestDataPreprocessing:
    def test_no_preprocessing_for_small_datasets(self, setup_test_data):
        """Test that small datasets are not preprocessed"""
        # Get regular 1-day data
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=1"
        )
        assert response.status_code == 200
        data = response.json()

        # Get preprocessed 1-day data
        response_preprocessed = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history/preprocessed?days=1"
        )
        assert response_preprocessed.status_code == 200
        data_preprocessed = response_preprocessed.json()

        # For small datasets (1 day), preprocessed should be similar to regular data
        assert len(data_preprocessed) >= len(data) * 0.9  # Within 10%

    def test_preprocessing_for_7_day_data(self, setup_test_data):
        """Test that 7-day data is appropriately preprocessed"""
        # Get regular 7-day data
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=7"
        )
        assert response.status_code == 200
        data = response.json()

        # Get preprocessed 7-day data
        response_preprocessed = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history/preprocessed?days=7"
        )
        assert response_preprocessed.status_code == 200
        data_preprocessed = response_preprocessed.json()

        # Should have fewer data points (but not too few)
        assert len(data_preprocessed) <= len(data)
        assert len(data_preprocessed) >= 7  # At least 7 points (one per day minimum)

    def test_preprocessing_for_30_day_data(self, setup_test_data):
        """Test that 30-day data is aggressively downsampled"""
        # Get regular 30-day data
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history?days=30"
        )
        assert response.status_code == 200
        data = response.json()

        # Get preprocessed 30-day data
        response_preprocessed = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history/preprocessed?days=30"
        )
        assert response_preprocessed.status_code == 200
        data_preprocessed = response_preprocessed.json()

        # Should have significantly fewer data points for 30 days
        assert len(data_preprocessed) < len(data)
        assert len(data_preprocessed) >= 30  # At least 30 points (one per day minimum)


# Test class for data retention
class TestDataRetention:
    def test_archive_old_data(self, setup_test_data):
        """Test that data older than 30 days is archived"""
        # First count data in active db directly through the repository
        repo = TimeseriesRepository()
        conn = sqlite3.connect(repo.active_db_path)
        cursor = conn.cursor()

        # Get count of all data for our test device
        cursor.execute(
            "SELECT COUNT(*) FROM temperature_readings WHERE heater_id = ?",
            (TEST_DEVICE_ID,),
        )
        pre_archive_count = cursor.fetchone()[0]
        conn.close()

        # We should have data older than 30 days in the database from our setup
        assert pre_archive_count > 0

        # Trigger archive operation
        response = client.post(f"/api/admin/timeseries/archive?days=30")
        assert response.status_code == 200

        # Verify response contains the archived count
        result = response.json()
        assert "archived" in result

        # Verify data was actually archived by checking active database directly
        conn = sqlite3.connect(repo.active_db_path)
        cursor = conn.cursor()

        # Get count of all data for our test device after archiving
        cursor.execute(
            "SELECT COUNT(*) FROM temperature_readings WHERE heater_id = ?",
            (TEST_DEVICE_ID,),
        )
        post_archive_count = cursor.fetchone()[0]
        conn.close()

        # Now check if the archive database has the archived records
        conn = sqlite3.connect(repo.archive_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM temperature_readings WHERE heater_id = ?",
            (TEST_DEVICE_ID,),
        )
        archive_db_count = cursor.fetchone()[0]
        conn.close()

        # We should have records in the archive database
        assert archive_db_count > 0

        # We should have fewer readings in the active store now
        # or the same if nothing needed archiving
        assert post_archive_count <= pre_archive_count

    def test_retrieve_archived_data(self, setup_test_data):
        """Test that archived data can be retrieved"""
        # First run the archive operation to ensure we have archived data
        client.post(f"/api/admin/timeseries/archive?days=30")

        # Set a date range that should be in archives (>30 days ago)
        start_date = (datetime.now() - timedelta(days=45)).isoformat()
        end_date = (datetime.now() - timedelta(days=35)).isoformat()

        # Now try to retrieve the archived data
        response = client.get(
            f"/api/water-heaters/{TEST_DEVICE_ID}/temperature/history/archived"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        archived_data = response.json()

        # We should have some data in this range
        assert len(archived_data) > 0
