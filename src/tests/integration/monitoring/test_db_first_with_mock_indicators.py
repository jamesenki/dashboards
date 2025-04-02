"""
Integration tests for database-first design with mock data indicators.

These tests verify that our model monitoring system:
1. Always attempts to use the database first
2. Only falls back to mock data when necessary
3. Properly indicates the data source to clients
4. Handles database failures gracefully
5. Respects the USE_MOCK_DATA environment variable
"""
import asyncio
import json
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
from src.monitoring.dashboard_api import create_dashboard_api
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestDBFirstWithMockIndicators:
    """Integration tests for database-first approach with mock data indicators."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Save original environment variable state
        self.original_use_mock = os.environ.get("USE_MOCK_DATA", "False")
        self.original_testing = os.environ.get("TESTING", "False")

        # Set testing mode to suppress error messages
        os.environ["TESTING"] = "True"

        # Initialize an in-memory database for testing
        self.db = initialize_database(in_memory=True, populate=True)

        # Create a real repository that uses our test database
        self.sqlite_repo = SQLiteModelMetricsRepository(db=self.db)

        # Create spies to track method calls
        self.sql_repo_spy = AsyncMock(wraps=self.sqlite_repo)

        # Create the repository with our spies
        self.metrics_repository = ModelMetricsRepository(
            sql_repo=self.sql_repo_spy, test_mode=True
        )

        # Add spy methods to track DB vs mock data usage
        self._add_repository_spies()

        # Create the service with our repository
        self.service = ModelMonitoringService(
            metrics_repository=self.metrics_repository
        )

        # Create the FastAPI app with our service
        self.app = create_dashboard_api(self.service)
        self.client = TestClient(self.app)

        # Seed the database with test data
        self._seed_test_data()

    def teardown_method(self):
        """Clean up after each test method."""
        # Restore original environment variables
        os.environ["USE_MOCK_DATA"] = self.original_use_mock
        os.environ["TESTING"] = self.original_testing

    def _add_repository_spies(self):
        """Add spies to repository methods to track SQL vs mock usage."""
        # Create spy for the SQL repository and methods that return mock data
        # The SQL repository methods are called directly, and we fall back to mock methods on failure
        self.sql_get_models_spy = MagicMock(wraps=self.sql_repo_spy.get_models)
        self.mock_models_spy = MagicMock(
            wraps=self.metrics_repository._mock_record_model_metrics
        )

        # Replace the methods with our spies
        self.sql_repo_spy.get_models = self.sql_get_models_spy
        self.metrics_repository._mock_record_model_metrics = self.mock_models_spy

    def _seed_test_data(self):
        """Seed the database with test data."""
        # Create unique test model and version IDs
        self.model_id = f"test-model-{str(uuid.uuid4())[:8]}"
        self.model_version = "1.0"

        # Insert model
        self.db.execute(
            "INSERT INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            (
                self.model_id,
                "DB-First Test Model",
                "Testing DB-first with indicators",
                0,
            ),
        )

        # Insert model version
        self.db.execute(
            "INSERT INTO model_versions (id, model_id, version) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), self.model_id, self.model_version),
        )

        # Insert metrics - add each metric as a separate row
        metrics_data = {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.91,
            "f1_score": 0.93,
        }

        # Insert each metric as a separate row
        for metric_name, metric_value in metrics_data.items():
            self.db.execute(
                "INSERT INTO model_metrics (id, model_id, model_version, metric_name, metric_value) VALUES (?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    self.model_id,
                    self.model_version,
                    metric_name,
                    metric_value,
                ),
            )

        # Insert alert rule with updated schema fields
        self.db.execute(
            """INSERT INTO alert_rules
               (id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, description, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                self.model_id,
                self.model_version,
                "Test Rule",
                "accuracy",
                0.9,
                "BELOW",
                "WARNING",
                "Test description",
                1,
            ),
        )

    @pytest.mark.asyncio
    async def test_repository_always_tries_db_first(self):
        """Test that repository methods always try the database first."""
        # Ensure mock data is disabled
        os.environ["USE_MOCK_DATA"] = "False"

        # Reset spy call counts
        self.sql_get_models_spy.reset_mock()

        # Call get_models - should use DB and not mock
        models, is_mock = await self.metrics_repository.get_models()

        # Verify SQL repo was called
        self.sql_get_models_spy.assert_called_once()

        # Verify is_mock indicator is False
        assert is_mock is False

        # Now simulate a DB failure with a patched method that also tracks calls
        patched_get_models = MagicMock(side_effect=Exception("Simulated DB failure"))

        with patch.object(self.sql_repo_spy, "get_models", patched_get_models):
            # Call get_models - should try DB, fail, then use mock
            models, is_mock = await self.metrics_repository.get_models()

            # DB method should be attempted - check on our patched mock
            patched_get_models.assert_called_once()

            # Verify is_mock indicator is True
            assert is_mock is True

    @pytest.mark.asyncio
    async def test_use_mock_data_env_var_respected(self):
        """Test that USE_MOCK_DATA environment variable is respected."""
        # Set to use mock data
        os.environ["USE_MOCK_DATA"] = "True"

        # Reset spy call counts
        self.sql_get_models_spy.reset_mock()

        # Call get_models - should go straight to mock
        models, is_mock = await self.metrics_repository.get_models()

        # SQL method should not be called
        self.sql_get_models_spy.assert_not_called()

        # Verify is_mock indicator is True
        assert is_mock is True

    @pytest.mark.asyncio
    async def test_all_repository_methods_return_indicators(self):
        """Test that all repository methods return mock data indicators."""
        # Ensure we're not using mock data
        os.environ["USE_MOCK_DATA"] = "False"

        # Test get_models
        models, is_mock = await self.metrics_repository.get_models()
        assert is_mock is False

        # Test get_model_versions
        versions, is_mock = await self.metrics_repository.get_model_versions(
            self.model_id
        )
        assert is_mock is False

        # Test get_model_metrics_history
        metrics, is_mock = await self.metrics_repository.get_model_metrics_history(
            self.model_id, self.model_version
        )
        assert is_mock is False

        # Test get_triggered_alerts
        alerts, is_mock = await self.metrics_repository.get_triggered_alerts(
            self.model_id, self.model_version
        )
        assert is_mock is False

        # Force DB failure for each method and verify indicator
        # Important: We need to patch the sql_repo_spy that's actually used by the repository
        with patch.object(
            self.sql_repo_spy, "get_models", side_effect=Exception("DB failure")
        ):
            models, is_mock = await self.metrics_repository.get_models()
            assert is_mock is True

        with patch.object(
            self.sql_repo_spy, "get_model_versions", side_effect=Exception("DB failure")
        ):
            versions, is_mock = await self.metrics_repository.get_model_versions(
                self.model_id
            )
            assert is_mock is True

        with patch.object(
            self.sql_repo_spy,
            "get_model_metrics_history",
            side_effect=Exception("DB failure"),
        ):
            metrics, is_mock = await self.metrics_repository.get_model_metrics_history(
                self.model_id, self.model_version
            )
            assert is_mock is True

        with patch.object(
            self.sql_repo_spy,
            "get_triggered_alerts",
            side_effect=Exception("DB failure"),
        ):
            alerts, is_mock = await self.metrics_repository.get_triggered_alerts(
                self.model_id, self.model_version
            )
            assert is_mock is True

    @pytest.mark.asyncio
    async def test_service_propagates_mock_indicators(self):
        """Test that service methods properly propagate mock indicators from repository."""
        # Ensure we're not using mock data
        os.environ["USE_MOCK_DATA"] = "False"

        # Test normal DB access
        models, is_mock = await self.service.get_models()
        assert is_mock is False

        # Test mock fallback
        with patch.object(
            self.metrics_repository,
            "get_models",
            return_value=([{"id": "mock1"}], True),
        ):
            models, is_mock = await self.service.get_models()
            assert is_mock is True

    def test_api_endpoints_include_mock_indicators(self):
        """Test that API endpoints include mock data indicators in responses."""
        # Ensure we're not using mock data
        os.environ["USE_MOCK_DATA"] = "False"

        # Patch the service methods to avoid SQLite threading issues in tests
        # Return non-mock data (is_mock=False) to match test expectations
        with patch.object(
            self.service,
            "get_monitored_models",
            return_value=([{"id": "model1"}], False),
        ), patch.object(
            self.service, "get_latest_metrics", return_value=({"accuracy": 0.95}, False)
        ), patch.object(
            self.service, "get_alert_rules", return_value=([{"id": "rule1"}], False)
        ), patch.object(
            self.service,
            "get_triggered_alerts",
            return_value=([{"id": "alert1"}], False),
        ):
            # Test models endpoint
            response = self.client.get("/models")
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is False

            # Test metrics endpoint
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/metrics"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is False

            # Test alert rules endpoint
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/alerts/rules"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is False

            # Test triggered alerts endpoint
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/alerts"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is False

    def test_api_endpoints_indicate_mock_on_db_failure(self):
        """Test that API endpoints properly indicate mock data on DB failure."""
        # Force DB failure for models
        with patch.object(
            self.service, "get_models", return_value=([{"id": "mock1"}], True)
        ):
            response = self.client.get("/models")
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

        # Force DB failure for metrics
        with patch.object(
            self.service,
            "get_model_metrics_history",
            return_value=([{"metric": "accuracy", "value": 0.9}], True),
        ):
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/metrics"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

        # Force DB failure for alert rules
        with patch.object(
            self.service,
            "get_alert_rules",
            return_value=([{"rule_name": "Mock Rule"}], True),
        ):
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/alerts/rules"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

        # Force DB failure for triggered alerts
        with patch.object(
            self.service,
            "get_triggered_alerts",
            return_value=([{"alert_id": "mock-alert"}], True),
        ):
            response = self.client.get(
                f"/models/{self.model_id}/versions/{self.model_version}/alerts"
            )
            assert response.status_code == 200
            assert "is_mock_data" in response.json()
            assert response.json()["is_mock_data"] is True

    @pytest.mark.asyncio
    async def test_create_operations_return_indicators(self):
        """Test that create operations return proper mock indicators."""
        # Test creating an alert rule with normal DB access
        rule_data = {
            "rule_name": "Test Rule Create",
            "metric_name": "precision",
            "threshold": 0.8,
            "operator": "<",
            "severity": "LOW",
            "description": "Test rule creation",
        }

        rule_id, is_mock = await self.service.create_alert_rule(
            self.model_id, self.model_version, **rule_data
        )

        assert is_mock is False
        assert rule_id is not None

        # Test with DB failure
        with patch.object(
            self.metrics_repository,
            "create_alert_rule",
            side_effect=Exception("DB failure"),
        ):
            rule_id, is_mock = await self.service.create_alert_rule(
                self.model_id, self.model_version, **rule_data
            )

            assert is_mock is True
            assert rule_id is not None

    @pytest.mark.asyncio
    async def test_model_operations_use_db_first(self):
        """Test that model operations use database by default."""
        # Ensure USE_MOCK_DATA is False
        os.environ["USE_MOCK_DATA"] = "False"

        # Create a spy for the SQL repository's record_model_metrics method
        record_spy = MagicMock(wraps=self.sql_repo_spy.record_model_metrics)
        self.sql_repo_spy.record_model_metrics = record_spy

        # Record new metrics to trigger alert evaluation
        metrics = {"accuracy": 0.85}  # Below our 0.9 threshold

        # Record metrics
        metric_id, is_mock = await self.service.record_model_metrics(
            model_id=self.model_id, model_version=self.model_version, metrics=metrics
        )

        # Verify SQL method was called
        record_spy.assert_called_once()

        # Verify is_mock indicator is False
        assert is_mock is False

        # Reset spy and force failure
        record_spy.reset_mock()
        record_spy.side_effect = Exception("DB failure")

        # Record metrics again - should use mock data now
        metric_id, is_mock = await self.service.record_model_metrics(
            model_id=self.model_id, model_version=self.model_version, metrics=metrics
        )

        # Verify SQL method was still called
        record_spy.assert_called_once()

        # Verify is_mock indicator is True
        assert is_mock is True
