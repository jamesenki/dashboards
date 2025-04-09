#!/usr/bin/env python3
"""
IoTSphere Comprehensive Test Runner
-----------------------------------
Orchestrates running all test types and generates a tabbed HTML report.
This follows TDD principles by providing clear visibility into test results.

Enhanced to support shadow document setup for tests that require it.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Define test types and their configurations
TEST_TYPES = {
    "unit": {
        "name": "Unit Tests",
        "command": "python -m pytest tests/unit --verbose",
        "report_file": "unit_tests_report.json",
        "description": "Tests for individual functions and methods",
    },
    "integration": {
        "name": "Integration Tests",
        "command": "python -m pytest tests/integration --verbose",
        "report_file": "integration_tests_report.json",
        "description": "Tests for component interactions",
    },
    "bdd": {
        "name": "BDD Tests",
        "command": "cd $(dirname $0) && npx cucumber-js --config tests/behavior/config/cucumber.js --format json:cucumber-report.json",
        "report_file": "cucumber-report.json",
        "description": "Behavior-driven development tests using Gherkin syntax",
    },
    "realtime": {
        "name": "Real-Time Update Tests",
        "command": "cd $(dirname $0) && npx cucumber-js --config tests/behavior/config/cucumber.js --profile realtime --format json:realtime-report.json",
        "report_file": "realtime-report.json",
        "description": "Tests for WebSocket-based real-time data updates",
    },
    "ui": {
        "name": "UI Tests",
        "command": "npx playwright test --reporter=json",
        "report_file": "playwright-report/results.json",
        "description": "Tests for user interface components",
    },
    "e2e": {
        "name": "End-to-End Tests",
        "command": "python e2e_websocket_test.py --json-report e2e_report.json",
        "report_file": "e2e_report.json",
        "description": "Full workflow tests from end to end",
    },
}


class TestRunner:
    """Orchestrates running various test types and generating reports."""

    def __init__(self, config_file: str = "test_config.json"):
        """Initialize the test runner with configuration."""
        self.project_root = Path(__file__).parent
        self.start_time = time.time()

        # Load config file if it exists, otherwise use defaults
        self.config_path = self.project_root / config_file
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "test_types": TEST_TYPES,
                "report_dir": "test_reports",
                "parallel": True,
                "timeout": 600,  # 10 minutes max per test type
                "report_title": "IoTSphere Test Report",
            }
            # Save default config
            self._save_config()

        # Create report directory if it doesn't exist
        self.report_dir = self.project_root / self.config["report_dir"]
        self.report_dir.mkdir(exist_ok=True)

        # Initialize results storage
        self.results = {}

    def _save_config(self):
        """Save the current configuration to file."""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def run_test(self, test_type: str) -> Dict[str, Any]:
        """Run a specific test type and return the results."""
        if test_type not in self.config["test_types"]:
            return {
                "success": False,
                "error": f"Unknown test type: {test_type}",
                "duration": 0,
                "tests_run": 0,
                "tests_passed": 0,
            }

        test_config = self.config["test_types"][test_type]
        print(f"Running {test_config['name']}...")

        test_start = time.time()
        try:
            # Run the test command
            # Convert string command to list for security if it's a string
            cmd = test_config["command"]
            if isinstance(cmd, str):
                # Split the command into a list for secure execution
                import shlex

                cmd = shlex.split(cmd)

            process = subprocess.run(
                cmd,
                shell=False,  # Set shell=False for security
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.config["timeout"],
            )

            success = process.returncode == 0

            # Check if report file was generated
            report_path = self.project_root / test_config["report_file"]
            report_exists = report_path.exists()

            # Copy report file to report directory with timestamp
            if report_exists:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.report_dir / f"{test_type}_{timestamp}.json"

                # Read the report file
                with open(report_path, "r") as src_file:
                    report_content = src_file.read()

                # Write to destination
                with open(dest_path, "w") as dest_file:
                    dest_file.write(report_content)

            return {
                "success": success,
                "output": process.stdout,
                "error": process.stderr,
                "duration": time.time() - test_start,
                "returncode": process.returncode,
                "report_file": str(dest_path) if report_exists else None,
                "report_content": report_content if report_exists else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Test timed out after {self.config['timeout']} seconds",
                "duration": time.time() - test_start,
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - test_start,
                "returncode": -1,
            }

    def setup_shadow_documents(self) -> bool:
        """Set up shadow documents for testing if configuration exists."""
        if "shadow_setup" not in self.config:
            print("No shadow document setup configured, skipping...")
            return True

        shadow_config = self.config["shadow_setup"]
        print("Setting up shadow documents for testing...")

        try:
            # Run the shadow setup command
            # Convert string command to list for security if it's a string
            cmd = shadow_config["command"]
            if isinstance(cmd, str):
                # Split the command into a list for secure execution
                import shlex

                cmd = shlex.split(cmd)

            process = subprocess.run(
                cmd,
                shell=False,  # Set shell=False for security
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=shadow_config.get("timeout", 60),
            )

            if process.returncode == 0:
                print("Shadow document setup successful")
                return True
            else:
                print(f"Shadow document setup failed: {process.stderr}")
                return False

        except Exception as e:
            print(f"Error during shadow document setup: {str(e)}")
            return False

    def run_all_tests(
        self, selected_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run all selected test types, or all configured types if none selected."""
        # Check if any tests require shadow document setup
        types_to_run = selected_types or list(self.config["test_types"].keys())

        # Check if any selected test types require shadow setup
        requires_shadow = any(
            self.config["test_types"].get(test_type, {}).get("requires_shadow", False)
            for test_type in types_to_run
        )

        # If shadow setup is required, run it first
        if requires_shadow:
            setup_success = self.setup_shadow_documents()
            if not setup_success:
                print("WARNING: Shadow document setup failed, tests may fail")
        types_to_run = selected_types or list(self.config["test_types"].keys())
        start_time = time.time()

        if self.config["parallel"]:
            # Run tests in parallel
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self.run_test, test_type): test_type
                    for test_type in types_to_run
                }
                for future in futures:
                    test_type = futures[future]
                    self.results[test_type] = future.result()
        else:
            # Run tests sequentially
            for test_type in types_to_run:
                self.results[test_type] = self.run_test(test_type)

        # Calculate overall statistics
        total_duration = time.time() - start_time
        success_count = sum(1 for result in self.results.values() if result["success"])

        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_duration": total_duration,
            "tests_run": len(types_to_run),
            "tests_passed": success_count,
            "success_rate": success_count / len(types_to_run) if types_to_run else 0,
            "results": self.results,
        }

        # Save summary to report directory
        summary_path = self.report_dir / "test_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        # Generate HTML report
        self.generate_report(summary)

        return summary

    def extract_detailed_test_results(
        self, test_type: str, report_data: Any
    ) -> List[Dict[str, Any]]:
        """Extract detailed test results from report data based on test type.

        Args:
            test_type: The type of test (unit, integration, bdd, ui, e2e)
            report_data: The test report data

        Returns:
            List of individual test results with details
        """
        tests = []

        # Handle different report formats based on test type
        if not report_data:
            return tests

        try:
            if test_type == "unit" or test_type == "integration" or test_type == "e2e":
                # pytest-json format
                if "tests" in report_data:
                    for test_data in report_data.get("tests", []):
                        test_result = {
                            "name": test_data.get("nodeid", "Unknown Test"),
                            "success": test_data.get("outcome") == "passed",
                            "duration": test_data.get("duration", 0),
                            "error": test_data.get("call", {})
                            .get("crash", {})
                            .get("message", ""),
                            "traceback": test_data.get("call", {})
                            .get("crash", {})
                            .get("traceback", ""),
                            "output": test_data.get("stdout", "")
                            + test_data.get("stderr", ""),
                        }
                        tests.append(test_result)

            elif test_type == "bdd" or test_type == "realtime":
                # cucumber-json format
                for feature in report_data:
                    feature_name = feature.get("name", "Unknown Feature")
                    for element in feature.get("elements", []):
                        scenario_name = (
                            f"{feature_name}: {element.get('name', 'Unknown Scenario')}"
                        )
                        failed_steps = []
                        duration = 0
                        output = ""

                        for step in element.get("steps", []):
                            step_result = step.get("result", {})
                            duration += (
                                step_result.get("duration", 0) / 1e9
                            )  # Convert nanoseconds to seconds

                            if step_result.get("status") != "passed":
                                failed_steps.append(
                                    {
                                        "step": step.get("name", "Unknown Step"),
                                        "error": step_result.get("error_message", ""),
                                    }
                                )

                            # Collect any output
                            if "output" in step_result:
                                output += step_result["output"] + "\n"

                        test_result = {
                            "name": scenario_name,
                            "success": len(failed_steps) == 0,
                            "duration": duration,
                            "error": "\n".join(
                                [
                                    f"Step: {s['step']}\nError: {s['error']}"
                                    for s in failed_steps
                                ]
                            ),
                            "output": output,
                        }
                        tests.append(test_result)

            elif test_type == "ui":
                # playwright-json format
                for suite in report_data.get("suites", []):
                    for spec in suite.get("specs", []):
                        test_result = {
                            "name": spec.get("title", "Unknown Test"),
                            "success": spec.get("ok", False),
                            "duration": spec.get("duration", 0)
                            / 1000,  # Convert ms to seconds
                            "error": "\n".join(
                                [
                                    error.get("message", "")
                                    for error in spec.get("errors", [])
                                ]
                            ),
                            "output": "\n".join(
                                spec.get("stdout", []) + spec.get("stderr", [])
                            ),
                        }
                        tests.append(test_result)
        except Exception as e:
            print(f"Error extracting test results for {test_type}: {str(e)}")

        return tests

    def generate_detailed_report(self, test_type: str, result: Dict[str, Any]) -> str:
        """Generate a detailed HTML report for a specific test type.

        Args:
            test_type: The type of test
            result: The test result data

        Returns:
            Path to the generated report file
        """
        from jinja2 import Template

        # Define the report template path
        template_path = self.project_root / "templates" / "report_detail_template.html"

        # Extract tests from report data if available
        report_data = result.get("report_content")
        if report_data and isinstance(report_data, str):
            try:
                report_data = json.loads(report_data)
            except:
                report_data = None

        tests = self.extract_detailed_test_results(test_type, report_data)

        # Create template context
        test_config = self.config["test_types"][test_type]
        context = {
            "report_title": self.config["report_title"],
            "test_type_name": test_config["name"],
            "test_description": test_config.get("description", ""),
            "test_command": test_config["command"],
            "overall_success": result["success"],
            "duration": result["duration"],
            "tests": tests,
            "tests_passed": len([t for t in tests if t["success"]]),
            "total_tests": len(tests),
            "output": result.get("output", ""),
            "error": result.get("error", ""),
            "latest_report_filename": "latest_report.html",
        }

        # Load template if exists, otherwise use default template
        if template_path.exists():
            with open(template_path, "r") as f:
                template_content = f.read()
        else:
            print(
                f"Detailed report template not found at {template_path}, using default template"
            )
            # Default simple template would be defined here
            template_content = (
                "<html><body><h1>{{ test_type_name }} Results</h1></body></html>"
            )

        # Render template
        template = Template(template_content)
        report_html = template.render(**context)

        # Generate unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{test_type}_detail_{timestamp}.html"
        report_path = self.report_dir / report_filename

        # Write report file
        with open(report_path, "w") as f:
            f.write(report_html)

        # Create a symbolic link to the latest report
        latest_path = self.report_dir / f"{test_type}_detail_latest.html"
        if os.path.exists(latest_path):
            os.remove(latest_path)
        with open(latest_path, "w") as f:
            f.write(report_html)

        return str(report_path)

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate an HTML report with tabs for each test type."""
        from jinja2 import Template

        # Define the report template path
        template_path = self.project_root / "templates" / "report_template.html"

        # Create template directory if it doesn't exist
        template_dir = self.project_root / "templates"
        template_dir.mkdir(exist_ok=True)

        # Default template content
        default_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ report_title }}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    background-color: #333;
                    color: white;
                    padding: 10px 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }
                .summary {
                    display: flex;
                    flex-wrap: wrap;
                    margin-bottom: 20px;
                }
                .summary-box {
                    background-color: #f4f4f4;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-right: 15px;
                    margin-bottom: 15px;
                    min-width: 150px;
                }
                .summary-box.success {
                    background-color: #e8f5e9;
                    border-color: #66bb6a;
                }
                .summary-box.failure {
                    background-color: #ffebee;
                    border-color: #ef5350;
                }
                .tab-container {
                    margin-top: 20px;
                }
                .tab-buttons {
                    overflow: hidden;
                    border: 1px solid #ccc;
                    background-color: #f1f1f1;
                    border-radius: 5px 5px 0 0;
                }
                .tab-buttons button {
                    background-color: inherit;
                    float: left;
                    border: none;
                    outline: none;
                    cursor: pointer;
                    padding: 10px 16px;
                    transition: 0.3s;
                    font-size: 16px;
                }
                .tab-buttons button:hover {
                    background-color: #ddd;
                }
                .tab-buttons button.active {
                    background-color: #ccc;
                }
                .tab-content {
                    display: none;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-top: none;
                    border-radius: 0 0 5px 5px;
                }
                .test-details {
                    margin-top: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #f9f9f9;
                }
                .test-output {
                    white-space: pre-wrap;
                    background-color: #f4f4f4;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    padding: 10px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 14px;
                    margin-top: 10px;
                }
                .test-error {
                    white-space: pre-wrap;
                    background-color: #ffe8e8;
                    border: 1px solid #f5c8c8;
                    border-radius: 3px;
                    padding: 10px;
                    max-height: 200px;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 14px;
                    margin-top: 10px;
                    color: #c41e3a;
                }
                .success-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    background-color: #4caf50;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .failure-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    background-color: #f44336;
                    color: white;
                    border-radius: 4px;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report_title }}</h1>
                <p>Generated on {{ summary.timestamp }}</p>
            </div>

            <div class="summary">
                <div class="summary-box {% if summary.success_rate == 1 %}success{% elif summary.success_rate < 0.5 %}failure{% endif %}">
                    <h3>Overall Results</h3>
                    <p>Success Rate: {{ (summary.success_rate * 100)|round(1) }}%</p>
                    <p>{{ summary.tests_passed }} of {{ summary.tests_run }} test suites passed</p>
                    <p>Total Duration: {{ (summary.total_duration / 60)|round(2) }} minutes</p>
                </div>

                {% for test_type, result in summary.results.items() %}
                <div class="summary-box {% if result.success %}success{% else %}failure{% endif %}">
                    <h3>{{ config.test_types[test_type].name }}</h3>
                    <p>Status: {% if result.success %}<span class="success-badge">PASSED</span>{% else %}<span class="failure-badge">FAILED</span>{% endif %}</p>
                    <p>Duration: {{ result.duration|round(2) }} seconds</p>
                </div>
                {% endfor %}
            </div>

            <div class="tab-container">
                <div class="tab-buttons">
                    {% for test_type, result in summary.results.items() %}
                    <button class="tab-button" onclick="openTab(event, '{{ test_type }}')" {% if loop.first %}id="default-tab"{% endif %}>
                        {{ config.test_types[test_type].name }}
                    </button>
                    {% endfor %}
                </div>

                {% for test_type, result in summary.results.items() %}
                <div id="{{ test_type }}" class="tab-content">
                    <h2>{{ config.test_types[test_type].name }} Results</h2>
                    <p>{{ config.test_types[test_type].description }}</p>

                    <div class="test-details">
                        <h3>Execution Details</h3>
                        <p>Command: <code>{{ config.test_types[test_type].command }}</code></p>
                        <p>Exit Code: {{ result.returncode }}</p>
                        <p>Duration: {{ result.duration|round(2) }} seconds</p>

                        {% if result.output and result.output.strip() %}
                        <h4>Output:</h4>
                        <div class="test-output">{{ result.output }}</div>
                        {% endif %}

                        {% if result.error and result.error.strip() %}
                        <h4>Errors:</h4>
                        <div class="test-error">{{ result.error }}</div>
                        {% endif %}

                        {% if result.report_file %}
                        <h4>Report File:</h4>
                        <p><a href="{{ result.report_file }}" target="_blank">{{ result.report_file }}</a></p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>

            <script>
                function openTab(evt, tabName) {
                    var i, tabcontent, tabbuttons;

                    // Hide all tab content
                    tabcontent = document.getElementsByClassName("tab-content");
                    for (i = 0; i < tabcontent.length; i++) {
                        tabcontent[i].style.display = "none";
                    }

                    // Remove active class from tab buttons
                    tabbuttons = document.getElementsByClassName("tab-button");
                    for (i = 0; i < tabbuttons.length; i++) {
                        tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
                    }

                    // Show current tab and add active class to button
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";
                }

                // Get the default tab and click it
                document.getElementById("default-tab").click();
            </script>
        </body>
        </html>
        """

        # Create the template file if it doesn't exist
        if not template_path.exists():
            with open(template_path, "w") as f:
                f.write(default_template)

        # Generate the report
        with open(template_path, "r") as f:
            template = Template(f.read())

        report_html = template.render(
            report_title=self.config["report_title"],
            summary=summary,
            config=self.config,
        )

        # Save the report
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"test_report_{timestamp}.html"
        report_path = self.report_dir / report_filename

        with open(report_path, "w") as f:
            f.write(report_html)

        # Create a symlink to the latest report
        latest_path = self.report_dir / "latest_report.html"
        if latest_path.exists():
            latest_path.unlink()

        os.symlink(report_path, latest_path)

        print(f"\nReport generated: {report_path}")
        return str(report_path)


def main():
    """Parse command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Run IoTSphere tests and generate reports"
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=TEST_TYPES.keys(),
        help="Test types to run (default: all)",
    )
    parser.add_argument(
        "--config",
        default="test_config.json",
        help="Path to config file (default: test_config.json)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run tests sequentially instead of in parallel",
    )

    args = parser.parse_args()

    runner = TestRunner(args.config)

    # Override parallel setting if specified
    if args.sequential:
        runner.config["parallel"] = False

    # Run tests and print summary
    summary = runner.run_all_tests(args.types)

    print("\n--- Test Summary ---")
    print(f"Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"{summary['tests_passed']} of {summary['tests_run']} test types passed")
    print(f"Total Duration: {summary['total_duration']/60:.2f} minutes")

    # Determine exit code based on success rate
    return 0 if summary["success_rate"] == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
