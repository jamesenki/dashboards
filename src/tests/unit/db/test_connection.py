import importlib
from unittest.mock import MagicMock, patch

import pytest

from src.db.config import db_settings
from src.db.connection import get_db_session, get_engine, get_session_factory


class TestDBConnection:
    """Test database connection with fallbacks."""

    @pytest.mark.asyncio
    @patch("src.db.connection.HAS_GREENLET", False)
    async def test_get_engine_without_greenlet(self):
        """Test that engine returns None when greenlet is not available."""
        # Reset the engine for testing
        import src.db.connection

        src.db.connection.engine = None

        # Get engine when greenlet is not available
        engine = get_engine()

        # Engine should be None, DB_TYPE should be memory
        assert engine is None
        assert db_settings.DB_TYPE == "memory"

    @pytest.mark.asyncio
    @patch("src.db.connection.HAS_GREENLET", True)
    @patch("src.db.connection.create_async_engine")
    async def test_get_engine_with_exception(self, mock_create_engine):
        """Test engine creation with exception handling."""
        # Reset the engine for testing
        import src.db.connection

        src.db.connection.engine = None

        # Setup mock to raise an exception
        mock_create_engine.side_effect = Exception("Test engine creation failure")

        # Get engine
        engine = get_engine()

        # Engine should be None, we should have attempted to fallback to memory
        assert engine is None
        assert db_settings.DB_TYPE == "memory"
        assert mock_create_engine.call_count == 2  # Called twice (original + fallback)

    @pytest.mark.asyncio
    @patch("src.db.connection.HAS_GREENLET", True)
    @patch("src.db.connection.get_engine")
    async def test_get_session_factory_with_null_engine(self, mock_get_engine):
        """Test session factory with null engine."""
        # Setup mock to return None
        mock_get_engine.return_value = None

        # Reset the session factory for testing
        import src.db.connection

        src.db.connection.async_session_factory = None

        # Get session factory
        factory = get_session_factory()

        # Factory should be None
        assert factory is None

    @pytest.mark.asyncio
    @patch("src.db.connection.HAS_GREENLET", False)
    async def test_get_db_session_without_greenlet(self):
        """Test db session generator without greenlet."""
        # Use aiter to collect generator values
        sessions = []
        async for session in get_db_session():
            sessions.append(session)

        # Should yield None exactly once
        assert len(sessions) == 1
        assert sessions[0] is None

    @pytest.mark.asyncio
    @patch("src.db.connection.HAS_GREENLET", True)
    @patch("src.db.connection.get_session_factory")
    async def test_get_db_session_with_null_factory(self, mock_get_factory):
        """Test db session generator with null factory."""
        # Setup mock to return None
        mock_get_factory.return_value = None

        # Use aiter to collect generator values
        sessions = []
        async for session in get_db_session():
            sessions.append(session)

        # Should yield None exactly once
        assert len(sessions) == 1
        assert sessions[0] is None
