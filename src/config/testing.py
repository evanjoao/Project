"""
Testing configuration settings.

This module contains configuration settings specific to the testing environment.
"""

from .base import BaseConfig

class TestingConfig(BaseConfig):
    """Testing configuration class."""
    
    # Override base settings for testing
    DEBUG: bool = False
    TESTING: bool = True
    
    # Testing-specific database settings
    DB_NAME: str = "crypto_trading_test"
    DATABASE_POOL_SIZE: int = 1
    DATABASE_MAX_OVERFLOW: int = 1
    DATABASE_ECHO: bool = False
    DATABASE_POOL_TIMEOUT: int = 5
    DATABASE_POOL_RECYCLE: int = 300  # 5 minutes
    
    # Testing-specific logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "logs/testing.log"
    
    # Testing-specific rate limiting
    RATELIMIT_DEFAULT: str = "1000 per minute"
    RATELIMIT_STORAGE_URL: str = "memory://"
    
    # Testing-specific cache settings
    CACHE_TYPE: str = "simple"
    CACHE_DEFAULT_TIMEOUT: int = 0
    
    # Testing-specific trading settings
    TRADING_PAIR: str = "BTC/USDT"
    MAX_OPEN_ORDERS: int = 1
    
    # Testing-specific risk management
    MAX_POSITION_SIZE: float = 0.01  # 1% del portfolio para testing
    STOP_LOSS_PERCENTAGE: float = 0.005  # 0.5%
    TAKE_PROFIT_PERCENTAGE: float = 0.01  # 1%

# Create an instance of the testing configuration
config = TestingConfig() 