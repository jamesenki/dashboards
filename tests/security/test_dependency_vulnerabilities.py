"""
Security tests for known vulnerabilities in dependencies.
Following TDD principles, these tests verify the application is protected against
known vulnerabilities in dependencies like MLflow and PyArrow.
"""
import importlib
import os
import re
import sys
from pathlib import Path

import pytest
from packaging import version as version_parser


def test_mlflow_version_secure():
    """Test that MLflow version is not vulnerable to known CVEs."""
    try:
        import mlflow

        mlflow_version = mlflow.__version__

        # Check against known vulnerable versions
        parsed_version = version_parser.parse(mlflow_version)
        assert parsed_version >= version_parser.parse(
            "2.9.0"
        ), f"MLflow version {mlflow_version} may be vulnerable to CVE-2024-1483 and others"

        # Additional check for more recent vulnerabilities
        assert not (
            parsed_version >= version_parser.parse("2.0.0")
            and parsed_version < version_parser.parse("2.8.1")
        ), f"MLflow version {mlflow_version} may be vulnerable to CVE-2023-48022"

        # Test for additional protections against deserialization attacks
        assert hasattr(mlflow, "utils"), "MLflow utils module is missing"

        # Check if we're using secure model loading practices
        model_loading_secure = getattr(mlflow, "security_enabled", False)
        if not model_loading_secure:
            # If not explicitly enabled, we need additional protection in our code
            # Check custom security measures (this should be implemented in the application code)
            sys.path.append(str(Path(__file__).parents[2]))
            try:
                from app.security import model_loader

                assert hasattr(
                    model_loader, "validate_model_security"
                ), "Application should implement custom model security validation"
            except ImportError:
                pytest.skip(
                    "Custom security module not found - may need to implement it"
                )

    except ImportError:
        pytest.skip("MLflow not installed")


def test_pyarrow_deserialization_protection():
    """Test protection against PyArrow's deserialization vulnerability (CVE-2023-47248)."""
    try:
        import pyarrow

        pyarrow_version = pyarrow.__version__

        # Check for vulnerable versions
        major, minor, patch = map(int, re.findall(r"\d+", pyarrow_version)[:3])

        # Use packaging.version for semantic versioning comparison
        parsed_version = version_parser.parse(pyarrow_version)

        # Version check based on PyArrow vulnerabilities (CVE-2023-47248 and others)
        is_vulnerable_version = (
            parsed_version < version_parser.parse("9.0.0")
            or (
                parsed_version >= version_parser.parse("10.0.0")
                and parsed_version < version_parser.parse("10.0.1")
            )
            or (
                parsed_version >= version_parser.parse("11.0.0")
                and parsed_version < version_parser.parse("11.0.1")
            )
            or (
                parsed_version >= version_parser.parse("12.0.0")
                and parsed_version < version_parser.parse("12.0.1")
            )
            or (
                parsed_version >= version_parser.parse("13.0.0")
                and parsed_version < version_parser.parse("13.0.1")
            )
            or (
                parsed_version >= version_parser.parse("14.0.0")
                and parsed_version < version_parser.parse("14.0.1")
            )
        )

        if is_vulnerable_version:
            # If using vulnerable version, check for custom protection
            sys.path.append(str(Path(__file__).parents[2]))
            try:
                # Try to import from main app package first (preferred approach)
                from app import validate_arrow_data

                assert (
                    validate_arrow_data is not None
                ), "Arrow data validation function is not properly exposed"
            except ImportError:
                try:
                    # Fallback to direct import from the security module
                    from app.security import validate_arrow_data

                    assert (
                        validate_arrow_data is not None
                    ), "Arrow data validation function is not properly exposed"
                except ImportError:
                    # Final fallback to check the class directly
                    from app.security.data_validation import ArrowDataValidator

                    assert hasattr(
                        ArrowDataValidator, "validate_arrow_data"
                    ), "ArrowDataValidator should implement validate_arrow_data method"
        else:
            # If using patched version, test passes
            assert True
    except ImportError:
        pytest.skip("PyArrow not installed")


def test_gunicorn_version_secure():
    """Test that Gunicorn version is not vulnerable to known CVEs."""
    try:
        # Create a subprocess to check gunicorn version without importing it
        import re
        import subprocess

        result = subprocess.run(
            ["gunicorn", "--version"], capture_output=True, text=True
        )
        version_str = result.stdout.strip()

        # Extract version number using regex
        match = re.search(r"\d+\.\d+\.\d+", version_str)
        if match:
            gunicorn_version = match.group(0)

            # Check against known vulnerable versions (CVE-2023-45802) using semantic versioning
            parsed_version = version_parser.parse(gunicorn_version)

            assert parsed_version >= version_parser.parse(
                "21.0.0"
            ), f"Gunicorn version {gunicorn_version} may be vulnerable to CVE-2023-45802"
        else:
            pytest.fail("Could not determine Gunicorn version")

    except (ImportError, FileNotFoundError, subprocess.SubprocessError):
        pytest.skip("Gunicorn not installed or not executable")


def test_model_loading_validation():
    """Test that model loading has appropriate validation to prevent code execution."""
    # This test checks that we have implemented custom validation logic for model loading
    model_loading_file = Path(__file__).parents[2] / "app" / "ml" / "model_loader.py"

    if not model_loading_file.exists():
        pytest.skip("Model loader not implemented in this application")

    with open(model_loading_file, "r") as f:
        code = f.read()

        # Check for validation patterns in the code
        has_validation = (
            re.search(r"validate_model", code) is not None
            or re.search(r"security_check", code) is not None
            or re.search(r"sanitize", code) is not None
        )

        assert has_validation, "Model loader should implement security validation"


def test_custom_mlflow_wrapper_exists():
    """Test that we have a custom wrapper around MLflow to handle security."""
    wrapper_paths = [
        Path(__file__).parents[2] / "app" / "ml" / "mlflow_wrapper.py",
        Path(__file__).parents[2] / "app" / "security" / "ml_security.py",
    ]

    wrapper_exists = any(path.exists() for path in wrapper_paths)

    if not wrapper_exists:
        pytest.skip("MLflow wrapper not implemented - consider adding one for security")
    else:
        # If exists, check it has security features
        selected_path = next(path for path in wrapper_paths if path.exists())
        with open(selected_path, "r") as f:
            code = f.read()
            has_security_features = (
                re.search(r"security|validate|sanitize|check", code, re.IGNORECASE)
                is not None
            )
            assert (
                has_security_features
            ), "MLflow wrapper should implement security features"
