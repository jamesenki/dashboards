#!/usr/bin/env python3
"""
Verify that PostgreSQL is being used as the data source.

This script:
1. Checks the application's configuration
2. Provides logs about which data source is being used
3. Creates a report summarizing the findings
"""
import asyncio
import datetime
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.db.config import db_settings
from src.repositories.mock_water_heater_repository import MockWaterHeaterRepository
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_database_connection():
    """Test the database connection and return information about it."""
    logger.info("Testing PostgreSQL database connection...")

    try:
        # Try to create a PostgreSQL repository
        repo = PostgresWaterHeaterRepository(
            db_host=db_settings.DB_HOST,
            db_port=db_settings.DB_PORT,
            db_name=db_settings.DB_NAME,
            db_user=db_settings.DB_USER,
            db_password=db_settings.DB_PASSWORD,
        )

        # Try to connect and get water heaters
        await repo.initialize()
        water_heaters = await repo.get_water_heaters()

        return {
            "connection_success": True,
            "water_heater_count": len(water_heaters),
            "connection_details": {
                "host": db_settings.DB_HOST,
                "port": db_settings.DB_PORT,
                "database": db_settings.DB_NAME,
                "user": db_settings.DB_USER,
            },
        }
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "connection_success": False,
            "error": str(e),
            "connection_details": {
                "host": db_settings.DB_HOST,
                "port": db_settings.DB_PORT,
                "database": db_settings.DB_NAME,
                "user": db_settings.DB_USER,
            },
        }


async def check_configurable_service():
    """Check which repository is being used by the configurable service."""
    logger.info("Checking ConfigurableWaterHeaterService configuration...")

    try:
        service = ConfigurableWaterHeaterService()

        # Get information about which repository is being used
        mock_data_config = ConfigurableWaterHeaterService.is_using_mock_data
        reason = ConfigurableWaterHeaterService.data_source_reason

        # Check the actual repository instance type
        repo_type = type(service.repository).__name__

        return {
            "is_using_mock_data": mock_data_config,
            "repository_type": repo_type,
            "reason": reason,
        }
    except Exception as e:
        logger.error(f"ConfigurableWaterHeaterService error: {str(e)}")
        return {"error": str(e)}


async def check_environment_settings():
    """Check environment settings that affect data source selection."""
    logger.info("Checking environment settings...")

    env_settings = {
        "IOTSPHERE_ENV": os.environ.get("IOTSPHERE_ENV", "Not set"),
        "USE_MOCK_DATA": os.environ.get("USE_MOCK_DATA", "Not set"),
        "FALLBACK_TO_MOCK": os.environ.get("FALLBACK_TO_MOCK", "Not set"),
        "DB_TYPE": os.environ.get("DB_TYPE", "Not set"),
        "DB_HOST": os.environ.get("DB_HOST", "Not set"),
        "DB_PORT": os.environ.get("DB_PORT", "Not set"),
        "DB_NAME": os.environ.get("DB_NAME", "Not set"),
        "DB_USER": os.environ.get("DB_USER", "Not set"),
    }

    # Check DB settings from the application configuration
    db_config = {
        "DB_TYPE": db_settings.DB_TYPE,
        "DB_HOST": db_settings.DB_HOST,
        "DB_PORT": db_settings.DB_PORT,
        "DB_NAME": db_settings.DB_NAME,
        "DB_USER": db_settings.DB_USER,
        "FALLBACK_TO_MOCK": db_settings.FALLBACK_TO_MOCK,
    }

    return {"environment_variables": env_settings, "application_db_settings": db_config}


async def main():
    """Run verification checks and generate a report."""
    logger.info("Starting PostgreSQL usage verification...")

    # Run all checks
    env_check = await check_environment_settings()
    db_check = await check_database_connection()
    service_check = await check_configurable_service()

    # Generate report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "environment_settings": env_check,
        "database_connection": db_check,
        "service_configuration": service_check,
        "summary": {
            "is_postgresql_working": db_check.get("connection_success", False),
            "is_using_postgresql": service_check.get("repository_type")
            == "PostgresWaterHeaterRepository",
            "is_using_mock_data": service_check.get("is_using_mock_data", True),
            "reason": service_check.get("reason", "Unknown"),
        },
    }

    # Print report summary
    logger.info("\n===== PostgreSQL USAGE VERIFICATION SUMMARY =====")
    logger.info(
        f"PostgreSQL Connection: {'✅ WORKING' if report['summary']['is_postgresql_working'] else '❌ FAILED'}"
    )
    logger.info(
        f"Using PostgreSQL Repository: {'✅ YES' if report['summary']['is_using_postgresql'] else '❌ NO'}"
    )
    logger.info(
        f"Using Mock Data: {'❌ YES' if report['summary']['is_using_mock_data'] else '✅ NO'}"
    )
    logger.info(f"Reason: {report['summary']['reason']}")

    # Recommendations
    logger.info("\n===== RECOMMENDATIONS =====")
    if not report["summary"]["is_postgresql_working"]:
        logger.info(
            "❗ PostgreSQL connection failed. Check your PostgreSQL server and connection settings."
        )

    if report["summary"]["is_using_mock_data"]:
        logger.info("❗ The application is using mock data instead of PostgreSQL.")
        logger.info("  - Check environment variables and application settings.")
        logger.info(
            "  - Try setting FALLBACK_TO_MOCK=false in the environment or .env file."
        )
        logger.info("  - Verify that PostgreSQL is correctly configured and working.")

    # Save report to file
    report_path = os.path.join(
        os.path.dirname(__file__), "postgresql_verification_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nDetailed report saved to: {report_path}")

    return 0


if __name__ == "__main__":
    asyncio.run(main())
