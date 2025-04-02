#!/usr/bin/env python3
"""
Test runner for automated training tests.

This script runs the tests for the automated training functionality,
following TDD principles to verify that tests fail before implementation.
"""
import os
import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(src_dir.absolute()))


def main():
    """Run the automated training tests."""
    print("Running tests for automated training functionality...")

    # Path to the test file
    test_file = Path(__file__).parent / "test_automated_training.py"

    # Run pytest with verbose output
    args = ["-v", str(test_file)]

    # Add the -k option to run specific test methods if needed
    # args.extend(["-k", "test_schedule_model_training or test_detect_performance_drift"])

    print(f"Test command: pytest {' '.join(args)}")
    result = pytest.main(args)

    # Return exit code based on test results
    return 0 if result == 0 else 1


if __name__ == "__main__":
    # Ensure proper working directory
    os.chdir(Path(__file__).parent)

    # Run tests
    sys.exit(main())
