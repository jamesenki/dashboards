"""
Environment-specific configuration provider.

This provider loads configuration from environment-specific YAML files
based on the current runtime environment.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from src.config.providers import FileProvider, ConfigurationProvider
from src.config.exceptions import ConfigurationProviderError


class EnvironmentFileProvider(ConfigurationProvider):
    """Provider for environment-specific configuration files."""
    
    def __init__(self, 
                 base_path: Union[str, Path],
                 default_env: str = "development"):
        """
        Initialize with base path for configuration files.
        
        Args:
            base_path: Base directory containing configuration files
            default_env: Default environment to use if not specified
                
        Raises:
            ConfigurationProviderError: If configuration files can't be loaded
        """
        super().__init__()
        self._base_path = Path(base_path)
        self._default_env = default_env
        self._config = None
        self._env = None
        self._load_config()
    
    def _get_current_env(self) -> str:
        """
        Get the current environment from environment variable or default.
        
        Returns:
            Current environment name
        """
        # Check for environment variable, use default if not found
        return os.environ.get("APP_ENV", self._default_env).lower()
    
    def _load_config(self):
        """
        Load configuration from the appropriate environment file.
        
        This method loads the base config.yaml and then overlays
        environment-specific settings from [environment].yaml.
        
        Raises:
            ConfigurationProviderError: If configuration files can't be loaded
        """
        try:
            # Determine current environment
            self._env = self._get_current_env()
            
            # Load base configuration
            base_config_path = self._base_path / "config.yaml"
            if not base_config_path.exists():
                raise ConfigurationProviderError(f"Base configuration file not found: {base_config_path}")
            
            # Load base config
            base_provider = FileProvider(base_config_path)
            self._config = base_provider._get_config()
            
            # Check for environment-specific file
            env_file_path = self._base_path / f"{self._env}.yaml"
            if env_file_path.exists():
                # Load environment-specific config and merge with base config
                env_provider = FileProvider(env_file_path)
                env_config = env_provider._get_config()
                
                # Merge configurations
                self._config = self._deep_merge(self._config, env_config)
            
            # Process environment variable substitutions
            self._process_env_vars(self._config)
                
        except Exception as e:
            raise ConfigurationProviderError(f"Error loading environment configuration: {e}")
    
    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """
        Deep merge two dictionaries, with overlay values taking precedence.
        
        Args:
            base: Base dictionary
            overlay: Dictionary to overlay (takes precedence)
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in overlay.items():
            # If both are dictionaries, recursively merge
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                # Otherwise, overlay value takes precedence
                result[key] = value
                
        return result
    
    def _process_env_vars(self, config_dict: Dict, path: str = ""):
        """
        Process environment variable substitutions in the configuration.
        
        This replaces ${VAR_NAME} or ${VAR_NAME|default} placeholders with
        the corresponding environment variable values.
        
        Args:
            config_dict: Configuration dictionary to process
            path: Current path in the configuration (for debugging)
        """
        for key, value in config_dict.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                self._process_env_vars(value, current_path)
            elif isinstance(value, str) and "${" in value and "}" in value:
                # Process environment variable substitution
                start_idx = value.find("${")
                end_idx = value.find("}", start_idx)
                
                if start_idx != -1 and end_idx != -1:
                    var_spec = value[start_idx+2:end_idx]
                    
                    # Check for default value
                    if "|" in var_spec:
                        var_name, default_value = var_spec.split("|", 1)
                    else:
                        var_name, default_value = var_spec, ""
                    
                    # Get environment variable value
                    env_value = os.environ.get(var_name, default_value)
                    
                    # Replace in the config
                    config_dict[key] = value.replace(f"${{{var_spec}}}", env_value)
    
    def _get_config(self) -> Dict[str, Any]:
        """
        Get the merged configuration.
        
        Returns:
            Configuration dictionary
        """
        return self._config
    
    def reload(self):
        """Reload the configuration."""
        self._load_config()
    
    def get_environment(self) -> str:
        """
        Get the current environment.
        
        Returns:
            Current environment name
        """
        return self._env
