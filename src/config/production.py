"""
Production configuration settings.

This module contains configuration settings specific to the production environment.
"""

from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration class."""
    
    # Override base settings for production
    DEBUG: bool = False
    TESTING: bool = False
    
    # Production-specific database settings
    DB_NAME: str = "crypto_trading_prod"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_ECHO: bool = False
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800  # 30 minutes
    
    # Production-specific logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/production.log"
    
    # Production-specific rate limiting
    RATELIMIT_DEFAULT: str = "100 per minute"
    RATELIMIT_STORAGE_URL: str = "redis://localhost:6379/0"
    
    # Production-specific cache settings
    CACHE_TYPE: str = "redis"
    CACHE_REDIS_URL: str = "redis://localhost:6379/1"
    CACHE_DEFAULT_TIMEOUT: int = 600
    
    # Production-specific trading settings
    TRADING_PAIR: str = "BTC/USDT"
    MAX_OPEN_ORDERS: int = 5
    
    # Production-specific risk management
    MAX_POSITION_SIZE: float = 0.1  # 10% del portfolio
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2%
    TAKE_PROFIT_PERCENTAGE: float = 0.04  # 4%

# Create an instance of the production configuration
config = ProductionConfig()

# API settings
API_KEY = None  # Should be set via environment variable
API_SECRET = None  # Should be set via environment variable

# Security settings
ALLOWED_HOSTS = ["your-domain.com"]
SSL_ENABLED = True 