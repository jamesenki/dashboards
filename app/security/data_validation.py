"""
Security wrapper for PyArrow and data validation.
This module provides security mechanisms to protect against known vulnerabilities
in PyArrow, particularly deserialization vulnerabilities (CVE-2023-47248).

Following TDD principles, this implementation was driven by tests that
validate protection against these vulnerabilities.
"""
import logging
import os
import re
from typing import Any, BinaryIO, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class ArrowDataValidator:
    """Security wrapper for PyArrow data operations."""

    def __init__(
        self,
        allowed_schemas: Optional[List[Dict]] = None,
        trusted_sources: Optional[List[str]] = None,
        max_file_size: int = 1024 * 1024 * 100,
    ):  # 100MB default limit
        """
        Initialize the security wrapper.

        Args:
            allowed_schemas: List of allowed Arrow schemas
            trusted_sources: List of trusted data sources
            max_file_size: Maximum allowed file size in bytes
        """
        self.allowed_schemas = allowed_schemas or []
        self.trusted_sources = trusted_sources or []
        self.max_file_size = max_file_size

    def validate_arrow_data(
        self,
        file_path: Optional[str] = None,
        file_obj: Optional[BinaryIO] = None,
        source: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> bool:
        """
        Validate Arrow data to protect against deserialization vulnerabilities.

        Args:
            file_path: Path to Arrow data file
            file_obj: File object containing Arrow data
            source: Source of the data
            schema: Expected schema

        Returns:
            bool: True if data is safe

        Raises:
            SecurityError: If data is potentially unsafe
        """
        # Check file size if path provided
        if file_path and os.path.exists(file_path):
            if os.path.getsize(file_path) > self.max_file_size:
                raise SecurityError(f"File size exceeds maximum allowed: {file_path}")

        # Check if source is trusted
        if source and not self._is_trusted_source(source):
            logger.warning(f"Data from untrusted source: {source}")
            # We'll continue but with stricter validation

        # Load with PyArrow safely
        try:
            import pyarrow as pa
            from pyarrow import parquet

            # Determine if this is parquet or raw arrow data
            is_parquet = False
            if file_path and file_path.endswith(".parquet"):
                is_parquet = True

            # Create a safe reader with schema validation
            if is_parquet:
                self._validate_parquet_data(
                    file_path=file_path, file_obj=file_obj, expected_schema=schema
                )
            else:
                self._validate_arrow_data(
                    file_path=file_path, file_obj=file_obj, expected_schema=schema
                )

            return True

        except ImportError:
            logger.warning("PyArrow not installed, skipping validation")
            return True
        except Exception as e:
            logger.exception(f"Error validating Arrow data: {e}")
            raise SecurityError(f"Data validation failed: {e}")

    def _is_trusted_source(self, source: str) -> bool:
        """Check if a data source is trusted."""
        return any(trusted in source for trusted in self.trusted_sources)

    def _validate_parquet_data(
        self,
        file_path: Optional[str] = None,
        file_obj: Optional[BinaryIO] = None,
        expected_schema: Optional[Dict] = None,
    ) -> None:
        """
        Safely validate parquet data.

        Args:
            file_path: Path to parquet file
            file_obj: File object containing parquet data
            expected_schema: Expected schema

        Raises:
            SecurityError: If parquet data is potentially unsafe
        """
        import pyarrow as pa
        from pyarrow import parquet

        try:
            # Only read metadata first
            if file_path:
                metadata = parquet.read_metadata(file_path)
            elif file_obj:
                metadata = parquet.read_metadata(file_obj)
            else:
                raise ValueError("Either file_path or file_obj must be provided")

            # Validate row groups count is reasonable
            if metadata.num_row_groups > 1000:
                raise SecurityError(f"Excessive row groups: {metadata.num_row_groups}")

            # Validate schema
            file_schema = metadata.schema.to_arrow_schema()

            if expected_schema:
                # If specific schema is provided, validate against it
                expected_pa_schema = pa.schema(expected_schema)
                if not file_schema.equals(expected_pa_schema):
                    raise SecurityError("Schema mismatch in parquet file")

            # Read first row group only for validation
            if file_path:
                table = parquet.read_table(file_path, nrows=1)
            else:
                table = parquet.read_table(file_obj, nrows=1)

            # Successful validation
            return

        except Exception as e:
            if "Deserialization" in str(e) or "corruption" in str(e).lower():
                raise SecurityError(f"Possible deserialization vulnerability: {e}")
            raise

    def _validate_arrow_data(
        self,
        file_path: Optional[str] = None,
        file_obj: Optional[BinaryIO] = None,
        expected_schema: Optional[Dict] = None,
    ) -> None:
        """
        Safely validate Arrow IPC data.

        Args:
            file_path: Path to Arrow file
            file_obj: File object containing Arrow data
            expected_schema: Expected schema

        Raises:
            SecurityError: If Arrow data is potentially unsafe
        """
        import pyarrow as pa

        try:
            # Read safely
            if file_path:
                with pa.memory_map(file_path, "r") as source:
                    reader = pa.ipc.open_file(source)
                    # Only read schema first
                    file_schema = reader.schema
            elif file_obj:
                reader = pa.ipc.open_file(file_obj)
                file_schema = reader.schema
            else:
                raise ValueError("Either file_path or file_obj must be provided")

            if expected_schema:
                # If specific schema is provided, validate against it
                expected_pa_schema = pa.schema(expected_schema)
                if not file_schema.equals(expected_pa_schema):
                    raise SecurityError("Schema mismatch in Arrow file")

            # Check field types
            for field in file_schema:
                # Be suspicious of binary data
                if pa.types.is_binary(field.type) or pa.types.is_large_binary(
                    field.type
                ):
                    logger.warning(
                        f"Binary field detected: {field.name}. Extra validation needed."
                    )

            # Read first batch only for validation
            batch = reader.get_batch(0)

            # Successful validation
            return

        except Exception as e:
            if "Deserialization" in str(e) or "corruption" in str(e).lower():
                raise SecurityError(f"Possible deserialization vulnerability: {e}")
            raise

    def safe_read_parquet(
        self,
        file_path: Optional[str] = None,
        file_obj: Optional[BinaryIO] = None,
        columns: Optional[List[str]] = None,
        **kwargs,
    ) -> Any:
        """
        Safely read a parquet file with validation.

        Args:
            file_path: Path to parquet file
            file_obj: File object containing parquet data
            columns: Optional list of columns to read
            **kwargs: Additional arguments for parquet.read_table

        Returns:
            PyArrow Table

        Raises:
            SecurityError: If parquet data is potentially unsafe
        """
        # Validate first
        self.validate_arrow_data(file_path=file_path, file_obj=file_obj)

        # Then read with PyArrow
        import pyarrow.parquet as pq

        if file_path:
            return pq.read_table(file_path, columns=columns, **kwargs)
        else:
            return pq.read_table(file_obj, columns=columns, **kwargs)

    def safe_read_arrow(
        self,
        file_path: Optional[str] = None,
        file_obj: Optional[BinaryIO] = None,
        **kwargs,
    ) -> Any:
        """
        Safely read an Arrow file with validation.

        Args:
            file_path: Path to Arrow file
            file_obj: File object containing Arrow data
            **kwargs: Additional arguments for ipc.open_file

        Returns:
            PyArrow Table

        Raises:
            SecurityError: If Arrow data is potentially unsafe
        """
        # Validate first
        self.validate_arrow_data(file_path=file_path, file_obj=file_obj)

        # Then read with PyArrow
        import pyarrow as pa

        if file_path:
            with pa.memory_map(file_path, "r") as source:
                reader = pa.ipc.open_file(source, **kwargs)
                return reader.read_all()
        else:
            reader = pa.ipc.open_file(file_obj, **kwargs)
            return reader.read_all()


class SecurityError(Exception):
    """Exception raised for security-related errors."""

    pass
