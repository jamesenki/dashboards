#!/usr/bin/env python3
"""
Debugging runner for BDD tests with enhanced error tracing.
"""
import logging
import os
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock environment variables for testing
os.environ["TESTING"] = "1"
os.environ["TEST_MODE"] = "BDD"


class TestStepTracer:
    def __init__(self):
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()

    def __enter__(self):
        self.stdout_redirect = redirect_stdout(self.stdout_capture)
        self.stderr_redirect = redirect_stderr(self.stderr_capture)
        self.stdout_redirect.__enter__()
        self.stderr_redirect.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stdout_redirect.__exit__(exc_type, exc_val, exc_tb)
        self.stderr_redirect.__exit__(exc_type, exc_val, exc_tb)

        # Log captured output
        if self.stdout_capture.getvalue():
            logger.debug(f"STDOUT: {self.stdout_capture.getvalue()}")
        if self.stderr_capture.getvalue():
            logger.debug(f"STDERR: {self.stderr_capture.getvalue()}")

        # If exception occurred, provide detailed traceback
        if exc_type:
            logger.error(
                f"Exception during step execution: {exc_type.__name__}: {exc_val}"
            )
            logger.error(f"Traceback: {''.join(traceback.format_tb(exc_tb))}")
            return False  # Don't suppress exception
        return True


def run_test_with_tracing():
    """Run BDD test with step-by-step tracing."""
    try:
        # Import BDD steps
        # Import behave context
        from behave.runner import Context
        from fastapi.testclient import TestClient
        from steps.dashboard_steps import (
            step_logged_in_as_role,
            step_navigate_to_dashboard,
            step_see_water_heater_list,
            step_water_heaters_show_connection_status,
            step_water_heaters_show_simulated_status,
        )

        from src.main import app

        # Create a test context
        context = Context()
        context.app = app
        context.client = TestClient(app)

        # Run each step with explicit tracing
        logger.info("=== Starting BDD Test Execution with Tracing ===")

        with TestStepTracer() as tracer:
            logger.info("Step 1: I am logged in as a 'facility_manager'")
            step_logged_in_as_role(context, "facility_manager")

        with TestStepTracer() as tracer:
            logger.info("Step 2: I navigate to the water heater dashboard")
            step_navigate_to_dashboard(context)

        with TestStepTracer() as tracer:
            logger.info(
                "Step 3: I should see a list of all water heaters in the system"
            )
            step_see_water_heater_list(context)

        with TestStepTracer() as tracer:
            logger.info(
                "Step 4: Each water heater should display its connection status"
            )
            step_water_heaters_show_connection_status(context)

        with TestStepTracer() as tracer:
            logger.info("Step 5: Each water heater should indicate if it is simulated")
            step_water_heaters_show_simulated_status(context)

        logger.info("=== All steps completed successfully ===")
        return 0

    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_test_with_tracing())
