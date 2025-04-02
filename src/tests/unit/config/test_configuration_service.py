"""
Tests for the IoTSphere configuration service.

Following TDD principles, these tests define the expected behavior
of the configuration system before implementation.
"""
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
import yaml

from src.config.exceptions import ConfigurationError
from src.config.models import ApiConfig, AppConfig, DatabaseConfig
from src.config.providers import (
    ConfigurationProvider,
    DefaultProvider,
    EnvironmentProvider,
    FileProvider,
)

# Imports that will exist after implementation
# These will fail until we create the actual implementation
from src.config.service import ConfigurationService


class TestConfigurationProviders:
    """Tests for individual configuration providers."""

    def test_default_provider(self):
        """Test the default values provider."""
        # RED: This test will fail until DefaultProvider is implemented
        defaults = {
            "app": {"name": "IoTSphere", "debug": False},
            "database": {"host": "localhost", "port": 5432},
        }

        provider = DefaultProvider(defaults)

        # Test getting values
        assert provider.get("app.name") == "IoTSphere"
        assert provider.get("database.port") == 5432
        assert provider.get("nonexistent") is None
        assert provider.get("nonexistent", "default") == "default"

    def test_file_provider(self):
        """Test loading configuration from YAML files."""
        # RED: This test will fail until FileProvider is implemented

        # Create temporary config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp:
            config_data = {
                "app": {"name": "IoTSphere Test", "debug": True},
                "database": {"host": "testdb", "port": 5433},
                "nested": {"level1": {"level2": {"value": "nested value"}}},
            }
            yaml.dump(config_data, temp)
            temp_path = temp.name

        try:
            # Test loading from file
            provider = FileProvider(temp_path)

            # Test basic values
            assert provider.get("app.name") == "IoTSphere Test"
            assert provider.get("database.port") == 5433

            # Test nested values
            assert provider.get("nested.level1.level2.value") == "nested value"

            # Test missing values
            assert provider.get("nonexistent") is None
            assert provider.get("nonexistent", "default") == "default"

            # Test with wrong file path
            with pytest.raises(ConfigurationError):
                FileProvider("nonexistent.yaml")

        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def test_environment_provider(self):
        """Test loading configuration from environment variables."""
        # RED: This test will fail until EnvironmentProvider is implemented

        # Save current environment
        old_environ = os.environ.copy()

        try:
            # Set test environment variables
            os.environ["IOTSPHERE_APP_NAME"] = "IoTSphere Env"
            os.environ["IOTSPHERE_DATABASE_PORT"] = "5434"
            os.environ[
                "IOTSPHERE_API_CORS_ALLOWED_ORIGINS"
            ] = "http://localhost:4200,http://example.com"

            # Create provider with prefix
            provider = EnvironmentProvider(prefix="IOTSPHERE_")

            # Test basic values
            assert provider.get("app.name") == "IoTSphere Env"
            assert (
                provider.get("database.port") == "5434"
            )  # Note: comes as string from env

            # Test list parsing
            assert (
                provider.get("api.cors.allowed_origins")
                == "http://localhost:4200,http://example.com"
            )

            # Test missing values
            assert provider.get("nonexistent") is None

            # Test without prefix
            basic_provider = EnvironmentProvider()
            assert basic_provider.get("IOTSPHERE_APP_NAME") == "IoTSphere Env"

        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(old_environ)


class TestConfigurationService:
    """Tests for the main configuration service."""

    def test_initialization(self):
        """Test configuration service initialization."""
        # RED: This test will fail until ConfigurationService is implemented

        service = ConfigurationService()

        # Service should initialize with empty configuration
        assert service.get("app.name") is None

        # Test with initial data
        initial_config = {"app": {"name": "Test App"}}
        service = ConfigurationService(initial_config)
        assert service.get("app.name") == "Test App"

    def test_provider_registration(self):
        """Test registering configuration providers."""
        # RED: This test will fail until provider registration is implemented

        service = ConfigurationService()

        # Register default provider
        defaults = {"app": {"name": "Default App"}}
        service.register_provider(DefaultProvider(defaults))
        assert service.get("app.name") == "Default App"

        # Register environment provider with higher priority
        os.environ["IOTSPHERE_APP_NAME"] = "Env App"
        service.register_provider(
            EnvironmentProvider(prefix="IOTSPHERE_"),
            priority=10,  # Higher priority than default
        )
        assert service.get("app.name") == "Env App"  # Should override default

        # Clean up
        os.environ.pop("IOTSPHERE_APP_NAME")

    def test_configuration_merging(self):
        """Test merging configuration from multiple providers."""
        # RED: This test will fail until configuration merging is implemented

        service = ConfigurationService()

        # Register providers with different values
        service.register_provider(
            DefaultProvider(
                {
                    "app": {"name": "Default App", "debug": False},
                    "database": {"host": "localhost", "port": 5432},
                }
            ),
            priority=1,
        )

        service.register_provider(
            DefaultProvider(
                {"app": {"name": "Override App"}, "api": {"version": "v1"}}
            ),
            priority=2,  # Higher priority
        )

        # Check merging behavior
        assert service.get("app.name") == "Override App"  # Overridden
        assert service.get("app.debug") is False  # From default
        assert service.get("database.port") == 5432  # From default
        assert service.get("api.version") == "v1"  # From override

    def test_typed_access(self):
        """Test typed configuration access."""
        # RED: This test will fail until typed access is implemented

        service = ConfigurationService()
        service.register_provider(
            DefaultProvider(
                {
                    "app": {
                        "name": "IoTSphere",
                        "debug": "true",
                        "port": "8080",
                        "workers": "4",
                    },
                    "database": {"timeout": "30.5"},
                }
            )
        )

        # Test type conversion
        assert service.get_bool("app.debug") is True
        assert service.get_int("app.port") == 8080
        assert service.get_int("app.workers") == 4
        assert service.get_float("database.timeout") == 30.5

        # Test type conversion with defaults
        assert service.get_bool("nonexistent", False) is False
        assert service.get_int("nonexistent", 42) == 42
        assert service.get_float("nonexistent", 3.14) == 3.14

    def test_section_access(self):
        """Test accessing configuration sections."""
        # RED: This test will fail until section access is implemented

        service = ConfigurationService()
        service.register_provider(
            DefaultProvider(
                {
                    "app": {"name": "IoTSphere", "debug": True},
                    "database": {"host": "localhost", "port": 5432},
                }
            )
        )

        # Get whole sections
        app_section = service.get_section("app")
        assert app_section == {"name": "IoTSphere", "debug": True}

        db_section = service.get_section("database")
        assert db_section == {"host": "localhost", "port": 5432}

        # Nonexistent section
        assert service.get_section("nonexistent") == {}

        # With default
        assert service.get_section("nonexistent", {"default": True}) == {
            "default": True
        }

    def test_validation_with_schema(self):
        """Test configuration validation with Pydantic models."""
        # RED: This test will fail until schema validation is implemented

        service = ConfigurationService()
        service.register_provider(
            DefaultProvider(
                {
                    "database": {
                        "type": "postgres",
                        "host": "localhost",
                        "port": 5432,
                        "credentials": {"username": "user", "password": "pass"},
                    }
                }
            )
        )

        # Validate database section against DatabaseConfig schema
        db_config = service.get_validated("database", DatabaseConfig)
        assert isinstance(db_config, DatabaseConfig)
        assert db_config.type == "postgres"
        assert db_config.port == 5432
        assert db_config.credentials.username == "user"

        # Invalid configuration should raise error
        service = ConfigurationService()
        service.register_provider(
            DefaultProvider(
                {
                    "database": {
                        "type": "postgres",
                        "host": "localhost",
                        "port": 5432,
                        # Missing credentials
                    }
                }
            )
        )

        with pytest.raises(ConfigurationError):
            service.get_validated("database", DatabaseConfig)

    def test_reload_configuration(self):
        """Test reloading configuration."""
        # RED: This test will fail until reload is implemented

        # Create temporary file for configuration
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp:
            config_data = {"app": {"name": "Original Name"}}
            yaml.dump(config_data, temp)
            temp_path = temp.name

        try:
            # Create service with file provider
            service = ConfigurationService()
            service.register_provider(FileProvider(temp_path))

            # Initial configuration
            assert service.get("app.name") == "Original Name"

            # Modify configuration file
            with open(temp_path, "w") as f:
                yaml.dump({"app": {"name": "Updated Name"}}, f)

            # Reload and check
            service.reload()
            assert service.get("app.name") == "Updated Name"

        finally:
            # Clean up
            os.unlink(temp_path)


if __name__ == "__main__":
    # Running manually will show failures (RED phase)
    pytest.main(["-xvs", __file__])
