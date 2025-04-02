import importlib.util
import logging
import sys
from typing import Any, AsyncGenerator, Dict, Optional, Union

from sqlalchemy import NullPool, text

# Check if required packages are available
HAS_GREENLET = importlib.util.find_spec("greenlet") is not None
HAS_ASYNCPG = importlib.util.find_spec("asyncpg") is not None
HAS_AIOSQLITE = importlib.util.find_spec("aiosqlite") is not None

# Only import these if greenlet is available to avoid errors
if HAS_GREENLET:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
else:
    # Create dummy classes for type hints when greenlet is not available
    class AsyncEngine:
        pass

    class AsyncSession:
        pass

    class async_sessionmaker:
        pass

    create_async_engine = None

from src.db.config import db_settings, get_db_url

logger = logging.getLogger(__name__)

# Global engine variable
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> Optional[AsyncEngine]:
    """Get or create SQLAlchemy engine with proper error handling."""
    global engine

    if engine is None:
        # Check if required dependencies are installed
        if not HAS_GREENLET:
            logger.error(
                "The greenlet library is required for async database operations. Using in-memory fallback."
            )
            # Force memory mode when greenlet is not available
            db_settings.DB_TYPE = "memory"
            return None

        # Handle specific database types and their dependencies
        if db_settings.DB_TYPE == "postgres" and not HAS_ASYNCPG:
            logger.error(
                "The asyncpg library is required for PostgreSQL. Falling back to SQLite."
            )
            db_settings.DB_TYPE = "sqlite"

        if db_settings.DB_TYPE == "sqlite" and not HAS_AIOSQLITE:
            logger.error(
                "The aiosqlite library is required for SQLite. Using in-memory fallback."
            )
            db_settings.DB_TYPE = "memory"

        try:
            url = get_db_url()
            if db_settings.DB_TYPE == "memory":
                # Use NullPool for in-memory SQLite to avoid thread issues
                engine = create_async_engine(url, poolclass=NullPool, echo=False)
            else:
                engine = create_async_engine(
                    url,
                    pool_size=db_settings.DB_POOL_SIZE,
                    max_overflow=db_settings.DB_MAX_OVERFLOW,
                    echo=False,
                )
            logger.info(f"Created database engine for {db_settings.DB_TYPE}")
        except Exception as e:
            logger.error(
                f"Failed to create database engine: {str(e)}. Using in-memory fallback."
            )
            db_settings.DB_TYPE = "memory"
            try:
                url = get_db_url()
                engine = create_async_engine(url, poolclass=NullPool, echo=False)
            except Exception as inner_e:
                logger.critical(f"Critical database error: {str(inner_e)}")
                return None

    return engine


def get_session_factory() -> Optional[async_sessionmaker]:
    """Get or create AsyncSession factory with proper error handling."""
    global async_session_factory

    if async_session_factory is None:
        if not HAS_GREENLET:
            logger.error("Cannot create session factory: greenlet library is missing.")
            return None

        try:
            engine = get_engine()
            if engine is None:
                logger.error(
                    "Cannot create session factory: engine initialization failed."
                )
                return None

            async_session_factory = async_sessionmaker(
                engine, expire_on_commit=False, class_=AsyncSession
            )
        except Exception as e:
            logger.error(f"Failed to create session factory: {str(e)}")
            return None

    return async_session_factory


async def get_db_session() -> AsyncGenerator[Union[AsyncSession, None], None]:
    """Dependency for getting DB session with graceful fallback."""
    if not HAS_GREENLET:
        logger.warning("Database session unavailable: greenlet library is missing.")
        yield None
        return

    session_factory = get_session_factory()
    if session_factory is None:
        logger.warning(
            "Database session unavailable: session factory initialization failed."
        )
        yield None
        return

    try:
        session = session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {str(rollback_error)}")
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Session close error: {str(close_error)}")
    except Exception as outer_e:
        logger.error(f"Failed to create database session: {str(outer_e)}")
        yield None
