"""
Ensure all water heaters have shadow documents script.

This script follows TDD principles by:
1. Validating assumptions through testing (all water heaters should have shadows)
2. Taking corrective action when tests fail (creating shadows for missing assets)
3. Verifying the result (testing that all water heaters now have shadows)

It retrieves all water heaters from the repository and ensures each has a
corresponding shadow document with populated historical data.
"""
import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.infrastructure.device_shadow.storage_factory import (
    create_shadow_storage_provider,
)
from src.models.device import DeviceStatus
from src.models.water_heater import WaterHeaterStatus
from src.services.device_shadow import DeviceShadowService
from src.services.water_heater import WaterHeaterService

# Configure MongoDB as the shadow storage provider
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
os.environ["MONGODB_DB_NAME"] = os.environ.get("MONGODB_DB_NAME", "iotsphere")

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ShadowValidator:
    """Validates and ensures that all assets have shadow documents"""

    def __init__(self):
        """Initialize the validator with required services"""
        self.water_heater_service = WaterHeaterService()
        self.shadow_service = None  # Will be initialized in setup method
        self.errors = []
        self.created_count = 0
        self.already_exists_count = 0
        self.total_heaters = 0

    async def setup(self):
        """Set up services with proper storage providers"""
        logger.info("Initializing services with MongoDB storage")

        # Create MongoDB storage provider
        storage_provider = await create_shadow_storage_provider()

        # Initialize shadow service with MongoDB storage
        self.shadow_service = DeviceShadowService(storage_provider=storage_provider)
        logger.info("Services initialized with MongoDB storage")

    async def validate_and_ensure_shadows(self):
        """
        Test that all water heaters have shadows, and create them if they don't
        Following TDD principles: Red (detect missing shadows), Green (create shadows), Refactor (verify all exist)
        """
        # Set up services with MongoDB storage
        await self.setup()

        logger.info("Starting validation of shadow documents for all water heaters")

        # Get all water heaters - gather requirements
        water_heaters = await self.water_heater_service.get_water_heaters()
        self.total_heaters = len(water_heaters)
        logger.info(f"Found {self.total_heaters} water heaters in the repository")

        # Test each water heater for shadow existence (Red phase)
        missing_shadows = []
        for heater in water_heaters:
            try:
                await self.shadow_service.get_device_shadow(heater.id)
                logger.info(f"Shadow document already exists for {heater.id}")
                self.already_exists_count += 1
            except ValueError:
                logger.warning(f"No shadow document found for water heater {heater.id}")
                missing_shadows.append(heater)

        # Create missing shadows (Green phase)
        for heater in missing_shadows:
            try:
                await self.create_shadow_with_history(heater)
                self.created_count += 1
            except Exception as e:
                error_msg = f"Error creating shadow for {heater.id}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        # Verify all shadows now exist (Refactor phase)
        all_exist = await self.verify_all_shadows_exist(water_heaters)

        # Report results
        logger.info("Shadow validation complete")
        logger.info(f"Total water heaters: {self.total_heaters}")
        logger.info(f"Already had shadows: {self.already_exists_count}")
        logger.info(f"Shadows created: {self.created_count}")
        logger.info(f"Errors encountered: {len(self.errors)}")
        logger.info(f"All shadows exist now: {all_exist}")

        if self.errors:
            logger.error("The following errors occurred:")
            for error in self.errors:
                logger.error(f"  - {error}")

        return all_exist

    async def create_shadow_with_history(self, heater):
        """
        Create a shadow document for a water heater and populate it with historical data

        Args:
            heater: Water heater instance
        """
        logger.info(f"Creating shadow document for {heater.id}")

        # Prepare shadow data
        reported_state = {
            "temperature": heater.current_temperature,
            "target_temperature": heater.target_temperature,
            "status": DeviceStatus.ONLINE.value,
            "heater_status": getattr(
                heater, "heater_status", WaterHeaterStatus.STANDBY.value
            ),
            "mode": getattr(heater, "mode", "ECO"),
            "last_updated": datetime.now().isoformat() + "Z",
        }

        desired_state = {
            "target_temperature": heater.target_temperature,
            "mode": getattr(heater, "mode", "ECO"),
        }

        # Create shadow document
        await self.shadow_service.create_device_shadow(
            device_id=heater.id,
            reported_state=reported_state,
            desired_state=desired_state,
        )
        logger.info(f"Created shadow document for {heater.id}")

        # Generate shadow history for the past week
        await self.generate_shadow_history(heater)

    async def generate_shadow_history(self, heater, days=7):
        """
        Generate shadow history entries for a water heater for the past week.

        Args:
            heater: Water heater instance
            days: Number of days of history to generate (default: 7)
        """
        logger.info(
            f"Generating shadow history for {heater.id} for the past {days} days"
        )

        current_time = datetime.now()
        base_temp = heater.current_temperature
        target_temp = heater.target_temperature

        # Generate one entry every 3 hours for the past week
        hours = days * 24
        for i in range(hours, 0, -3):  # Step by 3 hours
            # Calculate timestamp (going backwards from now)
            point_time = current_time - timedelta(hours=i)

            # Add daily cycle (hotter during day, cooler at night)
            hour = point_time.hour
            time_factor = ((hour - 12) / 12) * 3  # ±3 degree variation by time of day

            # Add some randomness
            random_factor = random.uniform(-1.0, 1.0)

            # Calculate temperature
            temp = base_temp + time_factor + random_factor
            temp = round(
                max(min(temp, target_temp + 5), target_temp - 10), 1
            )  # Keep within reasonable range

            # Determine heater status based on temperature and target
            if temp < target_temp - 1.0:
                heater_status = WaterHeaterStatus.HEATING.value
            else:
                heater_status = WaterHeaterStatus.STANDBY.value

            # Update shadow with historical data
            reported_state = {
                "temperature": temp,
                "heater_status": heater_status,
                "status": DeviceStatus.ONLINE.value,  # Device status remains online
                "timestamp": point_time.isoformat() + "Z",
            }

            # Update shadow (this will create history entries)
            try:
                await self.shadow_service.update_device_shadow(
                    device_id=heater.id, reported_state=reported_state
                )
            except Exception as e:
                logger.error(
                    f"Error adding history for {heater.id} at {point_time}: {e}"
                )
                raise

        logger.info(f"Completed generating {days} days of history for {heater.id}")

    async def verify_all_shadows_exist(self, water_heaters):
        """
        Verify that all water heaters now have shadow documents

        Args:
            water_heaters: List of water heater instances

        Returns:
            bool: True if all water heaters have shadow documents, False otherwise
        """
        logger.info("Verifying all water heaters have shadow documents")

        for heater in water_heaters:
            try:
                await self.shadow_service.get_device_shadow(heater.id)
            except ValueError:
                logger.error(f"Shadow document still missing for {heater.id}")
                return False

        logger.info("All water heaters have shadow documents")
        return True


async def main():
    """Run the shadow validation and creation process"""
    try:
        # Configure MongoDB for shadow storage
        logger.info(f"Using MongoDB for shadow storage: {os.environ['MONGODB_URI']}")

        # Run validation and creation
        validator = ShadowValidator()
        success = await validator.validate_and_ensure_shadows()

        # Show connection information for reference
        logger.info(f"Shadow storage type: {os.environ.get('SHADOW_STORAGE_TYPE')}")
        logger.info(f"MongoDB URI: {os.environ.get('MONGODB_URI')}")
        logger.info(f"MongoDB database: {os.environ.get('MONGODB_DB_NAME')}")

        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error running shadow validation: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
