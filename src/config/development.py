"""
Development configuration settings.

This module contains configuration settings specific to the development environment.
"""

from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development configuration class."""
    
    # Override base settings for development
    DEBUG: bool = True
    TESTING: bool = False
    
    # Development-specific database settings
    DB_NAME: str = "crypto_trading_dev"
    DATABASE_ECHO: bool = True  # Log all SQL queries in development
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Development-specific logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "logs/development.log"
    
    # Development-specific rate limiting
    RATELIMIT_DEFAULT: str = "1000 per minute"
    
    # Development-specific trading settings
    TRADING_PAIR: str = "BTC/USDT"
    MAX_OPEN_ORDERS: int = 3
    
    # Development-specific risk management
    MAX_POSITION_SIZE: float = 0.05  # 5% del portfolio para testing
    STOP_LOSS_PERCENTAGE: float = 0.01  # 1%
    TAKE_PROFIT_PERCENTAGE: float = 0.02  # 2%

# Create an instance of the development configuration
config = DevelopmentConfig() 