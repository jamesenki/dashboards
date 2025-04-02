#!/usr/bin/env python
"""
Code Quality Checker for IoTSphere

This script runs various code quality tools to ensure adherence to the
IoTSphere coding standards.
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional, Tuple


def print_header(title: str) -> None:
    """Print a formatted header for a section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_command(command: List[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    """Run a command and return its exit code and output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.returncode, result.stdout
    except Exception as e:
        return 1, str(e)


def check_python_code(path: str, fix: bool = False) -> bool:
    """Run Python code quality checks."""
    print_header("PYTHON CODE QUALITY CHECKS")
    success = True
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Check Python code formatting with Black
    print("\n🔍 Checking Python code formatting with Black...")
    black_args = ["black", "--check", path] if not fix else ["black", path]
    exit_code, output = run_command(black_args, cwd=project_root)
    if exit_code != 0:
        print(f"❌ Black found formatting issues:\n{output}")
        success = False
    else:
        print("✅ Black check passed!")

    # Check import sorting with isort
    print("\n🔍 Checking import sorting with isort...")
    isort_args = (
        ["isort", "--check-only", "--profile", "black", path]
        if not fix
        else ["isort", "--profile", "black", path]
    )
    exit_code, output = run_command(isort_args, cwd=project_root)
    if exit_code != 0:
        print(f"❌ isort found import sorting issues:\n{output}")
        success = False
    else:
        print("✅ isort check passed!")

    # Check for PEP 8 compliance with flake8
    print("\n🔍 Checking PEP 8 compliance with flake8...")
    exit_code, output = run_command(["flake8", path], cwd=project_root)
    if exit_code != 0:
        print(f"❌ flake8 found PEP 8 issues:\n{output}")
        success = False
    else:
        print("✅ flake8 check passed!")

    # Check type hints with mypy
    print("\n🔍 Checking type hints with mypy...")
    exit_code, output = run_command(["mypy", path], cwd=project_root)
    if exit_code != 0:
        print(f"❌ mypy found type hinting issues:\n{output}")
        success = False
    else:
        print("✅ mypy check passed!")

    return success


def check_javascript_code(path: str, fix: bool = False) -> bool:
    """Run JavaScript code quality checks."""
    print_header("JAVASCRIPT CODE QUALITY CHECKS")
    success = True
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Check JavaScript code with ESLint
    print("\n🔍 Checking JavaScript code with ESLint...")
    eslint_args = (
        ["npx", "eslint", path] if not fix else ["npx", "eslint", "--fix", path]
    )
    exit_code, output = run_command(eslint_args, cwd=project_root)
    if exit_code != 0:
        print(f"❌ ESLint found issues:\n{output}")
        success = False
    else:
        print("✅ ESLint check passed!")

    # Format JavaScript code with Prettier
    print("\n🔍 Checking JavaScript formatting with Prettier...")
    prettier_args = (
        ["npx", "prettier", "--check", path]
        if not fix
        else ["npx", "prettier", "--write", path]
    )
    exit_code, output = run_command(prettier_args, cwd=project_root)
    if exit_code != 0:
        print(f"❌ Prettier found formatting issues:\n{output}")
        success = False
    else:
        print("✅ Prettier check passed!")

    return success


def check_html_css(path: str, fix: bool = False) -> bool:
    """Run HTML/CSS code quality checks."""
    print_header("HTML/CSS CODE QUALITY CHECKS")
    success = True
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Check HTML with HTMLHint
    print("\n🔍 Checking HTML with HTMLHint...")
    exit_code, output = run_command(["npx", "htmlhint", path], cwd=project_root)
    if exit_code != 0:
        print(f"❌ HTMLHint found issues:\n{output}")
        success = False
    else:
        print("✅ HTMLHint check passed!")

    # Check CSS with stylelint
    print("\n🔍 Checking CSS with stylelint...")
    stylelint_args = (
        ["npx", "stylelint", f"{path}/**/*.css"]
        if not fix
        else ["npx", "stylelint", f"{path}/**/*.css", "--fix"]
    )
    exit_code, output = run_command(stylelint_args, cwd=project_root)
    if exit_code != 0:
        print(f"❌ stylelint found issues:\n{output}")
        success = False
    else:
        print("✅ stylelint check passed!")

    return success


def check_docstrings(path: str) -> bool:
    """Check for docstrings in Python files."""
    print_header("DOCSTRING CHECKS")
    success = True
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    print("\n🔍 Checking Python docstrings with pydocstyle...")
    exit_code, output = run_command(
        ["pydocstyle", "--convention=google", path], cwd=project_root
    )
    if exit_code != 0:
        print(f"❌ pydocstyle found docstring issues:\n{output}")
        success = False
    else:
        print("✅ pydocstyle check passed!")

    return success


def check_security(path: str) -> bool:
    """Run security checks on code."""
    print_header("SECURITY CHECKS")
    success = True
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Check Python code for security issues with bandit
    print("\n🔍 Checking Python code for security issues with bandit...")
    exit_code, output = run_command(["bandit", "-r", path], cwd=project_root)
    if exit_code != 0:
        print(f"❌ bandit found security issues:\n{output}")
        success = False
    else:
        print("✅ bandit check passed!")

    # Check JavaScript code for security issues with npm audit
    print("\n🔍 Checking JavaScript dependencies for security issues...")
    exit_code, output = run_command(["npm", "audit"], cwd=project_root)
    if exit_code != 0:
        print(f"❌ npm audit found security issues:\n{output}")
        success = False
    else:
        print("✅ npm audit check passed!")

    return success


def main() -> int:
    """Run the code quality checks."""
    parser = argparse.ArgumentParser(description="IoTSphere Code Quality Checker")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )
    parser.add_argument("--python", action="store_true", help="Only check Python code")
    parser.add_argument(
        "--javascript", action="store_true", help="Only check JavaScript code"
    )
    parser.add_argument("--html-css", action="store_true", help="Only check HTML/CSS")
    parser.add_argument(
        "--security", action="store_true", help="Only run security checks"
    )
    parser.add_argument(
        "--docstrings", action="store_true", help="Only check docstrings"
    )

    args = parser.parse_args()
    path = os.path.abspath(args.path)

    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist.")
        return 1

    # If no specific checks are selected, run all checks
    run_all = not (
        args.python
        or args.javascript
        or args.html_css
        or args.security
        or args.docstrings
    )
    success = True

    if run_all or args.python:
        if not check_python_code(path, args.fix):
            success = False

    if run_all or args.javascript:
        if not check_javascript_code(path, args.fix):
            success = False

    if run_all or args.html_css:
        if not check_html_css(path, args.fix):
            success = False

    if run_all or args.docstrings:
        if not check_docstrings(path):
            success = False

    if run_all or args.security:
        if not check_security(path):
            success = False

    if success:
        print_header("ALL CHECKS PASSED! ✅")
        return 0
    else:
        print_header("SOME CHECKS FAILED ❌")
        if args.fix:
            print("Some issues were automatically fixed. Please review the changes.")
        else:
            print("Run with --fix to attempt to automatically fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
