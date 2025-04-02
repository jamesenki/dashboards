#!/usr/bin/env python3
"""
Test runner for water heater configuration management components.
This script follows the Red-Green-Refactor TDD workflow to verify implementation.
"""
import logging
import os
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("water_heater_tdd")


def print_header(title):
    """Print a formatted section header."""
    separator = "=" * 80
    print(f"\n{separator}")
    print(f"  {title}")
    print(f"{separator}\n")


def run_test(test_path, test_name=None):
    """Run a specific test or test file with pytest."""
    cmd = ["pytest", "-xvs", test_path]
    if test_name:
        cmd.append(f"-k {test_name}")

    print_header(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("TEST OUTPUT:")
    print(result.stdout)

    if result.stderr:
        print("ERRORS:")
        print(result.stderr)

    print(f"Exit code: {result.returncode}")
    return result.returncode == 0


def run_all_tests():
    """Run the full TDD workflow for water heater configuration management."""
    success = True

    # Ensure test environment variable
    os.environ["USE_MOCK_DATA"] = "True"
    os.environ["TESTING"] = "True"

    print_header("WATER HEATER CONFIGURATION MANAGEMENT - TDD WORKFLOW")

    # 1. Repository tests
    print_header("STEP 1: Repository Tests (Repository Pattern Verification)")
    success = success and run_test(
        "tests/repositories/test_sqlite_water_heater_repository.py"
    )

    # 2. Service tests
    print_header("STEP 2: Service Tests (Business Logic Verification)")
    service_test_path = "tests/services/test_configurable_water_heater_service.py"

    # Check if service tests exist, otherwise skip
    if os.path.exists(service_test_path):
        success = success and run_test(service_test_path)
    else:
        print(f"WARNING: {service_test_path} not found. Skipping service tests.")
        print("TIP: Write service tests to verify business logic in isolation.")

    # 3. API tests
    print_header("STEP 3: API Tests (Interface Verification)")
    success = success and run_test("tests/api/test_configurable_water_heater_router.py")

    # 4. Integration tests (if they exist)
    print_header("STEP 4: Integration Tests (End-to-End Verification)")
    integration_test_path = "tests/integration/test_water_heater_integration.py"

    # Check if integration tests exist, otherwise skip
    if os.path.exists(integration_test_path):
        success = success and run_test(integration_test_path)
    else:
        print(
            f"WARNING: {integration_test_path} not found. Skipping integration tests."
        )
        print("TIP: Write integration tests to verify end-to-end functionality.")

    # Summary
    print_header("TEST SUMMARY")
    if success:
        print("✅ All tests PASSED")
        print(
            "The water heater configuration management implementation meets the requirements."
        )
    else:
        print("❌ Some tests FAILED")
        print("The implementation needs to be fixed to match test requirements.")
        print("Follow TDD principles: make changes to the code, not the tests!")

    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
