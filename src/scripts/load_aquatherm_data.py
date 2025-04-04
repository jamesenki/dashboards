"""
Script to load test AquaTherm water heater data into the database
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from src.data.test_rheem_data import get_test_rheem_water_heaters
from src.db.connection import get_db_session
from src.db.repository import DeviceRepository
from src.models.device import DeviceStatus
from src.models.rheem_water_heater import (
    RheemEcoNetStatus,
    RheemProductSeries,
    RheemWaterHeater,
    RheemWaterHeaterMode,
    RheemWaterHeaterType,
)

logger = logging.getLogger(__name__)


async def load_aquatherm_test_data():
    """
    Load AquaTherm water heater test data into the database.

    This function is called during application startup to ensure
    test data is available for UI testing and development.

    Following TDD principles, we are updating the implementation to match
    our test expectations without changing the tests themselves.
    """
    logger.info("Loading AquaTherm water heater test data...")

    # Get database session
    session = await get_db_session()

    # If database not available, skip
    if not session:
        logger.warning("Database session is None. Skipping AquaTherm data loading.")
        return

    try:
        # Create repository
        repo = DeviceRepository(session)

        # Create direct AquaTherm test heaters with the exact IDs expected by our validation
        now = datetime.now()

        # List to hold our test heaters
        aquatherm_heaters = []

        # Create TANK type water heaters
        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-tank-001",
                name="Master Bath HydroMax",
                status=DeviceStatus.ONLINE,
                location="Master Bathroom",
                last_seen=now,
                heater_type=RheemWaterHeaterType.TANK,
                series=RheemProductSeries.PROFESSIONAL,
                manufacturer="AquaTherm",
                target_temperature=49.0,  # 120°F
                current_temperature=48.5,
                mode=RheemWaterHeaterMode.ENERGY_SAVER,
                smart_enabled=True,
                capacity=50.0,
                uef_rating=0.93,
                energy_star_certified=True,
                installation_date=now - timedelta(days=90),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=75,
                    last_connected=now - timedelta(minutes=5),
                    firmware_version="2.3.5",
                    update_available=False,
                    remote_control_enabled=True,
                ),
            )
        )

        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-tank-002",
                name="Basement HydroMax Plus",
                status=DeviceStatus.ONLINE,
                location="Basement",
                last_seen=now,
                heater_type=RheemWaterHeaterType.TANK,
                series=RheemProductSeries.PERFORMANCE_PLATINUM,
                manufacturer="AquaTherm",
                target_temperature=48.0,  # 118°F
                current_temperature=48.0,
                mode=RheemWaterHeaterMode.ENERGY_SAVER,
                smart_enabled=True,
                capacity=75.0,
                uef_rating=0.95,
                energy_star_certified=True,
                installation_date=now - timedelta(days=180),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=92,
                    last_connected=now - timedelta(minutes=15),
                    firmware_version="2.3.7",
                    update_available=True,
                    remote_control_enabled=True,
                ),
            )
        )

        # Create HYBRID type water heaters
        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-hybrid-001",
                name="Garage EcoHybrid",
                status=DeviceStatus.ONLINE,
                location="Garage",
                last_seen=now,
                heater_type=RheemWaterHeaterType.HYBRID,
                series=RheemProductSeries.PROTERRA,
                manufacturer="AquaTherm",
                target_temperature=51.5,  # 125°F
                current_temperature=50.0,
                mode=RheemWaterHeaterMode.HEAT_PUMP,
                smart_enabled=True,
                capacity=65.0,
                uef_rating=4.0,
                energy_star_certified=True,
                installation_date=now - timedelta(days=45),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=82,
                    last_connected=now - timedelta(minutes=2),
                    firmware_version="3.1.0",
                    update_available=True,
                    remote_control_enabled=True,
                ),
            )
        )

        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-hybrid-002",
                name="Utility Room EcoHybrid Pro",
                status=DeviceStatus.ONLINE,
                location="Utility Room",
                last_seen=now,
                heater_type=RheemWaterHeaterType.HYBRID,
                series=RheemProductSeries.PROFESSIONAL,
                manufacturer="AquaTherm",
                target_temperature=52.0,  # 126°F
                current_temperature=51.0,
                mode=RheemWaterHeaterMode.HIGH_DEMAND,
                smart_enabled=True,
                capacity=80.0,
                uef_rating=3.8,
                energy_star_certified=True,
                installation_date=now - timedelta(days=30),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=95,
                    last_connected=now - timedelta(minutes=1),
                    firmware_version="3.1.1",
                    update_available=False,
                    remote_control_enabled=True,
                ),
            )
        )

        # Create TANKLESS type water heaters
        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-tankless-001",
                name="Kitchen FlowMax Tankless",
                status=DeviceStatus.ONLINE,
                location="Kitchen",
                last_seen=now,
                heater_type=RheemWaterHeaterType.TANKLESS,
                series=RheemProductSeries.PERFORMANCE_PLATINUM,
                manufacturer="AquaTherm",
                target_temperature=54.0,  # 130°F
                current_temperature=54.0,
                mode=RheemWaterHeaterMode.HIGH_DEMAND,
                smart_enabled=True,
                uef_rating=0.95,
                energy_star_certified=True,
                installation_date=now - timedelta(days=120),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=90,
                    last_connected=now - timedelta(minutes=10),
                    firmware_version="2.4.0",
                    update_available=False,
                    remote_control_enabled=True,
                ),
            )
        )

        aquatherm_heaters.append(
            RheemWaterHeater(
                id="aqua-wh-tankless-002",
                name="Guest Suite FlowMax Ultra",
                status=DeviceStatus.ONLINE,
                location="Guest Suite",
                last_seen=now,
                heater_type=RheemWaterHeaterType.TANKLESS,
                series=RheemProductSeries.PROFESSIONAL,
                manufacturer="AquaTherm",
                target_temperature=50.0,  # 122°F
                current_temperature=50.0,
                mode=RheemWaterHeaterMode.ENERGY_SAVER,
                smart_enabled=True,
                uef_rating=0.97,
                energy_star_certified=True,
                installation_date=now - timedelta(days=60),
                econet_status=RheemEcoNetStatus(
                    connected=True,
                    wifi_signal_strength=88,
                    last_connected=now - timedelta(minutes=5),
                    firmware_version="2.4.1",
                    update_available=True,
                    remote_control_enabled=True,
                ),
            )
        )

        # Check if devices already exist and add/update them
        for heater in aquatherm_heaters:
            existing = await repo.get_device(heater.id)
            if not existing:
                logger.info(
                    f"Adding test AquaTherm water heater: {heater.name} ({heater.id})"
                )
                await repo.create_device(heater)
            else:
                logger.info(
                    f"Test AquaTherm water heater already exists: {heater.name} ({heater.id})"
                )
                # Update the existing heater with the new information
                await repo.update_device(heater.id, heater)
                logger.info(
                    f"Updated test AquaTherm water heater: {heater.name} ({heater.id})"
                )

        logger.info(
            f"Finished loading {len(aquatherm_heaters)} AquaTherm water heater test data items"
        )
    except Exception as e:
        logger.error(f"Error loading AquaTherm test data: {str(e)}")
    finally:
        if session:
            await session.close()


async def initialize_aquatherm_data():
    """
    Initialize the AquaTherm test data loading process.
    This function can be called directly from the startup event.
    """
    await load_aquatherm_test_data()


# For testing purposes - can run this script directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(load_aquatherm_test_data())
