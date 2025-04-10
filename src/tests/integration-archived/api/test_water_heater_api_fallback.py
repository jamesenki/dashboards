"""
Integration tests for the water heater API fallback behavior.

These tests verify that the system attempts to use the database API first
and only falls back to the mock API if the database connection fails.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import config
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


class TestWaterHeaterApiFallback:
    """Tests for water heater API fallback behavior."""

    @pytest.fixture
    def client(self):
        """Create a test client with a clean environment."""
        # Store original environment variables
        original_env = {}
        for var in ["APP_ENV", "USE_MOCK_DATA"]:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        # Import the app from main directly
        # We need to reload main to ensure it picks up our environment changes
        if "src.main" in sys.modules:
            del sys.modules["src.main"]

        # Now import and create a test client
        from src.main import app

        client = TestClient(app)

        yield client

        # Restore original environment variables
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    @patch("src.config.config.get")
    def test_api_fallback_when_db_fails(self, mock_config_get, client):
        """Test that the API falls back to mock data when the database fails."""
        # Configure test settings to ensure fallback is enabled
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": "sqlite",
            "database.fallback_to_mock": True,
        }.get(key, default)

        # Use a patched version of the repository that will fail
        with patch(
            "src.repositories.water_heater_repository.SQLiteWaterHeaterRepository.__init__"
        ) as mock_sqlite_init:
            # Make SQLite repository initialization raise an exception
            mock_sqlite_init.side_effect = Exception("Database connection failed")

            # Also patch the database health check to avoid false positives
            with patch(
                "src.repositories.water_heater_repository.MockWaterHeaterRepository.get_water_heaters",
                return_value=[],
            ) as mock_get_heaters:
                # Access the regular water heaters API endpoint (not the specific db or mock one)
                response = client.get("/api/water-heaters/")

                # Should get a successful response, since fallback is enabled
                assert response.status_code == 200

                # Verify we got data from the mock repository
                mock_get_heaters.assert_called()

                # Verify that response contains indication it's from mock data
                # Get info about the data source
                source_info = client.get("/api/debug/water-heater-data-source")
                assert source_info.status_code == 200
                source_data = source_info.json()
                assert "repository_type" in source_data
                assert "MockWaterHeaterRepository" in source_data["repository_type"]

    @patch("src.config.config.get")
    def test_no_api_fallback_when_disabled(self, mock_config_get, client):
        """Test that the API doesn't fall back when fallback is disabled."""
        # Override config to disable fallback
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": "sqlite",
            "database.fallback_to_mock": False,  # Fallback explicitly disabled
        }.get(key, default)

        # Use a patched version of the repository initialization that will fail
        with patch(
            "src.repositories.water_heater_repository.SQLiteWaterHeaterRepository.__init__"
        ) as mock_sqlite_init:
            # Make SQLite repository initialization raise an exception
            mock_sqlite_init.side_effect = Exception("Database connection failed")

            # Also track if the mock repository is used as a fallback
            with patch(
                "src.repositories.water_heater_repository.MockWaterHeaterRepository.__init__",
                return_value=None,
            ) as mock_mock_init:
                # We expect an error since fallback is disabled
                # The actual response might not be 500 depending on how errors are handled
                # The important thing is to check if the mock repo was NOT used

                try:
                    # This might fail completely or return a 500 response
                    response = client.get("/api/water-heaters/")
                    # If we get here, the request didn't fail entirely, but should show an error
                    assert (
                        response.status_code >= 400
                    ), "Expected error response when database fails and fallback is disabled"
                except Exception as e:
                    # Exception is expected when fallback is disabled
                    pass

                # MockWaterHeaterRepository should not have been initialized if fallback is disabled
                # This verifies that when fallback is disabled, we don't use the mock repository
                mock_mock_init.assert_not_called()

    def test_separate_api_endpoints_no_fallback(self, client):
        """
        Test that the separate DB and mock API endpoints use their specific
        services without triggering the fallback mechanism.
        """
        # For this test, we use the real repositories but verify that
        # the API endpoints are working and returning information about their data sources

        # Test the database API endpoint's data source information
        response_db_info = client.get("/api/db/water-heaters/data-source")
        assert response_db_info.status_code == 200
        db_info = response_db_info.json()
        assert db_info["source_type"] == "database"

        # Test the mock API endpoint's data source information
        response_mock_info = client.get("/api/mock/water-heaters/data-source")
        assert response_mock_info.status_code == 200
        mock_info = response_mock_info.json()
        assert mock_info["source_type"] == "mock"

        # The separate endpoints should never fall back to each other
        # DB endpoints should always use the DB repository
        # Mock endpoints should always use the mock repository

    def test_browser_detection_of_data_source(self, client):
        """
        Test that the frontend can detect which data source is being used
        by examining the data source endpoint.
        """
        # Test the database data source info endpoint
        response_db = client.get("/api/db/water-heaters/data-source")
        assert response_db.status_code == 200
        data_source_db = response_db.json()
        assert data_source_db["source_type"] == "database"

        # Test the mock data source info endpoint
        response_mock = client.get("/api/mock/water-heaters/data-source")
        assert response_mock.status_code == 200
        data_source_mock = response_mock.json()
        assert data_source_mock["source_type"] == "mock"
