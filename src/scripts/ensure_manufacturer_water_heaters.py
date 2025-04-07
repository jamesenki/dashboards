#!/usr/bin/env python
"""
Script to ensure we have at least 2 water heaters per manufacturer (Rheem and AquaTherm) in PostgreSQL
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import project modules
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import required modules
try:
    from src.db.config import db_settings
    from src.models.device import DeviceStatus, DeviceType, ManufacturerType
    from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
    from src.repositories.postgres_water_heater_repository import (
        PostgresWaterHeaterRepository,
    )
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)


async def ensure_manufacturer_water_heaters():
    """Ensure we have at least 2 water heaters per manufacturer in PostgreSQL."""
    # Set environment to development
    os.environ["IOTSPHERE_ENV"] = "development"

    # Initialize PostgreSQL repository
    try:
        postgres_repo = PostgresWaterHeaterRepository(
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME,
            user=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
        )

        # Initialize the repository
        await postgres_repo._initialize()

        # Get all water heaters
        water_heaters = await postgres_repo.get_water_heaters()
        logger.info(f"Found {len(water_heaters)} water heaters in PostgreSQL database")

        # Count water heaters by manufacturer
        manufacturers_count = defaultdict(list)

        for heater in water_heaters:
            manufacturers_count[str(heater.manufacturer)].append(heater.id)

        # Display current manufacturer distribution
        logger.info("\n--- Current Manufacturer Distribution ---")
        for manufacturer, heater_ids in manufacturers_count.items():
            count = len(heater_ids)
            logger.info(f"Manufacturer: {manufacturer} - Count: {count}")
            logger.info(
                f"  IDs: {', '.join(heater_ids[:5])}"
                + (", ..." if len(heater_ids) > 5 else "")
            )

        # Check if we have at least 2 water heaters for Rheem and AquaTherm
        rheem_count = len(manufacturers_count.get(ManufacturerType.RHEEM.value, []))
        aquatherm_count = len(
            manufacturers_count.get(ManufacturerType.AQUATHERM.value, [])
        )

        logger.info("\n--- Requirements Check ---")
        logger.info(
            f"Rheem water heaters: {rheem_count} {'✅' if rheem_count >= 2 else '❌'}"
        )
        logger.info(
            f"AquaTherm water heaters: {aquatherm_count} {'✅' if aquatherm_count >= 2 else '❌'}"
        )

        # Add water heaters if needed
        manufacturers_to_add = []

        if rheem_count < 2:
            manufacturers_to_add.extend(
                [ManufacturerType.RHEEM.value] * (2 - rheem_count)
            )

        if aquatherm_count < 2:
            manufacturers_to_add.extend(
                [ManufacturerType.AQUATHERM.value] * (2 - aquatherm_count)
            )

        if manufacturers_to_add:
            logger.info(f"\nNeed to add {len(manufacturers_to_add)} water heaters")

            for manufacturer in manufacturers_to_add:
                # Create a new water heater for this manufacturer
                now_str = datetime.now().isoformat()
                new_heater = WaterHeater(
                    id=f"wh-{uuid.uuid4().hex[:8]}",
                    name=f"New {manufacturer} Water Heater",
                    manufacturer=manufacturer,
                    brand=manufacturer,
                    model=f"{manufacturer}-WH{uuid.uuid4().hex[:4].upper()}",
                    type=DeviceType.WATER_HEATER,
                    status=DeviceStatus.ONLINE,
                    location="Main Building",
                    current_temperature=45.0,
                    target_temperature=60.0,
                    mode=WaterHeaterMode.ECO,
                    heater_status=WaterHeaterStatus.STANDBY,
                    efficiency_rating=0.85,
                    installation_date=now_str,
                    warranty_expiry=(
                        datetime.now() + timedelta(days=365 * 5)
                    ).isoformat(),  # 5-year warranty
                    last_maintenance=now_str,
                    last_seen=now_str,
                    health_status="Good",
                    metadata={
                        "source": "PostgreSQL migration",
                        "created_by": "ensure_manufacturer_water_heaters.py",
                    },
                )

                # Add to PostgreSQL
                logger.info(f"Adding new {manufacturer} water heater: {new_heater.id}")
                await postgres_repo.create_water_heater(new_heater)

                # Add a couple of readings
                for i in range(2):
                    timestamp = datetime.now() - timedelta(hours=i)
                    from src.models.water_heater import WaterHeaterReading

                    # Create properly formed reading object
                    reading = WaterHeaterReading(
                        id=str(uuid.uuid4()),
                        temperature=45.0 + i,
                        pressure=50.0,
                        energy_usage=2.5,
                        flow_rate=5.0,
                        timestamp=timestamp.isoformat(),  # Convert to ISO format string
                    )

                    await postgres_repo.add_reading(new_heater.id, reading)

            # Verify results after additions
            water_heaters = await postgres_repo.get_water_heaters()
            manufacturers_count = defaultdict(list)

            for heater in water_heaters:
                manufacturers_count[str(heater.manufacturer)].append(heater.id)

            logger.info("\n--- Updated Manufacturer Distribution ---")
            for manufacturer, heater_ids in manufacturers_count.items():
                count = len(heater_ids)
                logger.info(f"Manufacturer: {manufacturer} - Count: {count}")

            # Final check
            rheem_count = len(manufacturers_count.get(ManufacturerType.RHEEM.value, []))
            aquatherm_count = len(
                manufacturers_count.get(ManufacturerType.AQUATHERM.value, [])
            )

            logger.info("\n--- Final Requirements Check ---")
            logger.info(
                f"Rheem water heaters: {rheem_count} {'✅' if rheem_count >= 2 else '❌'}"
            )
            logger.info(
                f"AquaTherm water heaters: {aquatherm_count} {'✅' if aquatherm_count >= 2 else '❌'}"
            )

            if rheem_count >= 2 and aquatherm_count >= 2:
                logger.info(
                    "✅ Requirements met: At least 2 water heaters per manufacturer"
                )
            else:
                logger.warning("❌ Requirements not met: Still need more water heaters")
        else:
            logger.info(
                "✅ No additional water heaters needed - requirements already met"
            )

    except Exception as e:
        logger.error(f"Error ensuring manufacturer water heaters: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the database connection
        if "postgres_repo" in locals() and postgres_repo.pool:
            await postgres_repo.pool.close()
            logger.info("Closed PostgreSQL connection pool")


if __name__ == "__main__":
    asyncio.run(ensure_manufacturer_water_heaters())
