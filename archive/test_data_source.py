"""
Test script to verify the application is using the database and not mock data.

This script uses the configurable water heater service with the new environment
configuration system to verify it's using the correct data source.
"""
import asyncio
import logging
import os
from pathlib import Path

from src.config import config
from src.config.env_provider import EnvironmentFileProvider
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_data_source():
    """Test which data source is being used by the configurable service."""
    # Setup environment configuration
    project_root = Path(__file__).parent
    config_dir = project_root / "config"

    # Get environment from command line or environment variable
    env = os.environ.get("APP_ENV", "development")
    logger.info(f"Using environment: {env}")

    # Initialize environment provider
    env_provider = EnvironmentFileProvider(config_dir, default_env=env)
    config.register_provider(env_provider, priority=50)

    # Check configuration settings
    use_mock_data = config.get("services.water_heater.use_mock_data", False)
    db_type = config.get("database.type", "sqlite")
    fallback_enabled = config.get("database.fallback_to_mock", True)

    logger.info(f"Configuration settings:")
    logger.info(f"  - Database type: {db_type}")
    logger.info(f"  - Use mock data: {use_mock_data}")
    logger.info(f"  - Fallback enabled: {fallback_enabled}")

    # Create the service
    logger.info("Creating configurable water heater service...")
    service = ConfigurableWaterHeaterService()

    # Log the type of repository being used
    repo_type = type(service.repository).__name__
    logger.info(f"Using repository type: {repo_type}")

    # Retrieve water heaters
    logger.info("Retrieving water heaters...")
    try:
        water_heaters = await service.get_water_heaters()
        logger.info(f"Retrieved {len(water_heaters)} water heaters")

        # Display the first few water heaters
        for i, wh in enumerate(water_heaters[:3]):
            logger.info(f"Water heater {i+1}:")
            logger.info(f"  - ID: {wh.id}")
            logger.info(f"  - Name: {wh.name}")
            logger.info(f"  - Type: {wh.heater_type}")
            logger.info(f"  - Status: {wh.status}")
            logger.info(f"  - Current Temp: {wh.current_temperature}°C")
            logger.info(f"  - Target Temp: {wh.target_temperature}°C")
    except Exception as e:
        logger.error(f"Error retrieving water heaters: {e}")

    # Return the repository type for verification
    return repo_type


if __name__ == "__main__":
    # Run the test
    repo_type = asyncio.run(test_data_source())

    # Provide a clear summary
    print("\n" + "=" * 50)
    print("DATA SOURCE TEST RESULTS")
    print("=" * 50)
    print(f"Repository type: {repo_type}")

    if "Mock" in repo_type:
        print("\n⚠️  USING MOCK REPOSITORY")
        print("The application is currently using mock data instead of the database.")
        print("Check your configuration settings and database connection.")
    else:
        print("\n✅ USING DATABASE REPOSITORY")
        print("The application is correctly using the database as configured.")
    print("=" * 50)
