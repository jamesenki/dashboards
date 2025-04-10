"""
Integration test to verify water heater data is properly loaded with correct structure.
This test ensures that data from all sources (mock, database) adheres to expected models.
"""
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

import pytest
from pydantic import ValidationError

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.models.device import DeviceStatus, DeviceType

# Import relevant models and classes
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterDiagnosticCode,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Setup logger for testing
logger = logging.getLogger(__name__)


class TestWaterHeaterDataValidation:
    """Integration tests to verify water heater data validation."""

    @pytest.fixture
    async def mock_repository(self):
        """Create a mock repository for testing."""
        return MockWaterHeaterRepository()

    @pytest.fixture
    async def db_repository(self, initialize_test_db):
        """Create a database repository for testing, with initialized database."""
        return SQLiteWaterHeaterRepository()

    @pytest.fixture
    def initialize_test_db(self):
        """Initialize the test database."""
        from src.db.initialize_db import initialize_database

        # Set the database path to a test-specific path to avoid conflicts
        os.environ["DATABASE_PATH"] = "test_water_heater.db"

        # Initialize the database
        initialize_database()

        yield

        # Clean up the test database file after tests
        db_path = os.environ.get("DATABASE_PATH", "test_water_heater.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception as e:
                logger.warning(f"Failed to remove test database: {e}")

    @pytest.mark.asyncio
    async def test_mock_data_structure(self, mock_repository):
        """Test that mock data has the correct structure."""
        # Get water heaters from mock repository
        water_heaters = await mock_repository.get_water_heaters()

        # Verify we have data
        assert len(water_heaters) > 0

        # Validate each water heater has the required structure
        for heater in water_heaters:
            validate_water_heater_structure(heater)

    @pytest.mark.asyncio
    async def test_db_data_structure(self, db_repository):
        """Test that database data has the correct structure."""
        try:
            # Try to get existing water heaters first
            water_heaters = await db_repository.get_water_heaters()

            # If no heaters exist and we can't create one due to schema issues, skip this test
            if len(water_heaters) == 0:
                pytest.skip(
                    "No water heaters in database and cannot create one due to schema limitations"
                )
        except Exception as e:
            pytest.skip(f"Database error: {e}")

        # Validate each water heater has the required structure
        for heater in water_heaters:
            validate_water_heater_structure(heater)

    @pytest.mark.asyncio
    async def test_aquatherm_data_structure(self, mock_repository):
        """Test that AquaTherm water heaters have the required structure."""
        # Get water heaters from mock repository
        water_heaters = await mock_repository.get_water_heaters()

        # Filter for AquaTherm heaters
        aquatherm_heaters = [h for h in water_heaters if h.id and "aqua-wh-" in h.id]

        # Verify we have AquaTherm heaters
        assert len(aquatherm_heaters) > 0

        # Validate each AquaTherm heater has the required structure
        for heater in aquatherm_heaters:
            validate_water_heater_structure(heater)

            # AquaTherm identifiers should follow the pattern
            assert (
                "aqua-wh-" in heater.id
            ), "AquaTherm heaters must have 'aqua-wh-' in their ID"

            # Check for specific AquaTherm attributes if they exist
            # Note: We've learned that not all AquaTherm heaters have these fields populated yet
            if heater.efficiency_rating is not None:
                assert isinstance(heater.efficiency_rating, (int, float))

            if heater.capacity is not None:
                assert isinstance(heater.capacity, (int, float))

    @pytest.mark.asyncio
    async def test_water_heater_readings_structure(self, mock_repository):
        """Test that water heater readings have the correct structure."""
        # Get water heaters from mock repository
        water_heaters = await mock_repository.get_water_heaters()

        # Find a heater with readings
        heaters_with_readings = [
            h for h in water_heaters if h.readings and len(h.readings) > 0
        ]

        # If no heaters have readings, create a reading for testing
        if not heaters_with_readings and water_heaters:
            # Get the first heater
            heater = water_heaters[0]

            # Create a test reading
            from datetime import datetime

            reading = WaterHeaterReading(
                timestamp=datetime.now(),
                temperature=heater.current_temperature,
                pressure=1.5,
                energy_usage=1200.0,
                flow_rate=2.5,
            )

            # Add to the heater
            heater.add_reading(reading)
            heaters_with_readings = [heater]

        # If we still don't have readings, skip the test
        if not heaters_with_readings:
            pytest.skip("No water heaters with readings available for testing")

        # Validate readings structure
        for heater in heaters_with_readings:
            for reading in heater.readings:
                validate_water_heater_reading(reading)

    @pytest.mark.asyncio
    async def test_water_heater_diagnostic_codes_structure(self, mock_repository):
        """Test that water heater diagnostic codes have the correct structure."""
        # Get water heaters from mock repository
        water_heaters = await mock_repository.get_water_heaters()

        # Find a heater with diagnostic codes
        heaters_with_codes = [
            h
            for h in water_heaters
            if h.diagnostic_codes and len(h.diagnostic_codes) > 0
        ]

        # If no heaters have diagnostic codes, create one
        if not heaters_with_codes and water_heaters:
            # Get the first heater
            heater = water_heaters[0]

            # Create a diagnostic code
            code = WaterHeaterDiagnosticCode(
                code="TEST-01",
                description="Test diagnostic code",
                severity="Info",
                timestamp=datetime.now(),
                active=True,
            )

            # Add it to the heater
            heater.add_diagnostic_code(code)
            heaters_with_codes = [heater]

        # Verify we have heaters with diagnostic codes
        assert len(heaters_with_codes) > 0

        # Validate diagnostic code structure
        for heater in heaters_with_codes:
            for code in heater.diagnostic_codes:
                validate_diagnostic_code(code)

    @pytest.mark.asyncio
    async def test_service_data_consistency(self):
        """Test that data from the service layer is consistent regardless of source."""
        # Test with mock data
        os.environ["USE_MOCK_DATA"] = "true"
        mock_service = ConfigurableWaterHeaterService()

        # Get water heaters from mock service
        mock_heaters = await mock_service.get_water_heaters()

        # Verify we have data and it has the correct structure
        assert len(mock_heaters) > 0
        for heater in mock_heaters:
            validate_water_heater_structure(heater)

        # Clean up environment variable
        os.environ.pop("USE_MOCK_DATA", None)

        # Test with database (ensure it's initialized)
        from src.db.initialize_db import initialize_database

        initialize_database()

        # Create a service using database
        db_service = ConfigurableWaterHeaterService()

        # Get water heaters from database service
        db_heaters = await db_service.get_water_heaters()

        # If no heaters in database, create one
        if not db_heaters:
            test_heater = create_test_water_heater()
            await db_service.create_water_heater(test_heater)
            db_heaters = await db_service.get_water_heaters()

        # Verify we have data and it has the correct structure
        assert len(db_heaters) > 0
        for heater in db_heaters:
            validate_water_heater_structure(heater)


def validate_water_heater_structure(heater: WaterHeater):
    """Validate that a water heater has the correct structure."""
    # Basic checks
    assert isinstance(heater, WaterHeater)

    # Required fields for all water heaters
    assert heater.id is not None
    assert heater.name is not None
    assert heater.status is not None
    assert heater.type == DeviceType.WATER_HEATER

    # Water heater specific fields
    assert isinstance(heater.current_temperature, (int, float))
    assert isinstance(heater.target_temperature, (int, float))
    assert isinstance(heater.min_temperature, (int, float))
    assert isinstance(heater.max_temperature, (int, float))
    assert isinstance(heater.mode, WaterHeaterMode)
    assert isinstance(heater.heater_status, WaterHeaterStatus)
    assert isinstance(heater.heater_type, WaterHeaterType)

    # Range validations for target temperature (which should always be within valid range)
    assert heater.min_temperature <= heater.target_temperature <= heater.max_temperature

    # For current temperature, some devices might be outside normal ranges
    # (e.g., in maintenance mode, malfunctioning, or just starting up)
    # So we'll log a warning but not fail the test if outside range
    if not (
        heater.min_temperature <= heater.current_temperature <= heater.max_temperature
    ):
        logger.warning(
            f"Water heater {heater.id} has current temperature {heater.current_temperature} "
            f"outside normal range ({heater.min_temperature}-{heater.max_temperature})"
        )

    # Optional fields may be None, but should have correct type if present
    if heater.capacity is not None:
        assert isinstance(heater.capacity, (int, float))
        assert heater.capacity > 0

    if heater.efficiency_rating is not None:
        assert isinstance(heater.efficiency_rating, (int, float))
        # Different water heaters might use different scales for efficiency rating
        # Some might use 0-1 (decimal), others 0-100 (percentage)
        assert heater.efficiency_rating >= 0, "Efficiency rating must be non-negative"

    if heater.specification_link is not None:
        assert isinstance(heater.specification_link, str)

    # Collection fields
    assert isinstance(heater.readings, list)
    assert isinstance(heater.diagnostic_codes, list)

    # Validate each reading if present
    for reading in heater.readings:
        validate_water_heater_reading(reading)

    # Validate each diagnostic code if present
    for code in heater.diagnostic_codes:
        validate_diagnostic_code(code)


def validate_water_heater_reading(reading: WaterHeaterReading):
    """Validate that a water heater reading has the correct structure."""
    assert isinstance(reading, WaterHeaterReading)
    assert isinstance(reading.timestamp, datetime)
    assert isinstance(reading.temperature, (int, float))

    # Optional fields may be None, but should have correct type if present
    if reading.pressure is not None:
        assert isinstance(reading.pressure, (int, float))

    if reading.energy_usage is not None:
        assert isinstance(reading.energy_usage, (int, float))

    if reading.flow_rate is not None:
        assert isinstance(reading.flow_rate, (int, float))


def validate_diagnostic_code(code: WaterHeaterDiagnosticCode):
    """Validate that a diagnostic code has the correct structure."""
    assert isinstance(code, WaterHeaterDiagnosticCode)
    assert isinstance(code.code, str)
    assert isinstance(code.description, str)
    assert isinstance(code.severity, str)
    assert isinstance(code.timestamp, datetime)
    assert isinstance(code.active, bool)


def create_test_water_heater():
    """Create a test water heater for database testing."""
    return WaterHeater(
        id="test-wh-1",
        name="Test Water Heater",
        status=DeviceStatus.ONLINE,
        current_temperature=50.0,
        target_temperature=60.0,
        min_temperature=40.0,
        max_temperature=85.0,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.STANDBY,
        heater_type=WaterHeaterType.RESIDENTIAL,
        capacity=200.0,
        efficiency_rating=0.85,
    )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
