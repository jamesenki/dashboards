#!/usr/bin/env python3
"""
Custom BDD test runner with enhanced debugging.
This script provides more detailed error output when BDD tests fail.
"""
import logging
import os
import sys

from behave.__main__ import main as behave_main

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set environment variables for testing
os.environ["TESTING"] = "1"
os.environ["TEST_MODE"] = "BDD"

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def run_tests():
    """Run the BDD tests with enhanced error reporting."""
    logger.info("Starting BDD tests with enhanced debugging")

    # Configure command-line arguments for behave
    # Use the correct absolute path to the feature file
    # Use the correct path we found
    feature_path = os.path.join(
        current_dir, "features", "dashboard", "water_heater_dashboard.feature"
    )
    logger.debug(f"Using feature path: {feature_path}")

    # Verify the feature file exists
    if not os.path.exists(feature_path):
        logger.error(f"Feature file not found: {feature_path}")
        # Attempt to locate the feature file
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file == "water_heater_dashboard.feature":
                    logger.info(f"Found feature file at: {os.path.join(root, file)}")
        return 1

    args = [
        feature_path,
        "--no-capture",
        "--no-skipped",
        "--format=pretty",
        "--logging-level=DEBUG",
    ]

    # Run behave tests
    try:
        result = behave_main(args)
        return result
    except Exception as e:
        logger.error(f"Error running BDD tests: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
