#!/usr/bin/env python3
"""
Comprehensive UI Test Runner for IoTSphere
Following Test-Driven Development (TDD) principles:
1. RED: Define expected behavior through tests
2. GREEN: Implement fixes to make tests pass
3. REFACTOR: Improve implementation while maintaining test coverage
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests" / "integration"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"
SERVER_PORT = 8000

# Ensure screenshots directory exists
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


# Set up colored output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}\n")


def print_step(step_number, message):
    """Print a formatted step message"""
    print(f"{Colors.BLUE}{Colors.BOLD}[STEP {step_number}] {message}{Colors.END}")


def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}✅ {message}{Colors.END}")


def print_failure(message):
    """Print a failure message"""
    print(f"{Colors.RED}{Colors.BOLD}❌ {message}{Colors.END}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  {message}{Colors.END}")


def check_server_running():
    """Check if the server is running on the expected port"""
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", SERVER_PORT))
        s.close()
        return True
    except:
        return False


def start_server():
    """Start the server if not already running"""
    if check_server_running():
        print_success(f"Server already running on port {SERVER_PORT}")
        return None

    print_step(1, f"Starting server on port {SERVER_PORT}")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    start_time = time.time()
    while not check_server_running() and time.time() - start_time < 10:
        time.sleep(0.5)

    if check_server_running():
        print_success("Server started successfully")
        return server_process
    else:
        print_failure("Failed to start server")
        server_process.terminate()
        return None


def discover_tests():
    """Discover all test files in the integration tests directory"""
    print_step(2, "Discovering test files")

    test_files = list(TESTS_DIR.glob("test_*.py"))
    if not test_files:
        print_failure("No test files found!")
        return []

    print_success(f"Found {len(test_files)} test files:")
    for i, test_file in enumerate(test_files, 1):
        print(f"  {i}. {test_file.name}")

    return sorted(test_files)


def run_test(test_file):
    """Run a specific test file"""
    test_name = test_file.stem
    print_step(3, f"Running test: {test_name}")

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    duration = time.time() - start_time

    # Print output
    if result.stdout:
        print(result.stdout)

    if result.stderr and "Traceback" in result.stderr:
        print_failure(f"Test {test_name} failed with errors:")
        print(result.stderr)
        return False

    if result.returncode != 0:
        print_failure(f"Test {test_name} failed with return code {result.returncode}")
        return False

    print_success(f"Test {test_name} completed successfully in {duration:.2f} seconds")
    return True


def run_all_tests(test_files):
    """Run all discovered tests"""
    if not test_files:
        print_warning("No tests to run!")
        return

    print_header("RUNNING ALL UI TESTS")

    results = []
    for test_file in test_files:
        result = run_test(test_file)
        results.append((test_file.name, result))

    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        status = (
            f"{Colors.GREEN}PASSED{Colors.END}"
            if result
            else f"{Colors.RED}FAILED{Colors.END}"
        )
        print(f"  {name}: {status}")

    if failed == 0:
        print_success(f"All {len(results)} tests passed successfully!")
    else:
        print_failure(f"{failed} tests failed out of {len(results)} total tests")


def verify_test_results():
    """Verify test results by checking for screenshot evidence"""
    print_step(4, "Verifying test evidence")

    screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
    if not screenshots:
        print_warning("No screenshot evidence found")
        return

    print_success(f"Found {len(screenshots)} screenshots as test evidence")

    # List latest screenshots
    latest_screenshots = sorted(screenshots, key=os.path.getmtime, reverse=True)[:5]
    print("Latest test evidence:")
    for i, screenshot in enumerate(latest_screenshots, 1):
        modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot))
        print(
            f"  {i}. {screenshot.name} (Created: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )


def main():
    """Main function to run all tests"""
    parser = argparse.ArgumentParser(description="Run UI tests for IoTSphere")
    parser.add_argument(
        "--no-server", action="store_true", help="Don't start the server"
    )
    args = parser.parse_args()

    print_header("IOTSPHERE UI TEST SUITE")
    print(f"Running in TDD mode: RED → GREEN → REFACTOR")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {PROJECT_ROOT}")

    # Start server if needed
    server_process = None
    if not args.no_server:
        server_process = start_server()
        if not server_process and not check_server_running():
            print_failure("Cannot proceed without a running server")
            return 1

    try:
        # Discover and run tests
        test_files = discover_tests()
        run_all_tests(test_files)
        verify_test_results()

        print_header("TEST RUN COMPLETED")
        return 0

    except KeyboardInterrupt:
        print_warning("\nTest run interrupted by user")
        return 130

    finally:
        # Clean up server process if we started it
        if server_process:
            print_step(5, "Stopping server")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print_success("Server stopped successfully")
            except subprocess.TimeoutExpired:
                server_process.kill()
                print_warning("Server process had to be killed")


if __name__ == "__main__":
    sys.exit(main())
