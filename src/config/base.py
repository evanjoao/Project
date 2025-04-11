"""
Base configuration settings for the application.

This module contains the base configuration class that will be extended by
environment-specific configurations (development, production, testing).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from pathlib import Path

@dataclass
class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application settings
    APP_NAME: str = "Bitcoin Trading Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    
    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800  # 7 days
    
    # Database settings
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "@Eleyfriki007")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "crypto_trading_dev")
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Cache settings
    CACHE_TYPE: str = "simple"
    CACHE_DEFAULT_TIMEOUT: int = 300
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Rate limiting
    RATELIMIT_DEFAULT: str = "100 per minute"
    RATELIMIT_STORAGE_URL: str = "memory://"
    
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
    
    # Trading settings
    TRADING_PAIR: str = "BTC/USDT"  # Solo Bitcoin
    MAX_OPEN_ORDERS: int = 5
    DEFAULT_ORDER_TYPE: str = "limit"
    DEFAULT_TIME_IN_FORCE: str = "GTC"
    
    # Risk management
    MAX_POSITION_SIZE: float = 0.1  # 10% del portfolio
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2%
    TAKE_PROFIT_PERCENTAGE: float = 0.04  # 4%
    
    @classmethod
    def load_from_file(cls, config_file: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        if not config_file.exists():
            return {}
        
        import json
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and not callable(v)}
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value) 