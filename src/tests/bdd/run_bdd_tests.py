#!/usr/bin/env python
"""
BDD Test Runner for IoTSphere

This script provides a convenient way to run BDD tests with various options.
It follows the TDD principles by focusing on running tests before implementation.

Usage:
  python run_bdd_tests.py [options]

Options:
  --tags=TAG         Run scenarios with specific tags (e.g., @api, @websocket)
  --feature=FILE     Run specific feature file
  --phase=PHASE      Run tests in specific TDD phase (@red, @green, @refactor)
  --report           Generate HTML report
  --junit            Generate JUnit XML report
  --coverage         Run with coverage report
  --verbose          Verbose output
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="BDD Test Runner for IoTSphere")
    parser.add_argument(
        "--tags", help="Run scenarios with specific tags (e.g., @api, @websocket)"
    )
    parser.add_argument("--feature", help="Run specific feature file")
    parser.add_argument(
        "--phase",
        choices=["red", "green", "refactor", "@red", "@green", "@refactor"],
        help="Run tests in specific TDD phase (@red, @green, @refactor)",
    )
    parser.add_argument(
        "--context",
        choices=[
            "device-management",
            "device-operation",
            "maintenance",
            "energy-management",
            "dashboard",
            "all",
        ],
        default="all",
        help="Run tests from a specific context/domain",
    )
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument(
        "--junit", action="store_true", help="Generate JUnit XML report"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def run_tests(args):
    """Run the BDD tests with the specified options."""
    # Get absolute paths
    bdd_dir = Path(__file__).parent.absolute()
    project_root = bdd_dir.parent.parent.parent
    reports_dir = project_root / "test-reports"

    # Create reports directory at the project root level
    try:
        reports_dir.mkdir(exist_ok=True, parents=True)
    except Exception as e:
        print(f"Warning: Could not create test-reports directory: {e}")

    # Change to BDD directory for test execution
    os.chdir(bdd_dir)

    # Set PYTHONPATH to include project root
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(project_root)

    # Build behave command
    cmd = ["behave"]

    # Determine features directory
    features_dir = "features"

    # Add tags if specified
    if args.tags:
        cmd.append(f"--tags={args.tags}")

    # Add phase if specified
    if args.phase:
        phase_tag = args.phase
        if not phase_tag.startswith("@"):
            phase_tag = f"@{phase_tag}"
        cmd.append(f"--tags={phase_tag}")

    # Add feature file if specified
    if args.feature:
        feature_path = args.feature
        if not feature_path.endswith(".feature"):
            feature_path += ".feature"

        # Handle relative paths
        if not os.path.isabs(feature_path):
            # Check various potential locations
            potential_paths = [
                feature_path,
                os.path.join(features_dir, feature_path),
                # Check in subdirectories
                *[
                    os.path.join(features_dir, subdir, os.path.basename(feature_path))
                    for subdir in ["dashboard", "maintenance", "device_management"]
                    if os.path.exists(os.path.join(features_dir, subdir))
                ],
            ]

            for path in potential_paths:
                if os.path.exists(path):
                    feature_path = path
                    break

        cmd.append(feature_path)
    else:
        # If no specific feature, run all features including subdirectories
        cmd.append(features_dir)

    # Add report options
    if args.report:
        # Use proper format for pretty output
        cmd.append("--format=pretty")

        # Create a local report file that will be processed by the main test report generator
        bdd_report_file = project_root / "test-reports" / "bdd_python_report.txt"
        cmd.append(f"--outfile={bdd_report_file}")

    if args.junit:
        # Create junit directory in the test-reports directory
        junit_path = project_root / "test-reports" / "junit"
        try:
            junit_path.mkdir(exist_ok=True, parents=True)
            cmd.append("--junit")
            cmd.append(f"--junit-directory={junit_path}")
        except Exception as e:
            print(f"Warning: Could not create junit directory: {e}")
            # Continue without junit if directory creation fails

    # Add verbose flag
    if args.verbose:
        cmd.append("--no-capture")
        cmd.append("--verbose")

    # Add coverage if specified
    if args.coverage:
        cmd = ["coverage", "run", "-m", "behave"] + cmd[1:]

    # Print TDD phase information if specified
    if args.phase:
        tdd_phases = {
            "@red": "RED phase - tests should fail (planned functionality)",
            "@green": "GREEN phase - tests should pass (minimal implementation)",
            "@refactor": "REFACTOR phase - tests should pass (improved implementation)",
        }
        phase = f"@{args.phase}" if not args.phase.startswith("@") else args.phase
        if phase in tdd_phases:
            print(f"\nRunning {tdd_phases[phase]}\n")

    # Run the command
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)

    # Generate coverage report if requested
    if args.coverage and result.returncode == 0:
        subprocess.run(["coverage", "report"])
        subprocess.run(["coverage", "html", "-d", "reports/coverage"])
        print("\nCoverage report generated in reports/coverage/index.html")

    return result.returncode


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 80)
    print("IoTSphere BDD Test Runner")
    print("=" * 80)

    # Run the tests
    exit_code = run_tests(args)

    # Output summary
    if exit_code == 0:
        print("\n✅ All BDD tests passed!")
    else:
        print("\n❌ Some BDD tests failed!")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
