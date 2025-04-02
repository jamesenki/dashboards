"""
Test script to check repository data
"""
import asyncio

from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)


async def test_repositories():
    # Check mock repository
    mock_repo = MockWaterHeaterRepository()
    mock_devices = await mock_repo.get_water_heaters()
    print(f"Mock repository has {len(mock_devices)} water heaters")
    for device in mock_devices[:3]:  # Show first 3 only
        print(f"ID: {device.id}, Name: {device.name}")

    # Try specific device to see if it exists
    test_id = "wh-5434c9c3"
    device = await mock_repo.get_water_heater(test_id)
    if device:
        print(f"Found device {test_id} in mock repository")
    else:
        print(f"Device {test_id} NOT found in mock repository")

    # Check SQLite repository
    print("\nChecking SQLite repository...")
    try:
        sqlite_repo = SQLiteWaterHeaterRepository()
        sqlite_devices = await sqlite_repo.get_water_heaters()
        print(f"SQLite repository has {len(sqlite_devices)} water heaters")
        for device in sqlite_devices[:3]:  # Show first 3 only
            print(f"ID: {device.id}, Name: {device.name}")

        # Try specific device
        device = await sqlite_repo.get_water_heater(test_id)
        if device:
            print(f"Found device {test_id} in SQLite repository")
        else:
            print(f"Device {test_id} NOT found in SQLite repository")
    except Exception as e:
        print(f"Error with SQLite repository: {e}")


if __name__ == "__main__":
    asyncio.run(test_repositories())
