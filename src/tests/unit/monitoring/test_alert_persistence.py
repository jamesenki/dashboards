import unittest
import pytest
from unittest.mock import MagicMock, patch
import sqlite3
import os
import json
import uuid
from datetime import datetime
import asyncio

from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.monitoring.alerts import AlertRule, AlertSeverity


class TestAlertPersistence(unittest.TestCase):
    """Tests for persisting and deleting alert configurations."""

    def setUp(self):
        """Set up test environment with a test database."""
        # Create an in-memory SQLite database for testing
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # Create the necessary tables for alert rules
        self.cursor.execute('''
        CREATE TABLE alert_rules (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            threshold REAL NOT NULL,
            operator TEXT NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            is_active INTEGER DEFAULT 1,
            description TEXT
        )
        ''')
        self.conn.commit()
        
        # Mock the database connection in the service
        self.db_mock = MagicMock()
        self.db_mock.execute.side_effect = self.mock_execute
        self.db_mock.fetch_all.side_effect = self.mock_fetch_all
        
        # Create the service with the mocked database
        self.service = ModelMonitoringService(db=self.db_mock)
    
    def mock_execute(self, query, params=None):
        """Mock the execute method of the database."""
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        self.conn.commit()
        return True
    
    def mock_fetch_all(self, query, params=None):
        """Mock the fetch_all method of the database."""
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def tearDown(self):
        """Clean up after tests."""
        self.cursor.close()
        self.conn.close()
    
    @pytest.mark.asyncio
    async def test_create_and_persist_alert_rule(self):
        """Test creating an alert rule and ensuring it's persisted."""
        # Create a test alert rule
        model_id = "test-model"
        model_version = "1.0"
        rule_name = "Test Alert"
        metric_name = "accuracy"
        threshold = 0.9
        operator = "<"
        severity = AlertSeverity.HIGH
        description = "Test alert description"
        
        # Create the rule with the correct parameter order
        rule_id = await self.service.create_alert_rule(
            model_id, 
            model_version, 
            rule_name, 
            metric_name, 
            threshold, 
            operator, 
            severity, 
            description
        )
        
        # Verify the rule was created with an ID
        self.assertIsNotNone(rule_id)
        
        # Retrieve the rules and verify our rule is there
        rules = await self.service.get_alert_rules(model_id, model_version)
        
        # Check persistence
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["rule_name"], rule_name)
        self.assertEqual(rules[0]["metric_name"], metric_name)
        self.assertEqual(rules[0]["threshold"], threshold)
        self.assertEqual(rules[0]["operator"], operator)
        self.assertEqual(rules[0]["severity"], severity.value)
        self.assertEqual(rules[0]["description"], description)
        
        # Verify rule persists after service recreation
        new_service = ModelMonitoringService(db=self.db_mock)
        rules_after_recreation = await new_service.get_alert_rules(model_id, model_version)
        self.assertEqual(len(rules_after_recreation), 1)
        self.assertEqual(rules_after_recreation[0]["id"], rule_id)
    
    @pytest.mark.asyncio
    async def test_delete_alert_rule(self):
        """Test deleting an alert rule."""
        # Create a test alert rule
        model_id = "test-model"
        model_version = "1.0"
        rule_name = "Test Alert"
        metric_name = "accuracy"
        threshold = 0.9
        operator = "<"
        severity = AlertSeverity.HIGH
        description = "Test alert description"
        
        # Create the rule with the correct parameter order
        rule_id = await self.service.create_alert_rule(
            model_id, 
            model_version, 
            rule_name, 
            metric_name, 
            threshold, 
            operator, 
            severity, 
            description
        )
        
        # Verify the rule was created
        rules_before = await self.service.get_alert_rules(model_id, model_version)
        self.assertEqual(len(rules_before), 1)
        
        # Delete the rule
        await self.service.delete_alert_rule(rule_id)
        
        # Verify the rule was deleted
        rules_after = await self.service.get_alert_rules(model_id, model_version)
        self.assertEqual(len(rules_after), 0)
        
        # Verify deletion persists after service recreation
        new_service = ModelMonitoringService(db=self.db_mock)
        rules_after_recreation = await new_service.get_alert_rules(model_id, model_version)
        self.assertEqual(len(rules_after_recreation), 0)
