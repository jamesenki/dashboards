"""
SQL Security Validator

This module provides functionality to validate SQL queries for potential
SQL injection vulnerabilities.
"""
import re
from typing import List, Pattern


class SQLSecurityValidator:
    """
    Validator for SQL queries to prevent SQL injection attacks.

    This class checks for common SQL injection patterns and validates that
    queries use proper parameterization.
    """

    def __init__(self):
        """Initialize the SQL security validator with common patterns to detect."""
        # Patterns that might indicate SQL injection attempts
        self.unsafe_patterns = [
            # SQL comments - might be used to bypass remaining logic
            r"--",
            r"/\*.*\*/",
            # SQL statement chaining - executing multiple statements
            r";.+",
            # Common SQL injection keywords
            r"\bOR\s+1\s*=\s*1\b",
            r"\bAND\s+1\s*=\s*1\b",
            r"\bDROP\s+TABLE\b",
            r"\bDELETE\s+FROM\b",
            r"\bINSERT\s+INTO\b",
            r"\bUPDATE\s+.*\s+SET\b",
            r"\bEXEC\b",
            r"\bXP_CMDSHELL\b",
            r"\bSYSTEM\b",
            r"\bUNION\s+SELECT\b",
            # Accessing system tables
            r"INFORMATION_SCHEMA",
            r"sysobjects",
            r"sys.tables",
        ]

        # Compiled regex patterns for performance
        self.compiled_unsafe_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.unsafe_patterns
        ]

        # Whitelist patterns that are always allowed
        self.whitelist_patterns: List[Pattern] = []

    def add_whitelist_pattern(self, pattern: str) -> None:
        """
        Add a pattern to the whitelist of allowed SQL patterns.

        Args:
            pattern: Regular expression pattern to whitelist
        """
        self.whitelist_patterns.append(re.compile(pattern))

    def is_unsafe(self, query: str) -> bool:
        """
        Check if a query might contain SQL injection attempts.

        Args:
            query: The SQL query to check

        Returns:
            True if the query appears unsafe, False otherwise

        Raises:
            TypeError: If the input is not a string
        """
        if not isinstance(query, str):
            raise TypeError("Query must be a string")

        # First check if query matches any whitelisted pattern
        for pattern in self.whitelist_patterns:
            if pattern.match(query):
                return False

        # Check if the query is using parameterized queries with placeholders
        has_placeholders = "?" in query

        # Parameterized queries are generally safe
        if has_placeholders:
            # But we still need to check for SQL injection through multiple statements
            if ";" in query and not (";" in query.split("--")[0] and "--" in query):
                return True

            # For parameterized queries, we consider them safe unless they have clear
            # indicators of trying to execute multiple commands
            return False

        # Non-parameterized queries need more scrutiny
        # If direct values in WHERE clause without parameters, it might be unsafe
        if "WHERE" in query.upper() or "HAVING" in query.upper():
            # Check for quotes which might indicate direct string embedding
            if "'" in query or '"' in query:
                return True

        # Check for known SQL injection patterns
        for unsafe_pattern in self.compiled_unsafe_patterns:
            if unsafe_pattern.search(query):
                return True

        return False

    def validate_query_params(self, params: List) -> bool:
        """
        Validate query parameters for potential SQL injection.

        Args:
            params: List of parameters to validate

        Returns:
            True if parameters are safe, False if potential SQL injection is detected
        """
        if not params:
            return True

        # When using parameterized queries, the parameters themselves don't need
        # to be as strictly validated since they'll be properly escaped by the
        # database connector. We're mostly looking for blatant SQL injection attempts.

        for param in params:
            # Only check string parameters
            if isinstance(param, str):
                # Check for obviously malicious patterns like trying to terminate statements
                if param.strip().endswith(";") and any(
                    keyword in param.upper()
                    for keyword in ["DROP", "DELETE", "INSERT", "UPDATE", "SELECT"]
                ):
                    return False

                # Check for attempts to comment out the rest of the query
                if "--" in param and any(
                    keyword in param.upper()
                    for keyword in ["DROP", "DELETE", "INSERT", "UPDATE", "SELECT"]
                ):
                    return False

                # Check for attempts to break out and start a new query
                if ";" in param and re.search(
                    r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)", param, re.IGNORECASE
                ):
                    return False

        return True
