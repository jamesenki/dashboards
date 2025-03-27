import asyncio
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateTable

from src.db.connection import get_engine
from src.db.models import Base, DeviceModel, ReadingModel, DiagnosticCodeModel

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create all tables if they don't exist."""
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Create tables one by one to handle dependencies
        for table in [DeviceModel.__table__, ReadingModel.__table__, DiagnosticCodeModel.__table__]:
            try:
                await conn.execute(CreateTable(table, if_not_exists=True))
                logger.info(f"Created table {table.name}")
            except Exception as e:
                logger.error(f"Error creating table {table.name}: {e}")
    
    logger.info("Database tables created")


async def configure_timescale() -> None:
    """Configure TimescaleDB for time-series data if using PostgreSQL.
    
    If TimescaleDB is not available, the function will log a warning but continue.
    For production deployments, TimescaleDB is recommended for time-series data,
    but the application can function without it.
    """
    from src.db.config import db_settings
    from sqlalchemy import text
    
    if db_settings.DB_TYPE != "postgres":
        logger.info("Skipping TimescaleDB configuration (not using PostgreSQL)")
        return
    
    try:
        engine = get_engine()
        
        async with engine.begin() as conn:
            # First check if the extension is already installed
            try:
                # Use SQLAlchemy text() for proper SQL query execution
                result = await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'"))
                timescale_exists = result.scalar() is not None
                if timescale_exists:
                    logger.info("TimescaleDB extension is installed and activated")
                    
                    # Only if TimescaleDB is available, try to convert readings table to hypertable
                    try:
                        await conn.execute(text(
                            "SELECT create_hypertable('readings', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE)"
                        ))
                        logger.info("Configured readings table as TimescaleDB hypertable")
                    except Exception as e:
                        logger.warning(f"Cannot convert readings table to TimescaleDB hypertable: {e}")
                        logger.info("Continuing with standard PostgreSQL table instead of TimescaleDB hypertable")
                else:
                    logger.info("TimescaleDB extension is not installed - using standard PostgreSQL tables")
                    logger.info("For time-series performance enhancements, consider installing TimescaleDB:")
                    logger.info("  1. Uninstall current timescaledb: brew uninstall timescaledb")
                    logger.info("  2. Install for PostgreSQL 14: brew install timescaledb --postgresql@14")
                    logger.info("  3. Run timescaledb-tune: /opt/homebrew/bin/timescaledb-tune --quiet --yes")
                    logger.info("  4. Restart PostgreSQL: brew services restart postgresql@14")
                    logger.info("  5. Create extension: psql -U iotsphere iotsphere -c \"CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;\"")
            except Exception as e:
                logger.info("Cannot verify TimescaleDB status - continuing with standard PostgreSQL")
                logger.debug(f"TimescaleDB check error: {e}")
                
    except Exception as e:
        logger.warning(f"Error during TimescaleDB configuration: {e}")
        logger.info("Continuing without TimescaleDB optimization")


async def initialize_db() -> None:
    """Initialize database with tables and extensions."""
    await create_tables()
    await configure_timescale()


if __name__ == "__main__":
    asyncio.run(initialize_db())
