"""
Configuration settings for the API module.

This module contains configuration settings for interacting with cryptocurrency exchanges,
particularly Binance, and economic data from FRED. It includes API endpoints, timeouts, and other settings.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Literal, List, Tuple, Optional
import json
from pathlib import Path

# Environment settings
# Use Literal for type hinting allowed environment values
env_value = os.getenv("API_ENV", "production")
if env_value not in ["production", "testnet", "development"]:
    env_value = "production"  # Default to production if invalid
ENV = env_value
DEBUG: bool = os.getenv("API_DEBUG", "false").lower() == "true"

@dataclass
class BinanceEnvConfig:
    """Configuration specific to a Binance environment (production/testnet)."""
    base_url: str
    ws_base_url: str
    futures_url: str
    api_key: str
    api_secret: str

@dataclass
class BinanceConfig:
    """Holds configuration for both production and testnet Binance environments."""
    # Use field with default_factory to load environment variables upon instantiation
    production: BinanceEnvConfig = field(default_factory=lambda: BinanceEnvConfig(
        base_url="https://api.binance.com",
        ws_base_url="wss://stream.binance.com:9443/ws",
        futures_url="https://fapi.binance.com",
        api_key=os.getenv("BINANCE_API_KEY", ""),
        api_secret=os.getenv("BINANCE_API_SECRET", "")
    ))
    testnet: BinanceEnvConfig = field(default_factory=lambda: BinanceEnvConfig(
        base_url="https://testnet.binance.vision",
        ws_base_url="wss://testnet.binance.vision/ws",
        futures_url="https://testnet.binancefuture.com",
        api_key=os.getenv("BINANCE_TESTNET_API_KEY", ""),
        api_secret=os.getenv("BINANCE_TESTNET_API_SECRET", "")
    ))

@dataclass
class FredConfig:
    """Configuration for FRED API."""
    base_url: str = "https://api.stlouisfed.org/fred"
    api_key: str = os.getenv("FRED_API_KEY", "")
    file_type: str = "json"  # Default response format
    version: str = "2"  # API version

@dataclass
class RequestConfig:
    """Configuration for HTTP requests."""
    timeout: int = int(os.getenv("API_REQUEST_TIMEOUT", "10"))  # seconds
    max_retries: int = int(os.getenv("API_MAX_RETRIES", "3"))
    retry_backoff_factor: float = float(os.getenv("API_RETRY_BACKOFF_FACTOR", "0.5"))

@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting."""
    enabled: bool = os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() == "true"
    requests: int = int(os.getenv("API_RATE_LIMIT_REQUESTS", "1200"))  # requests
    period: int = int(os.getenv("API_RATE_LIMIT_PERIOD", "60"))  # seconds

@dataclass
class WebSocketConfig:
    """Configuration for WebSocket connections."""
    reconnect_interval: int = int(os.getenv("API_WS_RECONNECT_INTERVAL", "5"))  # seconds
    ping_interval: int = int(os.getenv("API_WS_PING_INTERVAL", "30"))  # seconds
    ping_timeout: int = int(os.getenv("API_WS_PING_TIMEOUT", "10"))  # seconds

@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = os.getenv("API_LOG_LEVEL", "INFO")
    format: str = os.getenv("API_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@dataclass
class AppConfig:
    """Main application configuration class."""
    env = ENV
    debug: bool = DEBUG
    binance: BinanceConfig = field(default_factory=BinanceConfig)
    fred: FredConfig = field(default_factory=FredConfig)
    request: RequestConfig = field(default_factory=RequestConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def get_current_binance_config(self) -> BinanceEnvConfig:
        """Returns the Binance config for the current environment."""
        if self.env == "testnet":
            return self.binance.testnet
        # Default to production for 'production' or 'development' ENV values
        return self.binance.production

# Instantiate the main config object to be imported by other modules
settings = AppConfig()

# You can optionally export the specific environment config if needed frequently
# current_binance_config = settings.get_current_binance_config()

def load_config(config_file: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_file (Path): Path to the configuration file
        
    Returns:
        Dict[str, Any]: Configuration data
        
    Raises:
        ValueError: If the file cannot be read or contains invalid JSON
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Failed to load config file: {str(e)}")

def validate_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration data.
    
    Args:
        config_data (Dict[str, Any]): Configuration data to validate
        
    Returns:
        Dict[str, Any]: Validation result with success flag and errors
    """
    errors = []
    
    # Validate exchange section
    if "exchange" not in config_data:
        errors.append("Missing 'exchange' section")
    else:
        exchange = config_data["exchange"]
        if not isinstance(exchange, dict):
            errors.append("'exchange' must be an object")
        else:
            if "name" not in exchange:
                errors.append("Missing 'exchange.name'")
            if "api_key" not in exchange:
                errors.append("Missing 'exchange.api_key'")
            if "api_secret" not in exchange:
                errors.append("Missing 'exchange.api_secret'")
    
    # Validate trading section
    if "trading" not in config_data:
        errors.append("Missing 'trading' section")
    else:
        trading = config_data["trading"]
        if not isinstance(trading, dict):
            errors.append("'trading' must be an object")
        else:
            if "base_currency" not in trading:
                errors.append("Missing 'trading.base_currency'")
            if "trading_pairs" not in trading:
                errors.append("Missing 'trading.trading_pairs'")
            if "max_open_orders" not in trading:
                errors.append("Missing 'trading.max_open_orders'")
    
    # Validate risk management section
    if "risk_management" not in config_data:
        errors.append("Missing 'risk_management' section")
    else:
        risk = config_data["risk_management"]
        if not isinstance(risk, dict):
            errors.append("'risk_management' must be an object")
        else:
            if "max_position_size" not in risk:
                errors.append("Missing 'risk_management.max_position_size'")
            if "stop_loss_percentage" not in risk:
                errors.append("Missing 'risk_management.stop_loss_percentage'")
            if "take_profit_percentage" not in risk:
                errors.append("Missing 'risk_management.take_profit_percentage'")
    
    return {
        "success": len(errors) == 0,
        "errors": errors
    }

class Config:
    """Configuration class for managing API settings."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize the configuration."""
        # Validate config data
        validation = validate_config(config_data)
        if not validation["success"]:
            raise ValueError(f"Invalid configuration: {', '.join(validation['errors'])}")
        
        # Exchange settings
        exchange = config_data["exchange"]
        self.exchange_name = exchange["name"]
        self.api_key = exchange["api_key"]
        self.api_secret = exchange["api_secret"]
        self.testnet = exchange.get("testnet", False)
        
        # Trading settings
        trading = config_data["trading"]
        self.base_currency = trading["base_currency"]
        self.trading_pairs = trading["trading_pairs"]
        self.max_open_orders = trading["max_open_orders"]
        
        # Risk management settings
        risk = config_data["risk_management"]
        self.max_position_size = risk["max_position_size"]
        self.stop_loss_percentage = risk["stop_loss_percentage"]
        self.take_profit_percentage = risk["take_profit_percentage"]
