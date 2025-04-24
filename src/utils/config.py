import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration management class"""
    
    def __init__(self):
        """Initialize configuration with environment variables"""
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Server configuration
        self._config['PORT'] = int(os.getenv('PORT', 5000))
        self._config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
        self._config['ENV'] = os.getenv('ENV', 'development')
        
        # API configuration
        self._config['API_VERSION'] = os.getenv('API_VERSION', 'v1')
        self._config['API_PREFIX'] = os.getenv('API_PREFIX', '/api')
        
        # Logging configuration
        self._config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
        
        logger.info("Configuration loaded successfully")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        logger.debug(f"Configuration updated: {key}={value}")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values
        
        Returns:
            Dictionary containing all configuration
        """
        return self._config.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            Boolean indicating if configuration is valid
        """
        required_keys = ['PORT', 'ENV', 'API_VERSION']
        return all(key in self._config for key in required_keys) 