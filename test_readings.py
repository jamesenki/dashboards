"""
Test to verify water heater readings functionality - following TDD principles.
"""
import os
import asyncio
import uuid
from datetime import datetime

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.water_heater import WaterHeaterReading
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository

# Use an in-memory database for testing
TEST_DB_PATH = ":memory:"

async def test_add_and_retrieve_reading():
    """Test that we can add a reading with pressure, energy usage, and flow rate and retrieve it."""
    # Create repository with in-memory database
    repository = SQLiteWaterHeaterRepository(TEST_DB_PATH)
    
    # Create a test water heater
    from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus, WaterHeaterType
    
    test_water_heater = WaterHeater(
        id="test-wh-id",
        name="Test Water Heater",
        model="Test Model",
        manufacturer="Test Manufacturer",
        target_temperature=140.0,
        current_temperature=135.0,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.STANDBY,
        heater_type=WaterHeaterType.RESIDENTIAL
    )
    
    # Add the water heater to the database
    await repository.create_water_heater(test_water_heater)
    
    # Create a reading with complete data
    reading_id = str(uuid.uuid4())
    reading = WaterHeaterReading(
        id=reading_id,
        timestamp=datetime.now(),
        temperature=135.5,
        pressure=45.0,
        energy_usage=3.2,
        flow_rate=2.5
    )
    
    # Add the reading to the water heater
    await repository.add_reading(test_water_heater.id, reading)
    
    # Get the water heater from the database
    updated_water_heater = await repository.get_water_heater(test_water_heater.id)
    
    # Verify the reading was added with complete data
    assert updated_water_heater is not None, "Failed to retrieve water heater"
    assert len(updated_water_heater.readings) > 0, "No readings found for water heater"
    
    latest_reading = updated_water_heater.readings[0]
    print(f"Reading ID: {latest_reading.id}")
    print(f"Temperature: {latest_reading.temperature}")
    print(f"Pressure: {latest_reading.pressure}")
    print(f"Energy Usage: {latest_reading.energy_usage}")
    print(f"Flow Rate: {latest_reading.flow_rate}")
    
    # Assert that all fields are present
    assert latest_reading.temperature is not None, "Temperature is missing"
    assert latest_reading.pressure is not None, "Pressure is missing"
    assert latest_reading.energy_usage is not None, "Energy usage is missing"
    assert latest_reading.flow_rate is not None, "Flow rate is missing"
    
    print("All tests passed!")

async def main():
    """Run the tests."""
    try:
        await test_add_and_retrieve_reading()
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
