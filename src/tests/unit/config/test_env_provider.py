"""
Tests for the environment-specific configuration provider.
"""
import os
import tempfile
from pathlib import Path
import unittest
import yaml

from src.config.env_provider import EnvironmentFileProvider
from src.config.exceptions import ConfigurationProviderError


class TestEnvironmentFileProvider(unittest.TestCase):
    """Test cases for the EnvironmentFileProvider."""
    
    def setUp(self):
        """Set up the test case with temporary configuration files."""
        # Create temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        
        # Create base config.yaml
        self.base_config = {
            "app": {
                "name": "IoTSphere",
                "environment": "development",
                "log_level": "INFO"
            },
            "database": {
                "type": "sqlite",
                "path": "test.db",
                "fallback_to_mock": True
            }
        }
        
        with open(self.config_dir / "config.yaml", 'w') as f:
            yaml.dump(self.base_config, f)
        
        # Create development.yaml
        self.dev_config = {
            "app": {
                "log_level": "DEBUG"
            },
            "database": {
                "path": "dev.db"
            }
        }
        
        with open(self.config_dir / "development.yaml", 'w') as f:
            yaml.dump(self.dev_config, f)
        
        # Create production.yaml
        self.prod_config = {
            "app": {
                "environment": "production",
                "log_level": "WARNING"
            },
            "database": {
                "type": "postgres",
                "host": "${DB_HOST|localhost}",
                "fallback_to_mock": False
            }
        }
        
        with open(self.config_dir / "production.yaml", 'w') as f:
            yaml.dump(self.prod_config, f)
        
        # Store original environment variables
        self.original_env = os.environ.get("APP_ENV")
        self.original_db_host = os.environ.get("DB_HOST")
        
        # Clear environment variables that might affect tests
        if "DB_HOST" in os.environ:
            del os.environ["DB_HOST"]
    
    def tearDown(self):
        """Clean up after test."""
        # Restore original environment variables
        if self.original_env:
            os.environ["APP_ENV"] = self.original_env
        elif "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]
        
        if self.original_db_host:
            os.environ["DB_HOST"] = self.original_db_host
        elif "DB_HOST" in os.environ:
            del os.environ["DB_HOST"]
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_default_environment(self):
        """Test loading with default environment."""
        # Default to development
        provider = EnvironmentFileProvider(self.config_dir)
        
        # Check environment
        self.assertEqual(provider.get_environment(), "development")
        
        # Check merged config values
        self.assertEqual(provider.get("app.name"), "IoTSphere")
        self.assertEqual(provider.get("app.log_level"), "DEBUG")  # Overridden by dev config
        self.assertEqual(provider.get("database.path"), "dev.db")  # Overridden by dev config
        self.assertEqual(provider.get("database.type"), "sqlite")  # From base config
        self.assertTrue(provider.get("database.fallback_to_mock"))  # From base config
    
    def test_production_environment(self):
        """Test loading with production environment."""
        # Set production environment
        os.environ["APP_ENV"] = "production"
        
        provider = EnvironmentFileProvider(self.config_dir)
        
        # Check environment
        self.assertEqual(provider.get_environment(), "production")
        
        # Check merged config values
        self.assertEqual(provider.get("app.name"), "IoTSphere")  # From base config
        self.assertEqual(provider.get("app.environment"), "production")  # Overridden by prod config
        self.assertEqual(provider.get("app.log_level"), "WARNING")  # Overridden by prod config
        self.assertEqual(provider.get("database.type"), "postgres")  # Overridden by prod config
        self.assertEqual(provider.get("database.host"), "localhost")  # From prod config with default
        self.assertFalse(provider.get("database.fallback_to_mock"))  # Overridden by prod config
    
    def test_environment_variable_substitution(self):
        """Test environment variable substitution."""
        # Set production environment and DB_HOST
        os.environ["APP_ENV"] = "production"
        os.environ["DB_HOST"] = "testdb.example.com"
        
        provider = EnvironmentFileProvider(self.config_dir)
        
        # Check environment variable substitution
        self.assertEqual(provider.get("database.host"), "testdb.example.com")
    
    def test_missing_base_config(self):
        """Test error handling for missing base config."""
        # Create empty temporary directory
        empty_dir = tempfile.TemporaryDirectory()
        
        # Should raise exception for missing config.yaml
        with self.assertRaises(ConfigurationProviderError):
            EnvironmentFileProvider(empty_dir.name)
        
        empty_dir.cleanup()
    
    def test_reload_config(self):
        """Test reloading configuration."""
        # Initial setup
        os.environ["APP_ENV"] = "development"
        provider = EnvironmentFileProvider(self.config_dir)
        self.assertEqual(provider.get("app.log_level"), "DEBUG")
        
        # Modify development.yaml
        modified_dev_config = self.dev_config.copy()
        modified_dev_config["app"]["log_level"] = "TRACE"
        
        with open(self.config_dir / "development.yaml", 'w') as f:
            yaml.dump(modified_dev_config, f)
        
        # Reload configuration
        provider.reload()
        
        # Check updated value
        self.assertEqual(provider.get("app.log_level"), "TRACE")


if __name__ == "__main__":
    unittest.main()
