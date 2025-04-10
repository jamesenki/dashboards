"""
Behave environment setup for BDD tests.
This file configures the test environment, handles setup and teardown.
"""
import logging
import os
import sys
from unittest.mock import patch

# Add project root to Python path to make 'src' module importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our application
from fastapi.testclient import TestClient

from src.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def before_all(context):
    """
    Setup that runs before all tests.
    """
    logger.info("Setting up BDD test environment")

    # Store the app in the context
    context.app = app

    # Create a test client
    context.client = TestClient(app)

    # Set test mode flag to ensure we don't hit real databases/services
    os.environ["TESTING"] = "1"
    os.environ["TEST_MODE"] = "BDD"

    # Register custom path for step definitions
    # This ensures behave can find our Python step definitions
    steps_dir = os.path.join(os.path.dirname(__file__), "steps")
    sys.path.insert(0, steps_dir)

    # Enable discovery of Python step modules
    # We need to explicitly import step definition files in the step registry
    steps_dir = os.path.join(os.path.dirname(__file__), "steps")
    # Load all Python modules in the steps directory
    for module_file in os.listdir(steps_dir):
        if module_file.endswith(".py") and not module_file.startswith("__"):
            module_name = module_file[:-3]  # Remove .py extension
            try:
                # Use importlib to dynamically import the module
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    module_name, os.path.join(steps_dir, module_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.info(f"Loaded step definition module: {module_name}")
            except Exception as e:
                logger.error(f"Error importing step module {module_name}: {e}")

    logger.info("BDD test environment setup complete")


def after_all(context):
    """
    Teardown that runs after all tests.
    """
    logger.info("Tearing down BDD test environment")

    # Clean up test environment variables
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]

    logger.info("BDD test environment teardown complete")


def before_feature(context, feature):
    """
    Setup that runs before each feature.
    """
    logger.info(f"Setting up feature: {feature.name}")

    # Store patchers list for cleanup
    context.patchers = []

    # Reset all mocked data
    context.mock_data = {}

    # Check for API-specific features
    if "api" in feature.tags:
        logger.info("Setting up API test environment")


def after_feature(context, feature):
    """
    Teardown that runs after each feature.
    """
    logger.info(f"Tearing down feature: {feature.name}")

    # Stop all patchers
    for patcher in context.patchers:
        patcher.stop()

    # Clear the context
    context.mock_data = {}


def before_scenario(context, scenario):
    """
    Setup that runs before each scenario.
    """
    logger.info(f"Setting up scenario: {scenario.name}")

    # Reset scenario-specific data
    context.response = None
    context.response_data = None
    context.websocket = None
    context.ws_messages = []

    # Apply specific patches based on scenario tags
    if "websocket" in scenario.tags:
        # Setup WebSocket specific mocks
        logger.info("Setting up WebSocket test environment")

    # Store the scenario for reference
    context.scenario = scenario


def after_scenario(context, scenario):
    """
    Teardown that runs after each scenario.
    """
    logger.info(f"Tearing down scenario: {scenario.name}")

    # Close any open WebSocket connections
    if hasattr(context, "websocket") and context.websocket:
        # Clean up websocket if needed
        pass

    # Reset any scenario-specific data
    context.response = None
    context.response_data = None
