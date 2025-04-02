"""
Tests for the ModelMonitoringService.

Following TDD principles, these tests define the expected behavior
of the model monitoring service before implementation.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.monitoring.alerts import AlertRule, AlertSeverity
from src.monitoring.metrics import MetricType, ModelMetric

# Import the service (to be implemented)
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestModelMonitoringService:
    """Test suite for the ModelMonitoringService."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock dependencies
        self.db_mock = MagicMock()
        self.notification_service_mock = MagicMock()

        # Create service instance with mocked dependencies
        self.service = ModelMonitoringService(
            db=self.db_mock, notification_service=self.notification_service_mock
        )

        # Test data
        self.model_id = str(uuid.uuid4())
        self.model_version = "1.0.0"
        self.metric_data = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86,
            "roc_auc": 0.91,
        }

    def test_init(self):
        """Test service initialization."""
        assert self.service is not None
        assert self.service.db == self.db_mock
        assert self.service.notification_service == self.notification_service_mock

    def test_record_model_metrics(self):
        """Test recording metrics for a model."""
        # Arrange
        invoke_time = datetime.now()

        # Act
        self.service.record_model_metrics(
            model_id=self.model_id,
            model_version=self.model_version,
            metrics=self.metric_data,
            invoke_time=invoke_time,
        )

        # Assert
        self.db_mock.execute.assert_called_once()

    def test_get_model_metrics_history(self):
        """Test retrieving metric history for a model."""
        # Arrange
        metric_name = "accuracy"
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        # Mock the database response
        expected_metrics = [
            {"timestamp": datetime.now().isoformat(), "value": 0.92},
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "value": 0.91,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "value": 0.93,
            },
        ]
        self.db_mock.fetch_all.return_value = expected_metrics

        # Act
        metrics = self.service.get_model_metrics_history(
            model_id=self.model_id,
            model_version=self.model_version,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
        )

        # Assert
        assert metrics == expected_metrics
        self.db_mock.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_alert_rule(self):
        """Test creating an alert rule for metric thresholds."""
        # Arrange
        rule_name = "Accuracy Drop Alert"
        metric_name = "accuracy"
        threshold = 0.85
        operator = "<"  # Alert when accuracy falls below threshold
        severity = AlertSeverity.HIGH

        # Act
        rule_id = await self.service.create_alert_rule(
            model_id=self.model_id,
            model_version=self.model_version,
            rule_name=rule_name,
            metric_name=metric_name,
            threshold=threshold,
            operator=operator,
            severity=severity,
        )

        # Assert
        assert rule_id is not None
        self.db_mock.execute.assert_called_once()

    def test_check_for_alerts(self):
        """Test checking if metrics trigger alert rules."""
        # Arrange - explicitly disable mock data to test database path
        self.service.use_mock_data = False

        # Create a proper mock for the metrics_repository
        metrics_repo_mock = MagicMock()
        self.service.metrics_repository = metrics_repo_mock

        # Mock the alert rules
        alert_rules = [
            {
                "id": str(uuid.uuid4()),
                "model_id": self.model_id,
                "metric_name": "accuracy",
                "threshold": 0.90,
                "operator": "<",
                "severity": AlertSeverity.HIGH.value,
                "is_active": True,
            }
        ]

        # Mock the repository to return our test rules
        metrics_repo_mock.get_alert_rules.return_value = alert_rules

        # Mock the metrics history to trigger the alert
        metrics_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "value": 0.85,
            }  # Below threshold of 0.90
        ]
        metrics_repo_mock.get_model_metrics_history.return_value = metrics_history

        # Act
        # We need to provide all required parameters: model_id, model_version, and metrics
        test_metrics = {"accuracy": 0.85}  # Below threshold of 0.90
        triggered_alerts = self.service._check_for_alerts_sync(
            self.model_id, "1.0", test_metrics
        )

        # Assert
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0]["rule_id"] == alert_rules[0]["id"]
        assert triggered_alerts[0]["severity"] == AlertSeverity.HIGH.value

    def test_no_alerts_when_threshold_not_breached(self):
        """Test that no alerts are triggered when thresholds are not breached."""
        # Arrange
        self.service.use_mock_data = False

        # Create a proper mock for the metrics_repository
        metrics_repo_mock = MagicMock()
        self.service.metrics_repository = metrics_repo_mock

        # Mock the alert rules
        alert_rules = [
            {
                "id": str(uuid.uuid4()),
                "model_id": self.model_id,
                "metric_name": "accuracy",
                "threshold": 0.90,
                "operator": "<",
                "severity": AlertSeverity.HIGH.value,
                "is_active": True,
            }
        ]

        # Mock the repository to return our test rules
        metrics_repo_mock.get_alert_rules.return_value = alert_rules

        # Mock the metrics history to NOT trigger the alert (above threshold)
        metrics_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "value": 0.95,
            }  # Above threshold of 0.90
        ]
        metrics_repo_mock.get_model_metrics_history.return_value = metrics_history

        # Act
        # We need to provide all required parameters: model_id, model_version, and metrics
        test_metrics = {"accuracy": 0.95}  # Above threshold of 0.90
        triggered_alerts = self.service._check_for_alerts_sync(
            self.model_id, "1.0", test_metrics
        )

        # Assert
        assert len(triggered_alerts) == 0


"""
Integration tests for the database-first model monitoring API.

These tests verify that the monitoring API properly:
1. Retrieves data from database by default
2. Only falls back to mock data when database access fails
3. Properly indicates when mock data is being used
4. Maintains consistency in async patterns
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.initialize_db import initialize_database
from src.db.real_database import SQLiteDatabase
from src.main import app as main_app
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestMonitoringDatabaseFirstAPI:
    """Integration tests for database-first model monitoring API."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Initialize an in-memory database for testing
        self.db = initialize_database(in_memory=True, populate=True)

        # Create a real repository that uses our test database
        self.sqlite_repo = SQLiteModelMetricsRepository(db=self.db)

        # Create a spy repository to track method calls for verification
        self.sql_repo_spy = AsyncMock(wraps=self.sqlite_repo)

        # Create the repository with our spy
        self.metrics_repository = ModelMetricsRepository(
            sql_repo=self.sql_repo_spy, test_mode=True
        )

        # Create the service with our repository
        self.service = ModelMonitoringService(
            metrics_repository=self.metrics_repository
        )

        # Initialize and seed the database with test data
        self._seed_test_data()

        # Set up the test client with our service
        main_app.dependency_overrides = {}
        main_app.state.monitoring_service = self.service
        self.client = TestClient(main_app)

    def _seed_test_data(self):
        """Seed the database with test data."""
        # Add a unique test model to verify database access
        self.model_id = f"test-model-{str(uuid.uuid4())[:8]}"
        self.model_version = "1.0"

        # Insert test model
        self.db.execute(
            "INSERT INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            (
                self.model_id,
                "DB-First Test Model",
                "Created for database-first tests",
                0,
            ),
        )

        # Insert model version
        self.db.execute(
            "INSERT INTO model_versions (id, model_id, version, status) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), self.model_id, self.model_version, "active"),
        )

        # Insert test metrics
        metrics_data = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86,
        }

        self.db.execute(
            "INSERT INTO model_metrics (id, model_id, model_version, metrics, timestamp) VALUES (?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                self.model_id,
                self.model_version,
                json.dumps(metrics_data),
                datetime.now().isoformat(),
            ),
        )

        # Insert test alert rule
        self.db.execute(
            """INSERT INTO alert_rules
               (id, model_id, model_version, rule_name, metric_name, threshold, operator,
                severity, description, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                self.model_id,
                self.model_version,
                "Test Rule",
                "accuracy",
                0.9,
                "<",
                "HIGH",
                "Test alert rule",
                1,
                datetime.now().isoformat(),
            ),
        )

    @pytest.mark.asyncio
    async def test_get_models_uses_database(self):
        """Test that the models endpoint retrieves data from database."""
        # Ensure we're using the database, not mock data
        os.environ["USE_MOCK_DATA"] = "False"

        # Call the API
        response = self.client.get("/models")

        # Verify the response
        assert response.status_code == 200

        # Check that our unique test model is in the response
        models = response.json()
        test_model = next((m for m in models if m["id"] == self.model_id), None)
        assert test_model is not None, "Test model not found in response"

        # Verify there's a data source indicator that shows it's from the database
        assert "is_mock_data" in response.json()
        assert response.json()["is_mock_data"] is False

        # Verify the repository's database method was called
        self.sql_repo_spy.get_models.assert_called_at_least_once()

    @pytest.mark.asyncio
    async def test_get_models_falls_back_to_mock(self):
        """Test that the models endpoint falls back to mock data when DB access fails."""
        # Force the database operation to fail
        with patch.object(
            self.sql_repo_spy,
            "get_models",
            side_effect=Exception("Simulated DB failure"),
        ):
            # Call the API
            response = self.client.get("/models")

            # Verify the response
            assert response.status_code == 200

            # Verify there's a data source indicator that shows it's from mock data
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

    @pytest.mark.asyncio
    async def test_get_model_metrics_uses_database(self):
        """Test that the metrics endpoint retrieves data from database."""
        # Call the API
        response = self.client.get(
            f"/models/{self.model_id}/versions/{self.model_version}/metrics"
        )

        # Verify the response
        assert response.status_code == 200

        # Verify there's a data source indicator that shows it's from the database
        assert "is_mock_data" in response.json()
        assert response.json()["is_mock_data"] is False

        # Verify the metrics data is included
        assert "metrics" in response.json()
        metrics = response.json()["metrics"]
        assert len(metrics) > 0
        assert "accuracy" in metrics[0]

        # Verify the repository's database method was called
        self.sql_repo_spy.get_model_metrics_history.assert_called_at_least_once()

    @pytest.mark.asyncio
    async def test_get_model_metrics_falls_back_to_mock(self):
        """Test that the metrics endpoint falls back to mock when DB access fails."""
        # Force the database operation to fail
        with patch.object(
            self.sql_repo_spy,
            "get_model_metrics_history",
            side_effect=Exception("Simulated DB failure"),
        ):
            # Call the API
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/metrics"
            )

            # Verify the response
            assert response.status_code == 200

            # Verify there's a data source indicator that shows it's from mock data
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

            # Verify mock metrics are still returned
            assert "metrics" in response.json()
            assert len(response.json()["metrics"]) > 0

    @pytest.mark.asyncio
    async def test_create_alert_rule_uses_database(self):
        """Test that creating an alert rule uses the database."""
        # Prepare test data
        rule_data = {
            "rule_name": "Integration Test Rule",
            "metric_name": "precision",
            "threshold": 0.85,
            "operator": "<",
            "severity": "MEDIUM",
            "description": "Alert when precision drops below 85%",
        }

        # Call the API
        response = self.client.post(
            f"/models/{self.model_id}/versions/{self.model_version}/alerts/rules",
            json=rule_data,
        )

        # Verify the response
        assert response.status_code == 201

        # Verify there's a data source indicator
        assert "is_mock_data" in response.json()
        assert response.json()["is_mock_data"] is False

        # Verify the repository's database method was called
        self.sql_repo_spy.create_alert_rule.assert_called_once()

        # Verify the rule was actually saved in the database
        query = "SELECT * FROM alert_rules WHERE rule_name = ? AND model_id = ?"
        rows = self.db.fetch_all(query, (rule_data["rule_name"], self.model_id))
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_get_alert_rules_uses_database(self):
        """Test that getting alert rules uses the database."""
        # Call the API
        response = self.client.get(
            f"/models/{self.model_id}/versions/{self.model_version}/alerts/rules"
        )

        # Verify the response
        assert response.status_code == 200

        # Verify there's a data source indicator
        assert "is_mock_data" in response.json()
        assert response.json()["is_mock_data"] is False

        # Verify the alert rules are returned
        rules = response.json()["rules"]
        assert len(rules) > 0
        assert rules[0]["model_id"] == self.model_id

        # Verify the repository's database method was called
        self.sql_repo_spy.get_alert_rules.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_triggered_alerts_uses_database(self):
        """Test that getting triggered alerts uses the database."""
        # Trigger an alert by recording metrics below threshold
        low_metrics = {"accuracy": 0.85}  # Below our 0.9 threshold

        # Record the metrics through the service to trigger the alert
        await self.service.record_model_metrics(
            model_id=self.model_id,
            model_version=self.model_version,
            metrics=low_metrics,
        )

        # Call the API
        response = self.client.get(
            f"/models/{self.model_id}/versions/{self.model_version}/alerts"
        )

        # Verify the response
        assert response.status_code == 200

        # Verify there's a data source indicator
        assert "is_mock_data" in response.json()
        assert response.json()["is_mock_data"] is False

        # Verify the triggered alerts are returned
        alerts = response.json()["alerts"]
        assert len(alerts) > 0
        assert alerts[0]["model_id"] == self.model_id
        assert alerts[0]["metric_name"] == "accuracy"

        # Verify the repository's database method was called
        self.sql_repo_spy.get_triggered_alerts.assert_called_once()  # Add these tests to test_model_monitoring_service.py

        @pytest.mark.asyncio
        async def test_service_indicates_mock_data_on_db_failure(self):
            """Test that service properly indicates when mock data is used due to DB failure."""
            # Arrange - Force DB failure
            with patch.object(
                self.metrics_repo,
                "get_alert_rules",
                side_effect=Exception("Simulated DB failure"),
            ):
                # Act
                rules, is_mock = await self.service.get_alert_rules(self.model_id)

                # Assert
                self.assertTrue(is_mock, "Should indicate mock data is being used")
                self.assertTrue(len(rules) > 0, "Should return mock data")

        @pytest.mark.asyncio
        async def test_record_metrics_returns_mock_indicator(self):
            """Test that record_metrics returns a mock indicator."""
            # Arrange
            metrics = {"accuracy": 0.95}

            # Act with normal DB access
            metric_id, is_mock = await self.service.record_model_metrics(
                model_id=self.model_id,
                model_version=self.model_version,
                metrics=metrics,
            )

            # Assert
            self.assertFalse(is_mock, "Should indicate real DB was used")

            # Now force DB failure
            with patch.object(
                self.metrics_repo,
                "record_model_metrics",
                side_effect=Exception("Simulated DB failure"),
            ):
                # Act
                metric_id, is_mock = await self.service.record_model_metrics(
                    model_id=self.model_id,
                    model_version=self.model_version,
                    metrics=metrics,
                )

                # Assert
                self.assertTrue(is_mock, "Should indicate mock data was used")
