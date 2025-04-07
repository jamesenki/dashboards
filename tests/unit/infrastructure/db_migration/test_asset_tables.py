#!/usr/bin/env python3
"""
Unit tests for asset database schema creation
"""
import os
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add the src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Import the module to test
from src.infrastructure.db_migration.create_asset_tables import create_tables

class TestAssetTables(unittest.TestCase):
    """Test suite for asset database schema creation"""
    
    @patch('src.infrastructure.db_migration.create_asset_tables.psycopg2')
    def test_create_tables_success(self, mock_psycopg2):
        """Test successful table creation"""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        # Call the function
        result = create_tables()
        
        # Check results
        self.assertTrue(result)
        mock_psycopg2.connect.assert_called_once()
        
        # Check that all required tables were created
        execute_calls = mock_cursor.execute.call_args_list
        table_creations = [
            call[0][0] for call in execute_calls 
            if "CREATE TABLE IF NOT EXISTS" in call[0][0]
        ]
        
        # Verify all tables were created
        self.assertIn("device_registry", str(table_creations))
        self.assertIn("device_capabilities", str(table_creations))
        self.assertIn("device_auth", str(table_creations))
        self.assertIn("location", str(table_creations))
        self.assertIn("device_location", str(table_creations))
        self.assertIn("maintenance_history", str(table_creations))
        self.assertIn("water_heater_metadata", str(table_creations))
        
        # Verify indexes were created
        index_creations = [
            call[0][0] for call in execute_calls 
            if "CREATE INDEX IF NOT EXISTS" in call[0][0]
        ]
        self.assertGreaterEqual(len(index_creations), 5)
    
    @patch('src.infrastructure.db_migration.create_asset_tables.psycopg2')
    def test_create_tables_database_error(self, mock_psycopg2):
        """Test error handling for database connection issues"""
        # Setup mock to raise exception
        mock_psycopg2.connect.side_effect = Exception("Mocked database error")
        
        # Call the function
        result = create_tables()
        
        # Check result is False due to error
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
