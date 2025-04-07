#!/usr/bin/env python3
"""
Test direct connection to PostgreSQL and verify water heater data.

This script bypasses the application's configuration system and directly
connects to PostgreSQL to check if the data matches what should be displayed
in the UI.
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

import asyncpg

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
db_credentials = get_db_credentials()
DB_HOST = db_credentials["host"]
DB_PORT = db_credentials["port"]
DB_NAME = db_credentials["database"]
DB_USER = db_credentials["user"]
DB_PASSWORD = db_credentials["password"]


async def connect_to_postgres():
    """Directly connect to PostgreSQL and return the connection."""
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        logger.info("✅ Successfully connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {str(e)}")
        return None


async def check_water_heaters_table(conn):
    """Check if the water_heaters table exists and has data."""
    try:
        # Check if table exists
        table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'water_heaters'
        );
        """
        table_exists = await conn.fetchval(table_query)

        if not table_exists:
            logger.error("❌ water_heaters table does not exist in the database")
            return False, {}

        logger.info("✅ water_heaters table exists")

        # Get column information
        columns_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'water_heaters';
        """
        columns = await conn.fetch(columns_query)

        # Check if important columns exist
        column_names = [col["column_name"] for col in columns]
        required_columns = ["id", "device_id", "manufacturer", "water_heater_type"]
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            logger.error(f"❌ Missing required columns: {missing_columns}")
            return False, {"columns": column_names}

        logger.info(f"✅ All required columns present: {required_columns}")

        # Get water heater count
        count_query = "SELECT COUNT(*) FROM water_heaters;"
        count = await conn.fetchval(count_query)

        if count == 0:
            logger.error("❌ water_heaters table is empty")
            return False, {"count": 0, "columns": column_names}

        logger.info(f"✅ Found {count} water heaters in the database")

        # Get manufacturer distribution
        manufacturer_query = """
        SELECT manufacturer, COUNT(*)
        FROM water_heaters
        GROUP BY manufacturer;
        """
        manufacturers = await conn.fetch(manufacturer_query)
        manufacturer_counts = {
            row["manufacturer"]: row["count"] for row in manufacturers
        }

        # Get water heater type distribution
        type_query = """
        SELECT water_heater_type, COUNT(*)
        FROM water_heaters
        GROUP BY water_heater_type;
        """
        types = await conn.fetch(type_query)
        type_counts = {row["water_heater_type"]: row["count"] for row in types}

        # Get specific Rheem water heaters
        rheem_query = """
        SELECT id, device_id, manufacturer, water_heater_type, model, series
        FROM water_heaters
        WHERE manufacturer = 'Rheem'
        LIMIT 10;
        """
        rheem_water_heaters = await conn.fetch(rheem_query)
        rheem_data = [dict(row) for row in rheem_water_heaters]

        return True, {
            "count": count,
            "columns": column_names,
            "manufacturers": manufacturer_counts,
            "water_heater_types": type_counts,
            "rheem_sample": rheem_data,
        }
    except Exception as e:
        logger.error(f"❌ Error checking water_heaters table: {str(e)}")
        return False, {"error": str(e)}


async def check_rheem_water_heater_types(conn):
    """Check if all Rheem water heater types are present."""
    try:
        query = """
        SELECT water_heater_type, COUNT(*)
        FROM water_heaters
        WHERE manufacturer = 'Rheem'
        GROUP BY water_heater_type;
        """
        result = await conn.fetch(query)

        type_counts = {row["water_heater_type"]: row["count"] for row in result}
        required_types = ["Tank", "Tankless", "Hybrid"]
        missing_types = [
            wh_type for wh_type in required_types if wh_type not in type_counts
        ]

        if missing_types:
            logger.error(f"❌ Missing Rheem water heater types: {missing_types}")
            return False, type_counts

        # Check if we have at least 2 of each type
        insufficient_types = [
            wh_type
            for wh_type, count in type_counts.items()
            if wh_type in required_types and count < 2
        ]

        if insufficient_types:
            logger.warning(
                f"⚠️ Some Rheem water heater types have fewer than 2 items: {insufficient_types}"
            )

        logger.info(f"✅ All Rheem water heater types present: {type_counts}")
        return True, type_counts
    except Exception as e:
        logger.error(f"❌ Error checking Rheem water heater types: {str(e)}")
        return False, {"error": str(e)}


async def test_api_endpoints():
    """Test the API endpoints and compare with database data."""
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            # Test the brand-agnostic manufacturer endpoint
            logger.info("Testing manufacturer-agnostic API endpoint...")
            async with session.get(
                "http://localhost:8006/api/manufacturer/water-heaters?manufacturer=Rheem"
            ) as response:
                if response.status == 200:
                    api_data = await response.json()
                    api_count = len(api_data)
                    logger.info(f"✅ API returned {api_count} Rheem water heaters")

                    # Check for water heater types in the API response
                    api_types = {}
                    for wh in api_data:
                        wh_type = wh.get("water_heater_type")
                        api_types[wh_type] = api_types.get(wh_type, 0) + 1

                    logger.info(f"Water heater types from API: {api_types}")
                    return True, {
                        "count": api_count,
                        "types": api_types,
                        "sample": api_data[:2],
                    }
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ API request failed with status {response.status}: {error_text}"
                    )
                    return False, {"status": response.status, "error": error_text}
    except Exception as e:
        logger.error(f"❌ Error testing API endpoints: {str(e)}")
        return False, {"error": str(e)}

    return False, {"error": "Unknown error in API test"}


async def main():
    """Run all tests and generate a report."""
    logger.info("Starting PostgreSQL connection and data verification...")

    # Connect to PostgreSQL
    conn = await connect_to_postgres()
    if not conn:
        logger.error("Cannot proceed with tests due to connection failure")
        return 1

    try:
        # Run tests
        table_success, table_data = await check_water_heaters_table(conn)
        types_success, types_data = await check_rheem_water_heater_types(conn)

        # Test API endpoints
        try:
            api_success, api_data = await test_api_endpoints()
        except Exception as e:
            logger.error(f"API endpoint test failed: {str(e)}")
            api_success = False
            api_data = {"error": str(e)}

        # Generate report
        report = {
            "postgresql_connection": True,
            "water_heaters_table": {"success": table_success, "data": table_data},
            "rheem_water_heater_types": {"success": types_success, "data": types_data},
            "api_endpoint_test": {"success": api_success, "data": api_data},
        }

        # Print summary
        logger.info("\n===== POSTGRESQL DATA VERIFICATION SUMMARY =====")
        logger.info(f"PostgreSQL Connection: {'✅ CONNECTED' if conn else '❌ FAILED'}")
        logger.info(
            f"Water Heaters Table Check: {'✅ PASSED' if table_success else '❌ FAILED'}"
        )
        logger.info(
            f"Rheem Water Heater Types Check: {'✅ PASSED' if types_success else '❌ FAILED'}"
        )
        logger.info(f"API Endpoint Test: {'✅ PASSED' if api_success else '❌ FAILED'}")

        # Check for data match between API and database
        if api_success and types_success:
            api_types = api_data.get("types", {})
            db_types = types_data

            # Convert types to comparable format
            normalized_api_types = {k.upper(): v for k, v in api_types.items()}
            normalized_db_types = {k.upper(): v for k, v in db_types.items()}

            types_match = all(
                normalized_api_types.get(t) == normalized_db_types.get(t)
                for t in set(normalized_api_types) | set(normalized_db_types)
            )

            if types_match:
                logger.info("✅ API data matches database data!")
            else:
                logger.warning("⚠️ Discrepancy between API data and database data")
                logger.warning(f"API types: {api_types}")
                logger.warning(f"DB types:  {db_types}")

        # Save report to file
        report_path = os.path.join(
            os.path.dirname(__file__), "postgresql_data_verification.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\nDetailed report saved to: {report_path}")

        return 0
    finally:
        # Close the connection
        if conn:
            await conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
