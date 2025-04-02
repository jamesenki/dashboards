# In src/tests/conftest.py
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Add pytest fixtures for API testing
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.main import app

# Disable warnings about asyncio mode
pytest.register_assert_rewrite("pytest_asyncio.plugin")

@pytest.fixture
def test_client():
    """Fixture for creating a FastAPI TestClient"""
    return TestClient(app)

@pytest.fixture
def mock_service_locator():
    """Fixture for mocking the service locator"""
    with patch('src.services.service_locator.get_service') as mock_get:
        yield mock_get

# Provide event loop for async tests
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()