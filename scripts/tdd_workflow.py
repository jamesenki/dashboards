#!/usr/bin/env python
"""
Enhanced TDD Workflow Helper for IoTSphere Development.

This script helps automate the Test-Driven Development workflow with PostgreSQL integration
testing in the IoTSphere project. It follows the Red-Green-Refactor cycle with additional
best practices for test quality, coverage, and maintainability.

Usage:
    python scripts/tdd_workflow.py red <feature_name>     # Create a new failing test for a feature
    python scripts/tdd_workflow.py green <feature_name>   # Run tests to verify implementation
    python scripts/tdd_workflow.py refactor <feature_name> # Verify refactored code still passes tests
    python scripts/tdd_workflow.py cycle <feature_name>    # Run full TDD cycle
    python scripts/tdd_workflow.py ci <feature_name>       # Simulate CI pipeline
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Make sure src is in the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TDD_LOG_FILE = PROJECT_ROOT / "tdd_workflow.log"
TEST_DIR = PROJECT_ROOT / "src" / "tests"
PREDICTION_TEST_DIR = TEST_DIR / "unit" / "predictions"
TEST_DATA_DIR = TEST_DIR / "data"
TEST_MOCK_DIR = TEST_DIR / "mocks"
TEST_CHECKSUM_DIR = TEST_DIR / "checksums"

# Create necessary directories
os.makedirs(PREDICTION_TEST_DIR, exist_ok=True)
os.makedirs(TEST_DATA_DIR, exist_ok=True)
os.makedirs(TEST_MOCK_DIR, exist_ok=True)
os.makedirs(TEST_CHECKSUM_DIR, exist_ok=True)

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials


def log_message(message, level="INFO"):
    """Log a message to console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {level}: {message}"

    print(log_line)
    with open(TDD_LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    log_message(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd or PROJECT_ROOT,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        log_message(
            f"Command failed with exit code {e.returncode}: {e.stderr}", "ERROR"
        )
        return e.stderr


def verify_postgres_running():
    """Verify PostgreSQL is running and accessible."""
    log_message("Verifying PostgreSQL connection...")
    try:
        import psycopg2

        # Get database credentials from environment variables
        db_credentials = get_db_credentials()
        conn = psycopg2.connect(
            dbname=db_credentials["database"],
            user=db_credentials["user"],
            password=db_credentials["password"],
            host=db_credentials["host"],
            port=str(db_credentials["port"]),
        )
        conn.close()
        log_message("PostgreSQL connection successful")
        return True
    except (ImportError, psycopg2.OperationalError) as e:
        log_message(f"PostgreSQL connection failed: {str(e)}", "ERROR")
        log_message(
            "Try starting PostgreSQL with: brew services start postgresql@14", "INFO"
        )
        return False


def check_timescaledb():
    """Check if TimescaleDB extension is available."""
    log_message("Checking TimescaleDB extension...")
    try:
        import psycopg2

        # Get database credentials from environment variables
        db_credentials = get_db_credentials()
        conn = psycopg2.connect(
            dbname=db_credentials["database"],
            user=db_credentials["user"],
            password=db_credentials["password"],
            host=db_credentials["host"],
            port=str(db_credentials["port"]),
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb';")
        result = cursor.fetchone()
        conn.close()

        if result:
            log_message("TimescaleDB extension is installed")
            return True
        else:
            log_message("TimescaleDB extension is not installed", "WARNING")
            log_message(
                "Application will use standard PostgreSQL tables instead", "INFO"
            )
            return False
    except Exception as e:
        log_message(f"TimescaleDB check failed: {str(e)}", "ERROR")
        return False


def check_test_modifications(feature_name):
    """Check if tests have been modified from their original form."""
    snake_case_name = feature_name.replace("-", "_").lower()
    test_file = PREDICTION_TEST_DIR / f"test_{snake_case_name}.py"

    # Check if the test file exists
    if not test_file.exists():
        log_message(f"Test file does not exist: {test_file}", "INFO")
        return True

    # Check if we have a checksum of the original test file
    checksum_file = TEST_CHECKSUM_DIR / f"{snake_case_name}_test.md5"

    if not checksum_file.exists():
        log_message("No original test checksum found - this may be a new test", "INFO")
        return True

    # Calculate current checksum
    with open(test_file, "rb") as f:
        current_md5 = hashlib.md5(f.read()).hexdigest()

    with open(checksum_file, "r") as f:
        original_md5 = f.read().strip()

    if current_md5 != original_md5:
        log_message("WARNING: Tests have been modified since creation", "WARNING")
        log_message(
            "If you're modifying tests, make sure requirements have changed", "WARNING"
        )

        proceed = input("Continue anyway? (y/n): ")
        if proceed.lower() != "y":
            log_message("Aborting due to test modifications", "ERROR")
            return False

    return True


def save_test_checksum(feature_name):
    """Save a checksum of the test file to track modifications."""
    snake_case_name = feature_name.replace("-", "_").lower()
    test_file = PREDICTION_TEST_DIR / f"test_{snake_case_name}.py"

    if not test_file.exists():
        return

    # Calculate MD5 checksum
    with open(test_file, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()

    # Save checksum to file
    checksum_file = TEST_CHECKSUM_DIR / f"{snake_case_name}_test.md5"
    with open(checksum_file, "w") as f:
        f.write(md5)

    log_message(f"Saved test checksum to {checksum_file}")


def generate_test_data(feature_name):
    """Generate standard test data for the feature tests."""
    snake_case_name = feature_name.replace("-", "_").lower()

    # Create test data directory if it doesn't exist
    test_data_dir = TEST_DATA_DIR / snake_case_name
    os.makedirs(test_data_dir, exist_ok=True)

    # Generate test data files with timestamp to track versions
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_file = test_data_dir / f"test_data_{timestamp}.json"

    # Sample test data structure
    test_data = {
        "standard_scenarios": [
            {
                "scenario": "typical_device",
                "device_id": "test-device-001",
                "features": {
                    "installation_date": str(datetime.now() - timedelta(days=365)),
                    "temperature_settings": 60.0,
                    "water_hardness": "moderate",
                    "usage_intensity": "medium",
                },
                "expected_results": {
                    "prediction_value": None,  # To be filled by test author
                    "confidence_min": 0.7,
                },
            },
            {
                "scenario": "older_device",
                "device_id": "test-device-002",
                "features": {
                    "installation_date": str(datetime.now() - timedelta(days=730)),
                    "temperature_settings": 65.0,
                    "water_hardness": "hard",
                    "usage_intensity": "high",
                },
                "expected_results": {
                    "prediction_value": None,  # To be filled by test author
                    "confidence_min": 0.8,
                },
            },
        ],
        "edge_cases": [
            {
                "scenario": "new_device",
                "device_id": "test-device-003",
                "features": {
                    "installation_date": str(datetime.now() - timedelta(days=30)),
                    "temperature_settings": 50.0,
                    "water_hardness": "soft",
                    "usage_intensity": "low",
                },
                "expected_results": {
                    "prediction_value": None,  # To be filled by test author
                    "confidence_min": 0.5,
                },
            },
            {
                "scenario": "missing_data",
                "device_id": "test-device-004",
                "features": {
                    "installation_date": str(datetime.now() - timedelta(days=365)),
                    # Missing temperature_settings
                    "water_hardness": "moderate",
                    # Missing usage_intensity
                },
                "expected_results": {
                    "should_handle_gracefully": True,
                    "should_return_error": True,
                },
            },
        ],
    }

    with open(data_file, "w") as f:
        json.dump(test_data, f, indent=2)

    log_message(f"Generated test data at {data_file}")
    return data_file


def generate_mock_template(feature_name):
    """Generate a mock template for external dependencies."""
    snake_case_name = feature_name.replace("-", "_").lower()
    mock_file = TEST_MOCK_DIR / f"{snake_case_name}_mock.py"

    os.makedirs(Path(mock_file).parent, exist_ok=True)

    template = f'''"""
Mock objects for {feature_name} testing.
"""

import pytest
from unittest.mock import MagicMock

class MockDatabase:
    """Mock database connection for testing."""

    def __init__(self):
        self.query_results = []
        self.last_query = None

    def execute_query(self, query, params=None):
        """Mock query execution."""
        self.last_query = (query, params)
        return self.query_results

    def set_response(self, data):
        """Set the data to be returned by the mock."""
        self.query_results = data


@pytest.fixture
def mock_db():
    """Fixture that provides a mock database."""
    return MockDatabase()


class Mock{snake_case_name.capitalize()}Service:
    """Mock for external {snake_case_name} service."""

    def __init__(self):
        self.called_with = []
        self.return_value = {{"result": "mock_result"}}

    def call(self, *args, **kwargs):
        """Record call and return mock response."""
        self.called_with.append((args, kwargs))
        return self.return_value

    def set_response(self, response):
        """Set the response to be returned by the mock."""
        self.return_value = response


@pytest.fixture
def mock_{snake_case_name}_service():
    """Fixture that provides a mock {snake_case_name} service."""
    return Mock{snake_case_name.capitalize()}Service()
'''

    with open(mock_file, "w") as f:
        f.write(template)

    log_message(f"Generated mock template at {mock_file}")
    return mock_file


def generate_test_template(feature_name, phase="red"):
    """Generate a test template for the specified feature."""
    snake_case_name = feature_name.replace("-", "_").lower()
    test_file = PREDICTION_TEST_DIR / f"test_{snake_case_name}.py"

    # Create directory if it doesn't exist
    os.makedirs(PREDICTION_TEST_DIR, exist_ok=True)

    if test_file.exists() and phase == "red":
        log_message(f"Test file already exists: {test_file}", "WARNING")
        proceed = input("Do you want to overwrite it? (y/n): ")
        if proceed.lower() != "y":
            return None

    template = f'''"""
Test module for {feature_name} prediction feature.

This follows the TDD approach:
- Red: Write a failing test
- Green: Implement the feature to make the test pass
- Refactor: Clean up the code while keeping tests passing
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the mocks directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "mocks"))
from {snake_case_name}_mock import mock_db, mock_{snake_case_name}_service

# Import the module being tested
from src.predictions.maintenance.{snake_case_name} import {snake_case_name.capitalize()}Prediction


def load_test_data(scenario_type="standard_scenarios", scenario_name=None):
    """Load test data from the test data directory."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "{snake_case_name}"
    # Get the most recent test data file
    data_files = sorted(test_data_dir.glob("test_data_*.json"), reverse=True)

    if not data_files:
        raise FileNotFoundError(f"No test data found in {{test_data_dir}}")

    with open(data_files[0], 'r') as f:
        all_data = json.load(f)

    if scenario_name:
        # Find specific scenario
        for scenario in all_data[scenario_type]:
            if scenario["scenario"] == scenario_name:
                return scenario
        raise ValueError(f"Scenario {{scenario_name}} not found in {{scenario_type}}")

    # Return all scenarios of the specified type
    return all_data[scenario_type]


@pytest.mark.tdd_red
def test_{snake_case_name}_prediction_creation():
    """Test that the prediction class can be instantiated."""
    # Arrange & Act
    prediction = {snake_case_name.capitalize()}Prediction()

    # Assert
    assert prediction is not None


@pytest.mark.tdd_red
def test_{snake_case_name}_prediction_functionality():
    """Test the core prediction functionality."""
    # Arrange
    prediction = {snake_case_name.capitalize()}Prediction()
    test_scenario = load_test_data("standard_scenarios", "typical_device")

    device_id = test_scenario["device_id"]
    features = test_scenario["features"]

    # Act
    result = prediction.predict(device_id, features)

    # Assert
    assert result is not None
    assert "prediction_value" in result
    assert isinstance(result["prediction_value"], (int, float))
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1

    # Additional assertions based on expected results
    if test_scenario["expected_results"]["confidence_min"]:
        assert result["confidence"] >= test_scenario["expected_results"]["confidence_min"]


@pytest.mark.tdd_green
def test_{snake_case_name}_with_different_inputs():
    """Test prediction with different input types."""
    # Arrange
    prediction = {snake_case_name.capitalize()}Prediction()
    test_scenario = load_test_data("standard_scenarios", "older_device")

    device_id = test_scenario["device_id"]
    features = test_scenario["features"]

    # Convert temperature settings to a list to test different input types
    if "temperature_settings" in features:
        temp = features["temperature_settings"]
        features["temperature_settings"] = [temp - 5.0, temp, temp + 5.0]

    # Act
    result = prediction.predict(device_id, features)

    # Assert
    assert result is not None
    assert "prediction_value" in result


@pytest.mark.tdd_green
def test_{snake_case_name}_with_database(mock_db):
    """Test prediction with database interaction."""
    # Arrange
    prediction = {snake_case_name.capitalize()}Prediction(db=mock_db)
    test_scenario = load_test_data("standard_scenarios", "typical_device")

    device_id = test_scenario["device_id"]
    features = test_scenario["features"]

    # Setup mock response
    mock_db.set_response([{{"historical_data": "sample_value"}}])

    # Act
    result = prediction.predict(device_id, features)

    # Assert
    assert result is not None
    assert mock_db.last_query is not None, "Database should have been queried"


@pytest.mark.tdd_refactor
def test_{snake_case_name}_error_handling():
    """Test that the prediction handles errors gracefully."""
    # Arrange
    prediction = {snake_case_name.capitalize()}Prediction()
    test_scenario = load_test_data("edge_cases", "missing_data")

    device_id = test_scenario["device_id"]
    features = test_scenario["features"]

    # Act
    result = prediction.predict(device_id, features)

    # Assert
    assert result is not None
    if test_scenario["expected_results"].get("should_return_error", False):
        assert "error" in result

    # Even with bad input, it shouldn't raise an exception
    try:
        result_with_empty = prediction.predict(device_id, {{}})
        assert result_with_empty is not None
    except Exception as e:
        pytest.fail(f"Should not raise exception on empty features: {{e}}")


@pytest.mark.tdd_refactor
def test_{snake_case_name}_performance():
    """Test the performance characteristics of the prediction."""
    # Arrange
    prediction = {snake_case_name.capitalize()}Prediction()
    test_scenario = load_test_data("standard_scenarios", "typical_device")

    device_id = test_scenario["device_id"]
    features = test_scenario["features"]

    # Act
    import time
    start_time = time.time()
    result = prediction.predict(device_id, features)
    end_time = time.time()

    # Assert
    execution_time = end_time - start_time
    assert execution_time < 1.0, f"Prediction took too long: {{execution_time:.2f}} seconds"
    assert result is not None
'''

    with open(test_file, "w") as f:
        f.write(template)

    log_message(f"Generated test template at {test_file}")

    # Create an empty implementation file if it doesn't exist
    impl_dir = PROJECT_ROOT / "src" / "predictions" / "maintenance"
    os.makedirs(impl_dir, exist_ok=True)

    impl_file = impl_dir / f"{snake_case_name}.py"
    if not impl_file.exists() and phase == "red":
        with open(impl_file, "w") as f:
            f.write(
                f'''"""
{snake_case_name.capitalize()} prediction module for water heaters.

This module implements prediction functionality for {feature_name}.
"""

from typing import Dict, Any, Optional


class {snake_case_name.capitalize()}Prediction:
    """Prediction class for {feature_name}."""

    def __init__(self, db=None):
        """
        Initialize the prediction model.

        Args:
            db: Optional database connection
        """
        self.db = db

    def predict(self, device_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a prediction based on device features.

        Args:
            device_id: The ID of the device
            features: Dictionary of feature values

        Returns:
            Dictionary containing prediction results
        """
        # TODO: Implement this method
        # This is a placeholder that will fail tests (RED phase)
        return {{"error": "Not implemented yet"}}
'''
            )
        log_message(f"Generated implementation template at {impl_file}")

    # Save a checksum of the test file
    save_test_checksum(feature_name)

    return test_file


def run_with_coverage(feature_name, phase):
    """Run tests with coverage reporting."""
    snake_case_name = feature_name.replace("-", "_").lower()

    log_message(f"Running {phase} phase tests with coverage...")

    if phase == "red":
        marker = "tdd_red"
    elif phase == "green":
        marker = "tdd_red or tdd_green"
    elif phase == "refactor":
        marker = "tdd_red or tdd_green or tdd_refactor"
    else:
        marker = ""

    coverage_module = f"src.predictions.maintenance.{snake_case_name}"
    coverage_dir = f"coverage_html_{snake_case_name}"

    cmd = (
        f"python -m pytest src/tests -v -m '{marker}' "
        f"--cov={coverage_module} "
        f"--cov-report term --cov-report html:{coverage_dir}"
    )

    output = run_command(cmd)

    # Parse coverage percentage and alert if below threshold
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        coverage = int(match.group(1))
        if coverage < 90:
            log_message(
                f"Warning: Coverage is only {coverage}%, aim for at least 90%",
                "WARNING",
            )
        else:
            log_message(f"Good coverage: {coverage}%", "INFO")

    return output


def run_static_analysis(feature_name):
    """Run static analysis tools on the implemented code."""
    snake_case_name = feature_name.replace("-", "_").lower()
    impl_file = (
        PROJECT_ROOT / "src" / "predictions" / "maintenance" / f"{snake_case_name}.py"
    )

    log_message("Running static analysis...")

    try:
        # Run flake8 for style checking
        flake8_output = run_command(f"flake8 {impl_file}")
        if flake8_output:
            log_message("Style issues found:", "WARNING")
            log_message(flake8_output)
        else:
            log_message("No style issues found")
    except Exception as e:
        log_message(f"Error running flake8: {str(e)}", "ERROR")
        log_message("Make sure flake8 is installed: pip install flake8", "INFO")

    try:
        # Run pylint for more comprehensive analysis
        pylint_output = run_command(f"pylint {impl_file}")
        log_message(f"Pylint output: {pylint_output}")
    except Exception as e:
        log_message(f"Error running pylint: {str(e)}", "ERROR")
        log_message("Make sure pylint is installed: pip install pylint", "INFO")

    try:
        # Run mypy for type checking
        mypy_output = run_command(f"mypy {impl_file}")
        if mypy_output:
            log_message("Type checking issues found:", "WARNING")
            log_message(mypy_output)
        else:
            log_message("No type checking issues found")
    except Exception as e:
        log_message(f"Error running mypy: {str(e)}", "ERROR")
        log_message("Make sure mypy is installed: pip install mypy", "INFO")


def simulate_ci_pipeline(feature_name):
    """Simulate what would happen in CI/CD pipeline."""
    log_message(f"Simulating CI pipeline for {feature_name}...")

    # Run all tests
    log_message("Running all tests...")
    run_command("pytest src/tests -v")

    # Run coverage
    snake_case_name = feature_name.replace("-", "_").lower()
    coverage_module = f"src.predictions.maintenance.{snake_case_name}"
    log_message("Running coverage analysis...")
    run_command(f"python -m pytest src/tests --cov={coverage_module} --cov-report term")

    # Run static analysis
    log_message("Running static analysis...")
    impl_file = (
        PROJECT_ROOT / "src" / "predictions" / "maintenance" / f"{snake_case_name}.py"
    )
    try:
        run_command(f"flake8 {impl_file}")
        run_command(f"pylint {impl_file}")
        run_command(f"mypy {impl_file}")
    except Exception as e:
        log_message(f"Static analysis error: {str(e)}", "ERROR")

    log_message("CI pipeline simulation complete!")


def run_tdd_phase(feature_name, phase):
    """Run a specific TDD phase for the feature."""
    if not verify_postgres_running():
        log_message("PostgreSQL must be running to continue", "ERROR")
        return False

    check_timescaledb()  # Just informational, we don't require TimescaleDB

    # Always check if tests have been modified (except in red phase)
    if phase != "red" and not check_test_modifications(feature_name):
        return False

    if phase == "red":
        log_message(f"Starting RED phase for {feature_name}...")
        generate_test_template(feature_name, phase="red")
        generate_mock_template(feature_name)
        generate_test_data(feature_name)
        log_message("Running tests - they should fail at this point:")
        run_with_coverage(feature_name, "red")

    elif phase == "green":
        log_message(f"Starting GREEN phase for {feature_name}...")
        log_message("Running tests - they should pass after you implement the feature:")
        run_with_coverage(feature_name, "green")

    elif phase == "refactor":
        log_message(f"Starting REFACTOR phase for {feature_name}...")
        run_static_analysis(feature_name)
        log_message("Running all tests - they should all pass after refactoring:")
        run_with_coverage(feature_name, "refactor")

    elif phase == "cycle":
        log_message(f"Running full TDD cycle for {feature_name}...")
        run_tdd_phase(feature_name, "red")
        input(
            "\nImplement your feature now to make tests pass, then press Enter to continue to GREEN phase..."
        )
        run_tdd_phase(feature_name, "green")
        input(
            "\nRefactor your code now while keeping tests passing, then press Enter to continue to REFACTOR phase..."
        )
        run_tdd_phase(feature_name, "refactor")

        # Optionally run a CI simulation
        run_ci = input("Would you like to simulate a CI pipeline run? (y/n): ")
        if run_ci.lower() == "y":
            simulate_ci_pipeline(feature_name)

        log_message(f"Completed full TDD cycle for {feature_name}")

    elif phase == "ci":
        log_message(f"Running CI simulation for {feature_name}...")
        simulate_ci_pipeline(feature_name)

    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Enhanced TDD Workflow Helper for IoTSphere"
    )
    parser.add_argument(
        "phase",
        choices=["red", "green", "refactor", "cycle", "ci"],
        help="TDD phase to execute",
    )
    parser.add_argument("feature_name", help="Name of the feature to work on")

    args = parser.parse_args()

    log_message(f"TDD Workflow for feature: {args.feature_name}")
    run_tdd_phase(args.feature_name, args.phase)


if __name__ == "__main__":
    main()
