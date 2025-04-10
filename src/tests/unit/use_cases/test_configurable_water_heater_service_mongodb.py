"""
Unit tests for Configurable Water Heater Service with MongoDB Repository.

This module contains tests for the Configurable Water Heater Service that can use
different repository implementations including MongoDB, following the TDD approach
(red-green-refactor) and Clean Architecture principles.
"""
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestConfigurableWaterHeaterServiceWithMongoDB:
    """Unit tests for Configurable Water Heater Service with MongoDB repository."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment variables
        self.original_env = os.environ.get("APP_ENV")
        self.original_use_mock = os.environ.get("USE_MOCK_DATA")
        self.original_db_type = os.environ.get("DATABASE_TYPE")

        # Clear relevant environment variables
        if "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]
        if "USE_MOCK_DATA" in os.environ:
            del os.environ["USE_MOCK_DATA"]
        if "DATABASE_TYPE" in os.environ:
            del os.environ["DATABASE_TYPE"]

    def tearDown(self):
        """Clean up after test."""
        # Restore original environment variables
        if self.original_env:
            os.environ["APP_ENV"] = self.original_env
        elif "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]

        if self.original_use_mock:
            os.environ["USE_MOCK_DATA"] = self.original_use_mock
        elif "USE_MOCK_DATA" in os.environ:
            del os.environ["USE_MOCK_DATA"]

        if self.original_db_type:
            os.environ["DATABASE_TYPE"] = self.original_db_type
        elif "DATABASE_TYPE" in os.environ:
            del os.environ["DATABASE_TYPE"]

    @pytest.mark.tdd_red
    @patch("src.config.config.get")
    def test_init_with_mongodb_config(self, mock_config_get):
        """Test service initialization with MongoDB configuration.

        This test verifies that the service correctly initializes a MongoDB repository
        when configured to use MongoDB as the database type.
        """
        # Arrange
        # Mock configuration values to use MongoDB
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": "mongodb",
            "database.fallback_to_mock": True,
            "database.mongodb.connection_string": "mongodb://localhost:27017",
        }.get(key, default)

        # Import ConfigurableWaterHeaterService locally to avoid issues with mocking
        from src.services.configurable_water_heater_service import (
            ConfigurableWaterHeaterService,
        )

        # Mock the MongoDB repository
        with patch(
            "src.services.configurable_water_heater_service.MongoDBWaterHeaterRepository"
        ) as mock_mongodb:
            # Create service without explicit repository
            service = ConfigurableWaterHeaterService()

            # Assert
            # Should try to use MongoDB repository
            mock_mongodb.assert_called_once()
            assert service.repository == mock_mongodb.return_value

            # Verify the connection string was passed correctly
            args, kwargs = mock_mongodb.call_args
            assert kwargs["connection_string"] == "mongodb://localhost:27017"

    @pytest.mark.tdd_red
    @patch("src.config.config.get")
    def test_init_with_mongodb_environment_variable(self, mock_config_get):
        """Test service initialization with DATABASE_TYPE environment variable set to mongodb.

        This test verifies that the service correctly initializes a MongoDB repository
        when the DATABASE_TYPE environment variable is set to mongodb.
        """
        # Arrange
        # Set environment variable
        os.environ["DATABASE_TYPE"] = "mongodb"

        # Mock configuration values to use environment variable
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": None,  # This will force using the environment variable
            "database.fallback_to_mock": True,
            "database.mongodb.connection_string": "mongodb://localhost:27017",
        }.get(key, default)

        # Import ConfigurableWaterHeaterService locally to avoid issues with mocking
        from src.services.configurable_water_heater_service import (
            ConfigurableWaterHeaterService,
        )

        # Mock the MongoDB repository
        with patch(
            "src.services.configurable_water_heater_service.MongoDBWaterHeaterRepository"
        ) as mock_mongodb:
            # Create service without explicit repository
            service = ConfigurableWaterHeaterService()

            # Assert
            # Should try to use MongoDB repository
            mock_mongodb.assert_called_once()
            assert service.repository == mock_mongodb.return_value

    @pytest.mark.tdd_red
    @patch("src.config.config.get")
    def test_fallback_to_mock_when_mongodb_fails(self, mock_config_get):
        """Test fallback to mock data when MongoDB connection fails.

        This test verifies that the service correctly falls back to using a mock repository
        when the MongoDB connection fails.
        """
        # Arrange
        # Mock configuration values to use MongoDB
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": "mongodb",
            "database.fallback_to_mock": True,
            "database.mongodb.connection_string": "mongodb://localhost:27017",
        }.get(key, default)

        # Import ConfigurableWaterHeaterService locally to avoid issues with mocking
        from src.services.configurable_water_heater_service import (
            ConfigurableWaterHeaterService,
        )

        # Mock the repositories
        with patch(
            "src.services.configurable_water_heater_service.MongoDBWaterHeaterRepository"
        ) as mock_mongodb, patch(
            "src.services.configurable_water_heater_service.MockWaterHeaterRepository"
        ) as mock_mock:
            # Make MongoDB repository raise an exception on creation
            mock_mongodb.side_effect = Exception("MongoDB connection failed")

            # Create service
            service = ConfigurableWaterHeaterService()

            # Assert
            # Should try MongoDB repository first
            mock_mongodb.assert_called_once()

            # Then fall back to mock repository
            mock_mock.assert_called_once()
            assert service.repository == mock_mock.return_value

            # Verify warning was logged (would need to mock logger and check)

    @pytest.mark.tdd_red
    @patch("src.config.config.get")
    def test_explicit_repository_takes_precedence(self, mock_config_get):
        """Test that explicitly provided repository takes precedence over configuration.

        This test verifies that when a repository is explicitly provided to the service,
        it is used regardless of the configuration.
        """
        # Arrange
        # Mock configuration values to use MongoDB
        mock_config_get.side_effect = lambda key, default=None: {
            "services.water_heater.use_mock_data": False,
            "database.type": "mongodb",
            "database.fallback_to_mock": True,
        }.get(key, default)

        # Import ConfigurableWaterHeaterService and WaterHeaterRepository locally
        from src.gateways.water_heater_repository import WaterHeaterRepository
        from src.services.configurable_water_heater_service import (
            ConfigurableWaterHeaterService,
        )

        # Create a mock repository
        mock_repo = MagicMock(spec=WaterHeaterRepository)

        # Mock the MongoDB repository
        with patch(
            "src.services.configurable_water_heater_service.MongoDBWaterHeaterRepository"
        ) as mock_mongodb:
            # Create service with explicit repository
            service = ConfigurableWaterHeaterService(repository=mock_repo)

            # Assert
            # Should not try to create MongoDB repository
            mock_mongodb.assert_not_called()

            # Should use the explicitly provided repository
            assert service.repository == mock_repo

            # Configuration should not be queried
            mock_config_get.assert_not_called()

    @pytest.mark.tdd_red
    def test_mongodb_repository_implements_required_interface(self):
        """Test that MongoDBWaterHeaterRepository implements the required repository interface.

        This test verifies that the MongoDB repository implements all the methods required by
        the WaterHeaterRepository interface.
        """
        # Import the relevant classes
        from src.adapters.repositories.mongodb_water_heater_repository import (
            MongoDBWaterHeaterRepository,
        )
        from src.gateways.water_heater_repository import WaterHeaterRepository

        # Create the repository instance (mocked to avoid actual MongoDB connection)
        with patch("motor.motor_asyncio.AsyncIOMotorClient"):
            repo = MongoDBWaterHeaterRepository(
                connection_string="mongodb://localhost:27017"
            )

            # Verify the repository inherits from the interface
            assert isinstance(repo, WaterHeaterRepository)

            # Verify all required methods are implemented
            required_methods = ["get_by_id", "get_all", "save", "update", "delete"]

            for method in required_methods:
                assert hasattr(repo, method)
                assert callable(getattr(repo, method))
