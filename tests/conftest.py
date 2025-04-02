"""
pytest configuration file to set up test environment.
"""
import os
import sys

import pytest

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for testing
os.environ["USE_MOCK_DATA"] = "True"
os.environ["TESTING"] = "True"


@pytest.fixture
def test_db_path():
    """Provide an in-memory database path for tests."""
    return ":memory:"
