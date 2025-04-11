"""
Configuration package initialization.

This module provides easy access to the configuration classes and instances.
"""

import os
from typing import Union, Type

from .base import BaseConfig
from .development import DevelopmentConfig, config as development_config
from .production import ProductionConfig, config as production_config
from .testing import TestingConfig, config as testing_config

# Configuration mapping
config_map = {
    'development': development_config,
    'production': production_config,
    'testing': testing_config
}

def get_config() -> Union[DevelopmentConfig, ProductionConfig, TestingConfig]:
    """
    Get the appropriate configuration based on the environment.
    
    Returns:
        Union[DevelopmentConfig, ProductionConfig, TestingConfig]: The configuration instance
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, development_config)

# Export the current configuration
config = get_config()

__all__ = [
    'BaseConfig',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'config',
    'get_config'
]
