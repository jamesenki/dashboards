#!/usr/bin/env python3
"""
Configure the application to use PostgreSQL ONLY with no fallback to mock data.

This script:
1. Creates a special .env file that forces PostgreSQL usage
2. Disables fallback to mock data
3. Runs the application with explicit PostgreSQL configuration
"""
import argparse
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_env_file():
    """Create a .env file forcing PostgreSQL usage."""
    env_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../.env")
    )

    env_content = """# Force PostgreSQL configuration with no fallback
IOTSPHERE_ENV=development
USE_MOCK_DATA=false
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=iotsphere
DB_USER=iotsphere
DB_PASSWORD=iotsphere
FALLBACK_TO_MOCK=false
SUPPRESS_DB_CONNECTION_ERRORS=false
"""

    with open(env_file_path, "w") as f:
        f.write(env_content)

    logger.info(f"Created .env file at {env_file_path}")
    return env_file_path


def main():
    """Create environment configuration and launch application."""
    parser = argparse.ArgumentParser(description="Force PostgreSQL-only configuration")
    parser.add_argument(
        "--port", type=int, default=8006, help="Port to run the server on"
    )
    args = parser.parse_args()

    # Create .env file
    env_file = create_env_file()
    logger.info("PostgreSQL-only environment configured")

    # Recommend how to run the server
    logger.info(
        f"To run the server with PostgreSQL only, use: IOTSPHERE_ENV=development uvicorn src.main:app --port {args.port} --reload"
    )

    # Print verification steps
    logger.info("\nVerification Steps:")
    logger.info("1. Start the server with the command above")
    logger.info("2. Open http://localhost:8006/water-heaters in your browser")
    logger.info("3. Check the data source indicator in the bottom-right corner")
    logger.info("4. Verify that it shows 'PostgreSQL' and not 'Mock'")
    logger.info("5. Check that only water heaters from PostgreSQL appear in the list")

    return 0


if __name__ == "__main__":
    sys.exit(main())
