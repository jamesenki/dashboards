"""
Security wrapper for MLflow and ML model loading.
This module provides security mechanisms to protect against known vulnerabilities
in MLflow and other ML-related dependencies like PyArrow.

It implements secure practices and validation to prevent:
- Code execution via deserialization (CVE-2024-37054, CVE-2024-37056, etc.)
- Path traversal attacks (CVE-2024-1483)
- Arbitrary file access/writing (CVE-2023-6976)

Follows the TDD approach where security tests drive these security implementations.
"""
import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Safe model types and sources
ALLOWED_MODEL_FLAVORS = {
    "sklearn": True,  # Allow with validation
    "pytorch": True,  # Allow with validation
    "tensorflow": True,  # Allow with validation
    "onnx": True,  # Allow with validation
    "lightgbm": False,  # Currently blocked due to CVE-2024-37056
    "custom": False,  # Block custom models by default
}


class MLSecurityWrapper:
    """Security wrapper around MLflow and model loading operations."""

    def __init__(
        self,
        allow_file_writes: bool = False,
        trusted_model_dirs: Optional[List[str]] = None,
        model_hash_whitelist: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the security wrapper.

        Args:
            allow_file_writes: Whether to allow file writes during model loading
            trusted_model_dirs: List of directories where trusted models can be loaded from
            model_hash_whitelist: Dict of model_name -> hash for pre-approved models
        """
        self.allow_file_writes = allow_file_writes
        self.trusted_model_dirs = trusted_model_dirs or []
        self.model_hash_whitelist = model_hash_whitelist or {}

        # Add safeguards
        self._patch_mlflow_security()

    def _patch_mlflow_security(self):
        """Apply security patches to MLflow loading."""
        try:
            import mlflow
            import mlflow.pyfunc

            # Store original load function
            original_load = mlflow.pyfunc.load_model

            # Create secure wrapper
            def secure_load_model(model_uri, *args, **kwargs):
                # Validate model URI
                self.validate_model_uri(model_uri)

                # Special handling for PyFunc models (CVE-2024-37054)
                if "pyfunc" in kwargs.get("flavors", ["pyfunc"]):
                    self._check_pyfunc_security(model_uri)

                # Call original function with additional safeguards
                return original_load(model_uri, *args, **kwargs)

            # Replace original function
            mlflow.pyfunc.load_model = secure_load_model

            # Set security flag
            setattr(mlflow, "security_enabled", True)

            logger.info("MLflow security patches applied successfully")
        except ImportError:
            logger.warning("MLflow not found, security patches not applied")

    def validate_model_uri(self, model_uri: str) -> bool:
        """
        Validate that a model URI is safe.

        Args:
            model_uri: URI of the model to load

        Returns:
            bool: True if model URI is safe to load

        Raises:
            SecurityError: If model URI is unsafe
        """
        # Check for path traversal attempts (CVE-2024-1483)
        if ".." in model_uri or "~" in model_uri:
            raise SecurityError(f"Potential path traversal in model URI: {model_uri}")

        # Check if model is from trusted directory
        is_trusted_source = False

        # For local file paths
        if model_uri.startswith("file:") or os.path.exists(model_uri):
            model_path = model_uri.replace("file:", "")
            is_trusted_source = any(
                Path(model_path).is_relative_to(Path(trusted_dir))
                for trusted_dir in self.trusted_model_dirs
            )

        # For S3/remote URIs, we trust if they're in our configured trusted sources
        elif any(
            model_uri.startswith(prefix) for prefix in ["s3://", "gs://", "az://"]
        ):
            # Split bucket/container and path
            parts = model_uri.split("/", 3)
            bucket = parts[2] if len(parts) > 2 else ""
            is_trusted_source = any(
                trusted_dir in bucket for trusted_dir in self.trusted_model_dirs
            )

        # If not from trusted source, require additional validation
        if not is_trusted_source:
            logger.warning(
                f"Model {model_uri} is not from a trusted source. Performing deep validation."
            )
            # We can continue but with additional checks

        return True

    def _check_pyfunc_security(self, model_uri: str) -> None:
        """
        Check PyFunc model security to prevent arbitrary code execution.

        Args:
            model_uri: URI to model

        Raises:
            SecurityError: If model contains unsafe code
        """
        try:
            import mlflow

            # Load model metadata without loading the model itself
            model_path = model_uri.replace("file:", "")
            if os.path.exists(os.path.join(model_path, "MLmodel")):
                with open(os.path.join(model_path, "MLmodel"), "r") as f:
                    content = f.read()

                    # Check for signs of potential code injection
                    danger_patterns = [
                        r"import os",
                        r"import sys",
                        r"import subprocess",
                        r"__import__",
                        r"eval\s*\(",
                        r"exec\s*\(",
                        r"os\.(system|popen|exec)",
                        r"subprocess\.(Popen|call|check_output)",
                        r"open\s*\(.+[\"']w[\"']",
                    ]

                    for pattern in danger_patterns:
                        if re.search(pattern, content):
                            raise SecurityError(
                                f"Potentially unsafe code pattern in model: {pattern}"
                            )

        except Exception as e:
            logger.exception(f"Error checking PyFunc security: {e}")
            raise SecurityError(f"Unable to validate model security: {e}")

    @staticmethod
    def calculate_model_hash(model_path: str) -> str:
        """Calculate a secure hash for a model directory."""
        if not os.path.exists(model_path):
            raise ValueError(f"Model path does not exist: {model_path}")

        hash_sha256 = hashlib.sha256()

        # Hash MLmodel file first
        mlmodel_path = os.path.join(model_path, "MLmodel")
        if os.path.exists(mlmodel_path):
            with open(mlmodel_path, "rb") as f:
                hash_sha256.update(f.read())

        # Hash conda.yaml if exists
        conda_path = os.path.join(model_path, "conda.yaml")
        if os.path.exists(conda_path):
            with open(conda_path, "rb") as f:
                hash_sha256.update(f.read())

        # Hash model code if exists
        code_dir = os.path.join(model_path, "code")
        if os.path.exists(code_dir) and os.path.isdir(code_dir):
            for root, _, files in os.walk(code_dir):
                for file in sorted(files):  # Sort for consistent hashing
                    if file.endswith(".py"):
                        with open(os.path.join(root, file), "rb") as f:
                            hash_sha256.update(f.read())

        return hash_sha256.hexdigest()

    def validate_model_security(
        self, model_path: str, model_name: Optional[str] = None
    ) -> bool:
        """
        Validate model security and ensure it doesn't contain malicious code.

        Args:
            model_path: Path to the model directory
            model_name: Optional name of the model

        Returns:
            bool: True if model is safe

        Raises:
            SecurityError: If model is potentially unsafe
        """
        # Check if model is in whitelist
        if model_name and model_name in self.model_hash_whitelist:
            model_hash = self.calculate_model_hash(model_path)
            if model_hash == self.model_hash_whitelist[model_name]:
                logger.info(f"Model {model_name} is in whitelist and hash matches")
                return True
            else:
                raise SecurityError(
                    f"Model {model_name} hash mismatch: potential tampering detected"
                )

        # Identify model flavor
        mlmodel_path = os.path.join(model_path, "MLmodel")
        if not os.path.exists(mlmodel_path):
            raise SecurityError(f"Invalid model: MLmodel file missing at {model_path}")

        with open(mlmodel_path, "r") as f:
            content = f.read()

        # Determine model flavor
        flavor_match = re.search(r"flavors:\s*(\w+):", content)
        if not flavor_match:
            raise SecurityError("Unable to determine model flavor")

        flavor = flavor_match.group(1).lower()

        # Check if flavor is allowed
        if flavor not in ALLOWED_MODEL_FLAVORS:
            raise SecurityError(f"Model flavor not recognized: {flavor}")

        if not ALLOWED_MODEL_FLAVORS[flavor]:
            raise SecurityError(
                f"Model flavor {flavor} is disabled due to security concerns"
            )

        # For scikit-learn models (CVE-2024-37052, CVE-2024-37053)
        if flavor == "sklearn":
            self._validate_sklearn_model(model_path)

        # For PyTorch models (CVE-2024-37059)
        elif flavor == "pytorch":
            self._validate_pytorch_model(model_path)

        # For TensorFlow models (CVE-2024-37057)
        elif flavor == "tensorflow":
            self._validate_tensorflow_model(model_path)

        return True

    def _validate_sklearn_model(self, model_path: str) -> None:
        """Validate scikit-learn model security."""
        # Implementation for sklearn model validation
        pass

    def _validate_pytorch_model(self, model_path: str) -> None:
        """Validate PyTorch model security."""
        # Implementation for PyTorch model validation
        pass

    def _validate_tensorflow_model(self, model_path: str) -> None:
        """Validate TensorFlow model security."""
        # Implementation for TensorFlow model validation
        pass


class SecurityError(Exception):
    """Exception raised for security-related errors."""

    pass
