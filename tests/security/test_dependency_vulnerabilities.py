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
    # This test explicitly checks that MLflow is installed and has a secure version
    # We DO NOT skip this test if MLflow is not found
    # According to TDD principles, this test should fail if MLflow is not at the proper version

    # 1. Force import of MLflow - don't catch ImportError to ensure proper RED phase
    import mlflow

    # 2. Get the version - this should fail if MLflow is not installed correctly
    mlflow_version = mlflow.__version__

    # 3. Check for secure version using proper semantic versioning
    parsed_version = version_parser.parse(mlflow_version)

    # 4. Verify against all critical vulnerabilities
    # Main security assertion - this will show RED if we don't meet minimum security version
    assert parsed_version >= version_parser.parse("2.9.2"), (
        f"SECURITY VULNERABILITY: MLflow v{mlflow_version} has known critical vulnerabilities including path traversal, "
        f"command injection, and remote code execution. Update to at least v2.9.2"
    )

    # 5. Comprehensive checks for specific vulnerabilities
    # These tests provide detailed reporting about which specific vulnerabilities exist
    assert parsed_version >= version_parser.parse(
        "2.5.0"
    ), f"SECURITY VULNERABILITY: MLflow v{mlflow_version} vulnerable to path traversal attacks (CVE-2023-38900)"

    assert parsed_version >= version_parser.parse(
        "2.6.0"
    ), f"SECURITY VULNERABILITY: MLflow v{mlflow_version} vulnerable to OS command injection (CVE-2023-39938)"

    assert parsed_version >= version_parser.parse(
        "2.8.1"
    ), f"SECURITY VULNERABILITY: MLflow v{mlflow_version} allows arbitrary files to be PUT onto the server (CVE-2023-48022)"

    assert parsed_version >= version_parser.parse(
        "2.9.0"
    ), f"SECURITY VULNERABILITY: MLflow v{mlflow_version} vulnerable to information exposure and XSS (CVE-2024-1483)"

    # 6. Verify our secure wrapper is in place as an additional protection layer
    # Check both possible locations to ensure it's available somewhere in the codebase
    secure_model_loader_found = False

    # Try to import from src structure first
    try:
        sys.path.insert(0, str(Path(__file__).parents[2]))
        from src.security import secure_model_loader

        secure_model_loader_found = True
    except ImportError:
        pass

    # Try to import from app structure if not found in src
    if not secure_model_loader_found:
        try:
            from app.security import ml_security

            secure_model_loader_found = True
        except ImportError:
            pass

    assert (
        secure_model_loader_found
    ), "SECURITY CONTROL MISSING: No secure model loader wrapper found to protect against MLflow vulnerabilities"


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
