"""
Test helpers for IoTSphere tests.

This module provides helper functions and fixtures for testing the IoTSphere application.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.services.service_locator import get_service as original_get_service
from src.services.vending_machine import VendingMachineService
from src.services.water_heater import WaterHeaterService

# Dictionary to hold mock services for testing
_mock_services = {}


class TestEnvironment:
    """
    Test environment manager for IoTSphere tests.
    Provides methods to set up and tear down the test environment.
    """

    def __init__(self):
        # Create mock services
        self.mock_vending_machine_service = MagicMock(spec=VendingMachineService)
        self.mock_water_heater_service = MagicMock(spec=WaterHeaterService)

        # Store mock services in a dictionary for easy access
        self.services = {
            VendingMachineService.__name__: self.mock_vending_machine_service,
            WaterHeaterService.__name__: self.mock_water_heater_service,
        }

        # The patches that will be applied
        self.patches = []

    def mock_get_service(self, service_class):
        """Mock implementation of get_service"""
        service_name = service_class.__name__
        if service_name in self.services:
            return self.services[service_name]
        return MagicMock(spec=service_class)

    def setup(self):
        """
        Set up the test environment by patching the necessary services.
        This should be called before running tests.
        """
        # Create patch for service_locator.get_service
        patcher = patch(
            "src.services.service_locator.get_service",
            side_effect=self.mock_get_service,
        )
        self.patches.append(patcher)

        # Start all patches
        for p in self.patches:
            p.start()

        # Reload API modules to ensure they use the patched services
        self._reload_api_modules()

        return self

    def _reload_api_modules(self):
        """Reload API modules to ensure they use the patched services"""
        # Import and reload API modules to ensure they use our patched services
        try:
            import src.api.vending_machine
            import src.api.water_heater

            importlib.reload(src.api.vending_machine)
            importlib.reload(src.api.water_heater)
        except ImportError as e:
            print(f"Warning: Could not reload some API modules: {e}")

    def teardown(self):
        """
        Tear down the test environment by stopping all patches.
        This should be called after running tests.
        """
        for p in reversed(self.patches):
            p.stop()
        self.patches.clear()

    def __enter__(self):
        return self.setup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()


def get_mock_service(service_class):
    """
    Get a specific mock service for testing.
    This must be called after setting up the test environment.
    """
    env = pytest.current_test.env if hasattr(pytest, "current_test") else None
    if env and hasattr(env, "services"):
        service_name = service_class.__name__
        if service_name in env.services:
            return env.services[service_name]
    return None


@pytest.fixture
def test_env():
    """
    Pytest fixture to provide a test environment with mocked services.

    Example:
        def test_something(test_env):
            # Configure mocks
            test_env.mock_vending_machine_service.get_all_vending_machines.return_value = [...]

            # Run test
            ...
    """
    env = TestEnvironment()

    # Set up the environment and make it available to helper functions
    with env:
        # Attach to pytest for access within helper functions
        pytest.current_test = type("obj", (object,), {"env": env})

        yield env

    # Clean up
    if hasattr(pytest, "current_test"):
        delattr(pytest, "current_test")


@pytest.fixture
def test_client(test_env):
    """
    Pytest fixture to provide a configured TestClient with mocked services.

    This fixture depends on the test_env fixture to ensure services are properly mocked.

    Example:
        def test_api_endpoint(test_client, test_env):
            # Configure mocks
            test_env.mock_vending_machine_service.get_vending_machine.return_value = ...

            # Make request
            response = test_client.get("/api/vending-machines/123")
            ...
    """
    from src.main import app

    client = TestClient(app)
    return client
