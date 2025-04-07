#!/usr/bin/env python3
"""
Force the system to use PostgreSQL as the only data source.

This script temporarily modifies the ConfigurableWaterHeaterService to:
1. Disable fallback to mock data
2. Force the service to use PostgreSQL exclusively
3. Disable all mock data sources
"""
import asyncio
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import database settings
from src.db.config import configure_db_settings, db_settings
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)
from src.repositories.water_heater_repository import MockWaterHeaterRepository

# Import the service class
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


# Monkey patch the repository selection logic
def force_postgres_repository():
    """Force ConfigurableWaterHeaterService to use PostgreSQL repository."""
    # Store original __init__ method
    original_init = ConfigurableWaterHeaterService.__init__

    # Define new __init__ method that always uses PostgreSQL
    def new_init(self, repository=None):
        logger.info("Forcing PostgreSQL repository")

        # If repository is explicitly provided, only allow PostgreSQL
        if repository:
            if not isinstance(repository, PostgresWaterHeaterRepository):
                logger.warning(
                    f"Ignoring provided non-PostgreSQL repository: {type(repository).__name__}"
                )
                repository = None

        # Force PostgreSQL
        host = db_settings.DB_HOST
        port = db_settings.DB_PORT
        database = db_settings.DB_NAME
        user = db_settings.DB_USER
        password = db_settings.DB_PASSWORD

        logger.info(
            f"Using PostgreSQL repository ONLY for water heaters\n"
            f"  Host: {host}:{port}\n"
            f"  Database: {database}\n"
            f"  User: {user}"
        )

        # Attempt PostgreSQL connection
        try:
            self.repository = PostgresWaterHeaterRepository(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            ConfigurableWaterHeaterService.is_using_mock_data = False
            ConfigurableWaterHeaterService.data_source_reason = (
                "Forced to use PostgreSQL database only"
            )
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as pg_error:
            logger.error(f"PostgreSQL connection error: {pg_error}")
            logger.error("PostgreSQL is required - no fallback to mock data allowed")
            raise

    # Replace the __init__ method
    ConfigurableWaterHeaterService.__init__ = new_init
    logger.info("ConfigurableWaterHeaterService patched to use PostgreSQL only")

    # Return original method for restoration
    return original_init


def disable_mock_repository():
    """Disable the MockWaterHeaterRepository."""
    original_methods = {}

    # For each method in the MockWaterHeaterRepository
    for method_name, method in inspect.getmembers(
        MockWaterHeaterRepository, predicate=inspect.isfunction
    ):
        if method_name.startswith("_"):
            continue

        # Store original method
        original_methods[method_name] = getattr(MockWaterHeaterRepository, method_name)

        # Create replacement that raises an exception
        def create_disabled_method(name):
            async def disabled_method(*args, **kwargs):
                raise RuntimeError(
                    f"MockWaterHeaterRepository.{name} is disabled - use PostgreSQL only"
                )

            return disabled_method

        # Replace the method
        setattr(
            MockWaterHeaterRepository, method_name, create_disabled_method(method_name)
        )

    logger.info("MockWaterHeaterRepository methods disabled")
    return original_methods


def override_db_settings():
    """Override database settings to force PostgreSQL."""
    # Store original values
    original_settings = {
        "DB_TYPE": db_settings.DB_TYPE,
        "FALLBACK_TO_MOCK": db_settings.FALLBACK_TO_MOCK,
        "SUPPRESS_DB_CONNECTION_ERRORS": db_settings.SUPPRESS_DB_CONNECTION_ERRORS,
    }

    # Force PostgreSQL settings
    db_settings.DB_TYPE = "postgres"
    db_settings.FALLBACK_TO_MOCK = False
    db_settings.SUPPRESS_DB_CONNECTION_ERRORS = False
    logger.info("Database settings overridden to force PostgreSQL")

    return original_settings


async def test_postgres_connection():
    """Test PostgreSQL connection directly."""
    try:
        # Create PostgreSQL repository
        repo = PostgresWaterHeaterRepository(
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME,
            user=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
        )

        # Initialize the repository
        await repo._initialize()

        # Get all water heaters
        water_heaters = await repo.get_water_heaters()

        # Count Rheem water heaters
        rheem_heaters = [wh for wh in water_heaters if wh.manufacturer == "Rheem"]
        logger.info(
            f"Found {len(water_heaters)} total water heaters, {len(rheem_heaters)} Rheem heaters"
        )

        # Verify types
        types = {}
        for wh in rheem_heaters:
            wh_type = str(wh.water_heater_type)
            if wh_type not in types:
                types[wh_type] = 0
            types[wh_type] += 1

        for wh_type, count in types.items():
            logger.info(f"  - Type: {wh_type}, Count: {count}")

        # Close connection pool
        if repo.pool:
            await repo.pool.close()

        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection test failed: {e}")
        return False


async def apply_overrides():
    """Apply all overrides."""
    # Force environment variables
    os.environ["IOTSPHERE_ENV"] = "development"
    os.environ["USE_MOCK_DATA"] = "false"
    os.environ["DB_TYPE"] = "postgres"
    logger.info("Environment variables set")

    # Override database settings
    original_settings = override_db_settings()

    # Test PostgreSQL connection
    connection_ok = await test_postgres_connection()
    if not connection_ok:
        logger.error("Direct PostgreSQL connection failed - cannot continue")
        return False

    # Modify service to use PostgreSQL only
    original_init = force_postgres_repository()

    # Disable mock repository
    original_mock_methods = disable_mock_repository()

    logger.info("All overrides applied successfully")
    return True


async def main():
    """Apply overrides and run the verification."""
    logger.info("Starting PostgreSQL-only configuration")

    # Apply overrides
    success = await apply_overrides()
    if not success:
        logger.error("Failed to apply overrides")
        return 1

    # Run the verification script in the modified environment
    logger.info("\nRunning verification with PostgreSQL-only configuration")
    try:
        # Import and run the verification function
        from verify_postgres_data_flow import (
            verify_postgres_data_to_api_consistency,
            verify_ui_displays_postgres_data,
        )

        # Verify API data
        logger.info("\n--- Verifying PostgreSQL to API Data Flow ---")
        api_success = await verify_postgres_data_to_api_consistency()

        # Verify UI data
        logger.info("\n--- Verifying PostgreSQL Data in UI ---")
        ui_success = verify_ui_displays_postgres_data()

        # Overall check
        logger.info("\n--- Overall Results ---")
        if api_success:
            logger.info("✅ API correctly returns PostgreSQL water heaters")
        else:
            logger.error("❌ API does not correctly return PostgreSQL water heaters")

        if ui_success:
            logger.info("✅ UI displays Rheem water heaters from PostgreSQL")
        else:
            logger.error("❌ UI does not display Rheem water heaters from PostgreSQL")

        if api_success and ui_success:
            logger.info(
                "\n✅ All requirements met when using PostgreSQL-only configuration"
            )
        else:
            logger.error(
                "\n❌ Some requirements failed even with PostgreSQL-only configuration"
            )

        return 0 if api_success and ui_success else 1

    except Exception as e:
        logger.error(f"Error running verification: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
