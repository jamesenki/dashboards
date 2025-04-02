"""
Mock Data Provider.

This module provides a configurable mock data provider that loads mock data
from external files rather than hardcoding it in the source code.
Following TDD principles, this makes tests more maintainable and
allows for different mock datasets per environment.
"""
import os
import json
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from src.config import config

# Configure logging
logger = logging.getLogger(__name__)


class MockDataProvider:
    """
    Provider for mock data that uses external configuration.
    
    This class loads mock data from files specified in configuration,
    making it easier to maintain different datasets for different
    environments or test scenarios.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the mock data provider."""
        if cls._instance is None:
            cls._instance = MockDataProvider()
        return cls._instance
    
    def __init__(self):
        """Initialize the mock data provider."""
        self.enabled = config.get_bool('testing.mocks.enabled', False)
        self.data_path = config.get('testing.mocks.data_path', './mocks')
        self.response_delay_ms = config.get_int('testing.mocks.response_delay_ms', 0)
        self.mock_data = {}
        
        # Load mock data if enabled
        if self.enabled:
            self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock data from external files."""
        data_path = Path(self.data_path)
        
        if not data_path.exists():
            logger.warning(f"Mock data path not found: {data_path}")
            return
        
        # Load all JSON and YAML files in the mock data directory
        for file_path in data_path.glob('**/*.json'):
            self._load_json_file(file_path)
        
        for file_path in data_path.glob('**/*.yaml'):
            self._load_yaml_file(file_path)
            
        logger.info(f"Loaded mock data for {len(self.mock_data)} categories")
    
    def _load_json_file(self, file_path: Path):
        """
        Load a JSON file into the mock data.
        
        Args:
            file_path: Path to the JSON file
        """
        try:
            relative_path = file_path.relative_to(self.data_path)
            category = str(relative_path.parent / relative_path.stem)
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self.mock_data[category] = data
            logger.debug(f"Loaded mock data from {file_path}")
        except Exception as e:
            logger.error(f"Error loading mock data from {file_path}: {e}")
    
    def _load_yaml_file(self, file_path: Path):
        """
        Load a YAML file into the mock data.
        
        Args:
            file_path: Path to the YAML file
        """
        try:
            relative_path = file_path.relative_to(self.data_path)
            category = str(relative_path.parent / relative_path.stem)
            
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                
            self.mock_data[category] = data
            logger.debug(f"Loaded mock data from {file_path}")
        except Exception as e:
            logger.error(f"Error loading mock data from {file_path}: {e}")
    
    def get_mock_data(self, category: str, default: Any = None) -> Any:
        """
        Get mock data for a specific category.
        
        Args:
            category: The category of mock data to retrieve
            default: Default value if category not found
            
        Returns:
            The mock data for the specified category or default if not found
        """
        # Simulate network delay if configured
        if self.response_delay_ms > 0:
            time.sleep(self.response_delay_ms / 1000)
            
        # Return mock data or default
        return self.mock_data.get(category, default)
    
    def is_enabled(self) -> bool:
        """
        Check if mock data is enabled.
        
        Returns:
            True if mock data is enabled, False otherwise
        """
        return self.enabled
    
    def is_mock_data_available(self, category: str) -> bool:
        """
        Check if mock data is available for a specific category.
        
        Args:
            category: The category to check
            
        Returns:
            True if mock data is available for the category, False otherwise
        """
        return category in self.mock_data
    
    def register_mock_data(self, category: str, data: Any):
        """
        Register mock data for a category at runtime.
        
        Args:
            category: The category to register
            data: The mock data to register
        """
        self.mock_data[category] = data
        logger.debug(f"Registered mock data for category: {category}")
    
    def clear_mock_data(self, category: str = None):
        """
        Clear mock data for a specific category or all mock data.
        
        Args:
            category: The category to clear, or None to clear all mock data
        """
        if category is None:
            self.mock_data = {}
            logger.debug("Cleared all mock data")
        elif category in self.mock_data:
            del self.mock_data[category]
            logger.debug(f"Cleared mock data for category: {category}")
    
    def reload(self):
        """Reload mock data from external files."""
        self.mock_data = {}
        self._load_mock_data()
        logger.info("Reloaded mock data")


# Singleton instance for global access
mock_data_provider = MockDataProvider.get_instance()
