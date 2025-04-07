#!/usr/bin/env python
"""
Test the PostgreSQL Water Heater Service

This script tests if the ConfigurableWaterHeaterService is correctly
connecting to PostgreSQL and retrieving water heater data.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set environment to development to use PostgreSQL
os.environ["IOTSPHERE_ENV"] = "development"

# Import after setting environment
from src.db.config import db_settings
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


async def test_service():
    """Test if the service is using PostgreSQL correctly."""
    print(f"\n📊 Testing ConfigurableWaterHeaterService with PostgreSQL...")
    print(f"Environment: {os.environ.get('IOTSPHERE_ENV')}")
    print(f"Database settings:")
    print(f"  Type: {db_settings.DB_TYPE}")
    print(f"  Host: {db_settings.DB_HOST}")
    print(f"  Port: {db_settings.DB_PORT}")
    print(f"  Database: {db_settings.DB_NAME}")
    print(f"  User: {db_settings.DB_USER}")

    # Create service
    service = ConfigurableWaterHeaterService()

    # Check data source info
    data_source = ConfigurableWaterHeaterService.get_data_source_info()
    print(f"\n🔍 Data Source Information:")
    print(f"  Using mock data: {data_source['is_using_mock_data']}")
    print(f"  Reason: {data_source['data_source_reason']}")

    # Get water heaters
    try:
        result = await service.get_water_heaters()

        # Handle tuple return (water_heaters, total_count) or just list of water heaters
        if isinstance(result, tuple):
            water_heaters, total_count = result
            print(
                f"\n✅ Successfully retrieved {len(water_heaters)} water heaters (total count: {total_count})"
            )
        else:
            water_heaters = result
            print(f"\n✅ Successfully retrieved {len(water_heaters)} water heaters")

        # Check first water heater
        if water_heaters and len(water_heaters) > 0:
            first_heater = water_heaters[0]
            print(f"\n📌 First water heater details:")
            print(f"  ID: {first_heater.id}")
            print(f"  Name: {first_heater.name}")
            print(
                f"  Manufacturer: {first_heater.manufacturer if hasattr(first_heater, 'manufacturer') else 'N/A'}"
            )
            print(
                f"  Model: {first_heater.model if hasattr(first_heater, 'model') else 'N/A'}"
            )
            print(f"  Temperature: {first_heater.current_temperature}")

    except Exception as e:
        print(f"\n❌ Error retrieving water heaters: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_service())
