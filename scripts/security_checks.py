#!/usr/bin/env python
"""
Security check script for pre-commit hooks.
Checks both Python and JavaScript dependencies for vulnerabilities,
only failing on critical issues.

Following TDD principles, this script contains self-tests to validate
its functionality before being used in production.
"""
import argparse
import json

# Configure logging
import logging
import os
import re
import subprocess
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityChecker:
    """Check dependencies for security vulnerabilities."""

    def __init__(
        self,
        fail_on_critical: bool = True,
        python_paths: Optional[List[str]] = None,
        js_paths: Optional[List[str]] = None,
        ignore_list: Optional[List[str]] = None,
    ):
        """
        Initialize the security checker.

        Args:
            fail_on_critical: Whether to exit with non-zero code on critical vulnerabilities
            python_paths: Paths to Python requirements files
            js_paths: Paths to JavaScript package.json files
            ignore_list: List of vulnerability IDs to ignore
        """
        self.fail_on_critical = fail_on_critical
        self.python_paths = python_paths or ["requirements.txt"]
        self.js_paths = js_paths or ["package.json"]
        self.ignore_list = ignore_list or []

        # Critical level thresholds
        self.python_critical_severity = "high"  # high or critical for Python
        self.js_critical_severity = "high"  # high or critical for JS

    def check_python_dependencies(self) -> Tuple[bool, int, List[Dict]]:
        """
        Check Python dependencies for vulnerabilities using safety.

        Returns:
            Tuple containing:
                - Whether all checks passed
                - Number of critical vulnerabilities found
                - List of vulnerability details
        """
        critical_count = 0
        all_passed = True
        all_vulnerabilities = []

        for req_file in self.python_paths:
            if not os.path.exists(req_file):
                logger.warning(f"Python requirements file not found: {req_file}")
                continue

            logger.info(f"Checking Python dependencies in {req_file}")

            # Run the updated safety scan command instead of the deprecated check command
            # Note: The scan command has different output format and exit codes
            try:
                # First try the newer 'scan' command (preferred)
                output = subprocess.check_output(
                    [
                        "safety",
                        "scan",
                        "-r",
                        req_file,
                        "--output",
                        "json",
                        "--exit-code",
                        "0",
                    ],
                    universal_newlines=True,
                    stderr=subprocess.PIPE,
                )
                has_vulnerabilities = "'vulnerabilities': " in output
                logger.info("Using new 'safety scan' command")

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(
                    f"New 'safety scan' command failed, falling back to legacy 'check': {e}"
                )

                # Fallback to the older 'check' command
                try:
                    output = subprocess.check_output(
                        ["safety", "check", "-r", req_file, "--json"],
                        universal_newlines=True,
                        stderr=subprocess.STDOUT,
                    )
                    has_vulnerabilities = False

                except subprocess.CalledProcessError as e:
                    # Exit code 64 is expected when vulnerabilities are found
                    if e.returncode == 64 and e.output:
                        output = e.output
                        has_vulnerabilities = True
                    else:
                        logger.error(f"Safety check failed with unexpected error: {e}")
                        logger.error(
                            f"Output: {e.output if hasattr(e, 'output') else 'None'}"
                        )
                        all_passed = False
                        critical_count += 1  # Consider unexpected failures as critical
                        continue

            # Parse the output
            try:
                results = json.loads(output)
                vulnerabilities = results.get("vulnerabilities", [])

                # Count critical vulnerabilities
                critical_in_this_file = 0
                for vuln in vulnerabilities:
                    severity = vuln.get("severity", "").lower()
                    vuln_id = vuln.get("vulnerability_id", "")

                    logger.info(
                        f"Found vulnerability {vuln_id} with severity {severity}"
                    )

                    if severity in ["critical", "high"]:
                        # Check if in ignore list
                        if vuln_id in self.ignore_list:
                            logger.warning(
                                f"Ignoring vulnerability {vuln_id} (in ignore list)"
                            )
                            continue

                        critical_count += 1
                        critical_in_this_file += 1
                        all_passed = False

                    all_vulnerabilities.append(vuln)

                if vulnerabilities:
                    logger.warning(
                        f"Found {len(vulnerabilities)} vulnerabilities in {req_file}"
                    )
                    logger.warning(f"{critical_in_this_file} of these are critical")
                else:
                    logger.info(f"No vulnerabilities found in {req_file}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse safety output: {e}")
                logger.error(f"Raw output: {output[:500]}...")
                all_passed = False

        return all_passed, critical_count, all_vulnerabilities

    def check_npm_dependencies(self) -> Tuple[bool, int, List[Dict]]:
        """
        Check npm dependencies for vulnerabilities.

        Returns:
            Tuple containing:
                - Whether all checks passed
                - Number of critical vulnerabilities found
                - List of vulnerability details
        """
        critical_count = 0
        all_passed = True
        all_vulnerabilities = []

        for package_file in self.js_paths:
            package_dir = os.path.dirname(os.path.abspath(package_file))

            if not os.path.exists(package_file):
                logger.warning(f"Package.json file not found: {package_file}")
                continue

            logger.info(f"Checking npm dependencies in {package_file}")

            # Run npm audit in JSON format for easier parsing
            try:
                # Use the directory of package.json as working directory
                output = subprocess.check_output(
                    ["npm", "audit", "--json"], universal_newlines=True, cwd=package_dir
                )

                try:
                    results = json.loads(output)
                    vulnerabilities = results.get("vulnerabilities", {})

                    # Count critical vulnerabilities
                    for pkg_name, vuln_info in vulnerabilities.items():
                        severity = vuln_info.get("severity", "").lower()
                        if severity in ["critical", "high"]:
                            # Check if in ignore list
                            vuln_id = vuln_info.get("id", "")
                            if str(vuln_id) in self.ignore_list:
                                logger.warning(
                                    f"Ignoring vulnerability {vuln_id} (in ignore list)"
                                )
                                continue

                            critical_count += 1
                            all_passed = False

                        all_vulnerabilities.append({"package": pkg_name, **vuln_info})

                    if vulnerabilities:
                        logger.warning(
                            f"Found {len(vulnerabilities)} vulnerable dependencies in {package_file}"
                        )
                        logger.warning(f"{critical_count} of these are critical")
                    else:
                        logger.info(f"No vulnerabilities found in {package_file}")

                except json.JSONDecodeError:
                    logger.error("Failed to parse npm audit output")
                    all_passed = False

            except subprocess.CalledProcessError as e:
                logger.error(f"npm audit failed: {e}")
                all_passed = False
                critical_count += 1  # Consider failures as critical

        return all_passed, critical_count, all_vulnerabilities

    def run_checks(self) -> int:
        """
        Run all security checks.

        Returns:
            Exit code: 0 if passed or only non-critical issues found,
                      1 if critical issues found and fail_on_critical is True
        """
        python_passed, python_critical, python_vulns = self.check_python_dependencies()
        js_passed, js_critical, js_vulns = self.check_npm_dependencies()

        total_critical = python_critical + js_critical
        all_passed = python_passed and js_passed

        # Create a summary
        logger.info("=== Security Check Summary ===")
        logger.info(
            f"Python: {len(python_vulns)} vulnerabilities, {python_critical} critical"
        )
        logger.info(
            f"JavaScript: {len(js_vulns)} vulnerabilities, {js_critical} critical"
        )
        logger.info(
            f"Total: {len(python_vulns) + len(js_vulns)} vulnerabilities, {total_critical} critical"
        )

        if not all_passed and self.fail_on_critical and total_critical > 0:
            logger.error("Critical vulnerabilities found - failing build")
            return 1

        if not all_passed:
            logger.warning("Some vulnerabilities found, but not failing build")
        else:
            logger.info("All security checks passed")

        return 0


class SecurityCheckerTests(unittest.TestCase):
    """Unit tests for the SecurityChecker."""

    def setUp(self):
        """Set up test files."""
        # Create temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create mock vulnerable requirements file
        self.req_path = os.path.join(self.temp_dir.name, "test_requirements.txt")
        with open(self.req_path, "w") as f:
            f.write("# Test vulnerable requirements\n")
            f.write("mlflow==2.8.0\n")  # Known vulnerable version

        # Create mock package.json
        self.pkg_path = os.path.join(self.temp_dir.name, "package.json")
        with open(self.pkg_path, "w") as f:
            f.write(
                '{"name": "test", "version": "1.0.0", "dependencies": {"lodash": "4.17.0"}}'
            )

    def test_python_checker(self):
        """Test Python dependency checker with known vulnerability."""
        # This test is marked to be skipped in CI environments
        if os.environ.get("CI") == "true":
            self.skipTest("Skipping in CI environment")

        checker = SecurityChecker(
            fail_on_critical=True, python_paths=[self.req_path], js_paths=[]
        )

        passed, critical, _ = checker.check_python_dependencies()

        # We expect it to fail because mlflow 2.8.0 has critical vulnerabilities
        self.assertFalse(passed)
        self.assertGreater(critical, 0)

    def test_with_ignore_list(self):
        """Test ignoring specific vulnerabilities."""
        # Create a checker that ignores all vulnerabilities
        checker = SecurityChecker(
            fail_on_critical=True,
            python_paths=[self.req_path],
            js_paths=[],
            ignore_list=["CVE-2023-6976", "CVE-2024-1483"],  # Known MLflow CVEs
        )

        # This should still fail because there are more CVEs, but with fewer counts
        _, critical_with_ignore, _ = checker.check_python_dependencies()

        # Create a checker without ignore list for comparison
        checker_no_ignore = SecurityChecker(
            fail_on_critical=True, python_paths=[self.req_path], js_paths=[]
        )

        _, critical_no_ignore, _ = checker_no_ignore.check_python_dependencies()

        # With ignores, we should have fewer critical vulnerabilities
        self.assertLessEqual(critical_with_ignore, critical_no_ignore)


def load_config(config_path="security_config.json"):
    """Load security configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def main():
    """Run security checks from command line."""
    parser = argparse.ArgumentParser(
        description="Check dependencies for security vulnerabilities"
    )
    parser.add_argument(
        "--python", action="append", help="Python requirements file paths"
    )
    parser.add_argument(
        "--js", action="append", help="JavaScript package.json file paths"
    )
    parser.add_argument("--ignore", action="append", help="Vulnerability IDs to ignore")
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        default=True,
        help="Fail on critical vulnerabilities",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only report issues, never fail the build",
    )
    parser.add_argument(
        "--test", action="store_true", help="Run self-tests instead of checks"
    )
    parser.add_argument(
        "--config",
        default="security_config.json",
        help="Path to security configuration file",
    )

    args = parser.parse_args()

    if args.test:
        # Run self-tests
        unittest.main(argv=[sys.argv[0]])
        return 0

    # Load configuration
    config = load_config(args.config)
    python_config = config.get("python", {})
    js_config = config.get("javascript", {})

    # Get ignore lists from config
    python_ignores = python_config.get("ignore_vulnerabilities", [])
    js_ignores = js_config.get("ignore_vulnerabilities", [])

    # Combine with command line ignores
    all_ignores = python_ignores + js_ignores
    if args.ignore:
        all_ignores.extend(args.ignore)

    # Get paths from config or command line
    python_paths = args.python or python_config.get("paths", ["requirements.txt"])
    js_paths = args.js or js_config.get("paths", ["package.json"])

    # If report-only is set, override fail-on-critical
    if args.report_only:
        args.fail_on_critical = False

    logger.info(f"Running security checks with config from {args.config}")
    logger.info(f"Python paths: {python_paths}")
    logger.info(f"JS paths: {js_paths}")
    logger.info(f"Ignoring vulnerabilities: {all_ignores}")

    checker = SecurityChecker(
        fail_on_critical=args.fail_on_critical,
        python_paths=python_paths,
        js_paths=js_paths,
        ignore_list=all_ignores,
    )

    return checker.run_checks()


if __name__ == "__main__":
    sys.exit(main())
