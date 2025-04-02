"""
Data Access Layer

This module provides a secure interface for database operations.
It includes protections against SQL injection and provides an abstraction
over the database connection.
"""
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

from src.security.sql_security import SQLSecurityValidator


class DataAccess:
    """
    Data Access Layer for database operations.

    This class provides methods to securely interact with the database,
    including protections against SQL injection.
    """

    def __init__(self, db_connection=None):
        """
        Initialize the data access layer.

        Args:
            db_connection: Database connection object
                          (defaults to creating a new SQLite connection)
        """
        self.connection = db_connection or sqlite3.connect(":memory:")
        self.sql_validator = SQLSecurityValidator()

    def execute(self, query: str, params: List = None) -> None:
        """
        Execute a SQL query with parameters.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Raises:
            ValueError: If the query is potentially unsafe
            TypeError: If query is not a string
        """
        if params is None:
            params = []

        # Validate query for SQL injection
        if self.sql_validator.is_unsafe(query):
            raise ValueError("Potentially unsafe SQL detected")

        # Validate parameters for SQL injection attempts
        if not self.sql_validator.validate_query_params(params):
            raise ValueError("SQL injection attempt detected in parameters")

        # Execute the query with parameters
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()

    def fetch_one(self, query: str, params: List = None) -> Optional[Dict[str, Any]]:
        """
        Execute a query and fetch a single row.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Returns:
            Single row as a dictionary or None if no results

        Raises:
            ValueError: If the query is potentially unsafe
        """
        if params is None:
            params = []

        # Validate query and parameters
        if self.sql_validator.is_unsafe(query):
            raise ValueError("Potentially unsafe SQL detected")

        if not self.sql_validator.validate_query_params(params):
            raise ValueError("SQL injection attempt detected in parameters")

        # Execute and fetch
        cursor = self.connection.cursor()
        cursor.execute(query, params)

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Fetch one row
        row = cursor.fetchone()
        if row:
            # Convert to dictionary
            return dict(zip(column_names, row))
        return None

    def fetch_all(self, query: str, params: List = None) -> List[Dict[str, Any]]:
        """
        Execute a query and fetch all rows.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Returns:
            List of rows as dictionaries

        Raises:
            ValueError: If the query is potentially unsafe
        """
        if params is None:
            params = []

        # Validate query and parameters
        if self.sql_validator.is_unsafe(query):
            raise ValueError("Potentially unsafe SQL detected")

        if not self.sql_validator.validate_query_params(params):
            raise ValueError("SQL injection attempt detected in parameters")

        # Execute and fetch
        cursor = self.connection.cursor()
        cursor.execute(query, params)

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Fetch all rows and convert to dictionaries
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(column_names, row)))
        return results

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Dictionary of column names and values

        Returns:
            ID of the inserted row

        Raises:
            ValueError: If the table name is potentially unsafe
        """
        # Validate table name (prevent SQL injection in table name)
        if self.sql_validator.is_unsafe(table):
            raise ValueError("Potentially unsafe table name")

        # Create parameterized query
        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[column] for column in columns]

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        # Execute the query
        cursor = self.connection.cursor()
        cursor.execute(query, values)
        self.connection.commit()

        # Return the ID of the inserted row
        return cursor.lastrowid

    def update(
        self, table: str, data: Dict[str, Any], condition: str, params: List
    ) -> int:
        """
        Update rows in a table.

        Args:
            table: Table name
            data: Dictionary of column names and values to update
            condition: WHERE condition (must use ? for parameters)
            params: Parameters for the condition

        Returns:
            Number of rows affected

        Raises:
            ValueError: If the query is potentially unsafe
        """
        # Validate table name and condition
        if self.sql_validator.is_unsafe(table) or self.sql_validator.is_unsafe(
            condition
        ):
            raise ValueError("Potentially unsafe SQL detected")

        # Validate parameters
        if not self.sql_validator.validate_query_params(params):
            raise ValueError("SQL injection attempt detected in parameters")

        # Create SET clause
        set_clause = ", ".join([f"{column} = ?" for column in data.keys()])
        values = list(data.values()) + params

        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"

        # Execute the query
        cursor = self.connection.cursor()
        cursor.execute(query, values)
        self.connection.commit()

        # Return number of rows affected
        return cursor.rowcount

    def delete(self, table: str, condition: str, params: List) -> int:
        """
        Delete rows from a table.

        Args:
            table: Table name
            condition: WHERE condition (must use ? for parameters)
            params: Parameters for the condition

        Returns:
            Number of rows affected

        Raises:
            ValueError: If the query is potentially unsafe
        """
        # Validate table name and condition
        if self.sql_validator.is_unsafe(table) or self.sql_validator.is_unsafe(
            condition
        ):
            raise ValueError("Potentially unsafe SQL detected")

        # Validate parameters
        if not self.sql_validator.validate_query_params(params):
            raise ValueError("SQL injection attempt detected in parameters")

        query = f"DELETE FROM {table} WHERE {condition}"

        # Execute the query
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()

        # Return number of rows affected
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
