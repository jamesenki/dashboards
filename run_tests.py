#!/usr/bin/env python
"""
Test runner script for IoTSphere water heater application.

This script provides a convenient way to run tests with proper Python path setup
and optional coverage reporting.

Usage:
    python run_tests.py [--coverage] [--unit] [--integration] [--ui]
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def setup_environment():
    """Set up environment variables and Python path."""
    # Add the src directory to Python path
    src_path = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))
    
    # Set environment variable for testing mode
    os.environ['IOTSPHERE_ENV'] = 'test'
    
    print(f"Python path set to include: {src_path}")


def run_tests(coverage=False, unit=True, integration=True, ui=False):
    """Run the tests with optional coverage reporting."""
    setup_environment()
    
    # Apply filters
    test_paths = []
    if unit:
        test_paths.append("src/tests/unit")
    if integration:
        test_paths.append("src/tests/integration")
    if ui:
        test_paths.append("frontend/tests")
    
    # Construct the command using modules instead of direct command line options
    # This helps avoid command-line argument issues
    import pytest
    args = ['-v']
    
    # Add coverage if requested
    if coverage:
        try:
            import pytest_cov
            args.extend(['--cov=src', '--cov-report=term', '--cov-report=html:coverage_report'])
        except ImportError:
            print("Warning: pytest-cov not installed. Run 'pip install pytest-cov' first.")
            print("Continuing without coverage reporting...")
    
    # Add test paths
    args.extend(test_paths)
    
    # Run the tests using pytest's API
    print(f"Running pytest with arguments: {' '.join(args)}")
    return pytest.main(args)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run IoTSphere tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--ui", action="store_true", help="Run UI tests")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all (except UI which needs browser)
    if not (args.unit or args.integration or args.ui):
        args.unit = True
        args.integration = True
    
    return args


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_tests(
        coverage=args.coverage,
        unit=args.unit,
        integration=args.integration,
        ui=args.ui
    ))
