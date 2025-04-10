"""
Configuration file for pytest/behave integration.

This file provides fixture definitions and test setup for the BDD tests.
Following TDD principles, it sets up the test environment properly before implementation.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add project root to Python path to make modules importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our application
from src.main import app


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="function")
def reset_test_state():
    """Reset the test state between tests for proper isolation."""
    # This will be expanded as the application grows
    yield
    # Any cleanup needed after tests
