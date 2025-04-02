"""
Tests for SQL injection prevention in database operations.

These tests verify that our data access layer properly protects
against SQL injection attacks.
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from unittest.mock import MagicMock

from src.db.data_access import DataAccess
from src.security.sql_security import SQLSecurityValidator


class TestSQLInjectionPrevention:
    """Test suite for SQL injection prevention."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.connection_mock = MagicMock()
        self.cursor_mock = MagicMock()
        self.connection_mock.cursor.return_value = self.cursor_mock

        # Create a DataAccess instance with mocked connection
        self.data_access = DataAccess(db_connection=self.connection_mock)

        # Create a security validator
        self.sql_validator = SQLSecurityValidator()

    def test_detect_unsafe_sql_query(self):
        """Test that unsafe SQL queries are detected."""
        # Arrange
        unsafe_queries = [
            "SELECT * FROM users WHERE username = 'admin' OR 1=1;--'",
            "UPDATE users SET password = 'hacked' WHERE id = 1 OR 1=1",
            f"DELETE FROM logs WHERE id = 1; DROP TABLE users;--",
            "INSERT INTO users (username) VALUES ('user'); INSERT INTO admin_users VALUES (1, 'attacker')",
            "SELECT * FROM users WHERE username = ''; EXEC xp_cmdshell('net user')",
        ]

        # Act & Assert
        for query in unsafe_queries:
            assert self.sql_validator.is_unsafe(
                query
            ), f"Failed to detect unsafe query: {query}"

    def test_safe_sql_queries(self):
        """Test that safe parameterized SQL queries are allowed."""
        # Arrange
        safe_queries = [
            "SELECT * FROM users WHERE username = ?",
            "UPDATE users SET password = ? WHERE id = ?",
            "DELETE FROM logs WHERE id = ?",
            "INSERT INTO users (username, email) VALUES (?, ?)",
            "SELECT * FROM products WHERE category = ? AND price > ?",
        ]

        # Act & Assert
        for query in safe_queries:
            assert not self.sql_validator.is_unsafe(
                query
            ), f"Incorrectly flagged safe query: {query}"

    def test_data_access_execute_query_with_params(self):
        """Test that DataAccess properly parameterizes queries."""
        # Arrange
        query = "SELECT * FROM users WHERE id = ?"
        params = (1,)

        # Act
        self.data_access.execute(query, params)

        # Assert
        self.cursor_mock.execute.assert_called_once_with(query, params)

    def test_data_access_rejects_unsafe_direct_sql(self):
        """Test that DataAccess rejects unsafe direct SQL execution."""
        # Arrange
        unsafe_query = "SELECT * FROM users WHERE username = 'admin' OR 1=1;--'"

        # Act & Assert
        with pytest.raises(ValueError, match="Potentially unsafe SQL"):
            self.data_access.execute(unsafe_query, [])

    def test_sql_security_validator_non_string_input(self):
        """Test SQLSecurityValidator handles non-string inputs correctly."""
        # Arrange
        non_string_inputs = [
            None,
            123,
            {"query": "SELECT *"},
            ["SELECT *"],
        ]

        # Act & Assert
        for input_val in non_string_inputs:
            with pytest.raises(TypeError):
                self.sql_validator.is_unsafe(input_val)

    def test_data_access_with_sql_injection_attempt(self):
        """Test that attempts to perform SQL injection are caught."""
        # Arrange - Payload in parameter that tries to break out
        malicious_param = "1; DROP TABLE users;--"

        # Act
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            self.data_access.execute(
                "SELECT * FROM users WHERE id = ?", [malicious_param]
            )

    def test_parameterized_query_properly_escapes(self):
        """Test that parameters are properly escaped in parameterized queries."""
        # Arrange
        query = "SELECT * FROM users WHERE username = ?"
        special_chars_param = "user'--name"  # Contains SQL meaningful characters

        # Act
        self.data_access.execute(query, [special_chars_param])

        # Assert
        self.cursor_mock.execute.assert_called_once_with(query, [special_chars_param])
        # In real parameterized queries, the database driver would properly escape this

    def test_whitelist_query_patterns(self):
        """Test that whitelisted query patterns are allowed."""
        # Arrange
        # Define some patterns that should always be allowed
        self.sql_validator.add_whitelist_pattern(
            r"^SELECT \* FROM allowed_table WHERE id = \?$"
        )

        # Act & Assert
        assert not self.sql_validator.is_unsafe(
            "SELECT * FROM allowed_table WHERE id = ?"
        )
