"""
API Configuration Module

This module handles the loading and validation of API configuration settings from YAML files.
It provides a type-safe interface for accessing API configuration parameters and includes
validation to ensure the configuration meets the required specifications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any, ClassVar

import yaml
from pydantic import BaseModel, Field, model_validator, field_validator

class EndpointConfig(BaseModel):
    """Configuration for API endpoints."""
    market_data: Optional[str] = None
    order_book: Optional[str] = None
    recent_trades: Optional[str] = None
    klines: Optional[str] = None
    series: Optional[str] = None
    series_observations: Optional[str] = None
    series_tags: Optional[str] = None
    series_related_tags: Optional[str] = None
    category: Optional[str] = None
    category_children: Optional[str] = None
    category_series: Optional[str] = None
    category_related_tags: Optional[str] = None
    category_tags: Optional[str] = None
    tags: Optional[str] = None
    related_tags: Optional[str] = None
    tag_series: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def validate_endpoints(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that at least one endpoint is provided."""
        if isinstance(values, dict):
            # Check if any endpoint is provided
            has_endpoint = any(
                values.get(field) is not None 
                for field in [
                    "market_data", "order_book", "recent_trades", "klines",
                    "series", "series_observations", "series_tags", "series_related_tags",
                    "category", "category_children", "category_series", "category_related_tags",
                    "category_tags", "tags", "related_tags", "tag_series"
                ]
            )
            if not has_endpoint:
                raise ValueError("At least one endpoint must be provided")
        return values

class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: int
    weight_per_minute: Optional[int] = None

class WebsocketConfig(BaseModel):
    """WebSocket configuration."""
    enabled: bool
    ping_interval: Optional[int] = None
    reconnect_delay: Optional[int] = None

class ExchangeConfig(BaseModel):
    """Configuration for a specific exchange."""
    enabled: bool
    api_version: str
    base_url: str
    testnet_url: Optional[str] = None
    sandbox_url: Optional[str] = None
    endpoints: EndpointConfig
    rate_limits: RateLimitConfig
    supported_pairs: Optional[List[str]] = None
    supported_series: Optional[List[str]] = None
    websocket: WebsocketConfig

    @model_validator(mode='before')
    @classmethod
    def validate_supported_items(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that at least one supported item is provided."""
        if isinstance(values, dict):
            # For Binance, supported_pairs is required
            if "binance" in values.get("api_version", "") and not values.get("supported_pairs"):
                raise ValueError("At least one supported pair must be provided for Binance")
        return values

class AuthTemplate(BaseModel):
    """Authentication template configuration."""
    api_key: str
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def validate_api_secret(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that api_secret is provided for exchanges that require it."""
        if isinstance(values, dict):
            api_key = values.get("api_key", "")
            api_secret = values.get("api_secret")
            
            if "binance" in api_key and api_secret is None:
                raise ValueError("API secret is required for Binance")
        return values

class GlobalConfig(BaseModel):
    """Global API settings."""
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_pause: int = 1
    log_level: str = "INFO"

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform global configuration."""
        if isinstance(values, dict):
            values.setdefault('timeout', 30)
            values.setdefault('retry_attempts', 3)
            values.setdefault('rate_limit_pause', 1)
            values.setdefault('log_level', "INFO")
        return values

class WebsocketGlobalConfig(BaseModel):
    """Global WebSocket settings."""
    default_channels: List[str]
    buffer_size: int
    max_reconnect_attempts: int
    connection_timeout: int

class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""
    max_retries: int = 3
    backoff_factor: int = 2
    retry_on_status: List[int] = [429, 500, 502, 503, 504]

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform error configuration."""
        if isinstance(values, dict):
            values.setdefault('max_retries', 3)
            values.setdefault('backoff_factor', 2)
            values.setdefault('retry_on_status', [429, 500, 502, 503, 504])
        return values

class ValidationConfig(BaseModel):
    """Data validation configuration."""
    price_precision: int
    amount_precision: int
    min_order_amount: float
    max_order_amount: float

class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    health_check_interval: int
    alert_thresholds: Dict[str, Union[float, int]]
    metrics: Dict[str, Union[bool, int]]

class APIConfig(BaseModel):
    """Complete API configuration."""
    global_settings: GlobalConfig = Field(..., alias="global")
    exchanges: Dict[str, ExchangeConfig]
    auth_templates: Dict[str, AuthTemplate]
    websocket: WebsocketGlobalConfig
    error_handling: ErrorHandlingConfig
    validation: ValidationConfig
    monitoring: MonitoringConfig

    @field_validator("global_settings")
    @classmethod
    def validate_log_level(cls, v: GlobalConfig) -> GlobalConfig:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.log_level.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform API configuration."""
        if isinstance(values, dict):
            # Set default values if not provided
            values.setdefault('global_settings', {})
            values.setdefault('error_handling', {})
            values.setdefault('exchanges', {})
            values.setdefault('auth_templates', {})
            values.setdefault('websocket', {})
            values.setdefault('validation', {})
            values.setdefault('monitoring', {})
        return values

    @field_validator('global_settings')
    @classmethod
    def validate_global_settings(cls, v: Any) -> GlobalConfig:
        """Validate global settings."""
        if isinstance(v, dict):
            return GlobalConfig(**v)
        return v

class APIConfigManager:
    """Manager class for handling API configuration."""
    
    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize the API configuration manager.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config: Optional[APIConfig] = None

    def load_config(self) -> APIConfig:
        """
        Load and validate the API configuration.

        Returns:
            APIConfig: Validated configuration object

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration doesn't meet validation requirements
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f)

        self._config = APIConfig.model_validate(config_data)
        return self._config

    @property
    def config(self) -> APIConfig:
        """
        Get the current configuration.

        Returns:
            APIConfig: The current configuration

        Raises:
            RuntimeError: If configuration hasn't been loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def get_exchange_config(self, exchange: str) -> ExchangeConfig:
        """
        Get configuration for a specific exchange.

        Args:
            exchange: Name of the exchange

        Returns:
            ExchangeConfig: Configuration for the specified exchange

        Raises:
            KeyError: If the exchange doesn't exist in the configuration
        """
        return self.config.exchanges[exchange]

    def get_auth_template(self, exchange: str) -> AuthTemplate:
        """
        Get authentication template for a specific exchange.

        Args:
            exchange: Name of the exchange

        Returns:
            AuthTemplate: Authentication template for the specified exchange

        Raises:
            KeyError: If the exchange doesn't exist in the configuration
        """
        return self.config.auth_templates[exchange]

    def is_exchange_enabled(self, exchange: str) -> bool:
        """
        Check if a specific exchange is enabled.

        Args:
            exchange: Name of the exchange

        Returns:
            bool: True if the exchange is enabled, False otherwise

        Raises:
            KeyError: If the exchange doesn't exist in the configuration
        """
        return self.config.exchanges[exchange].enabled
        
    def get_supported_items(self, exchange: str) -> List[str]:
        """
        Get supported pairs or series for a specific exchange.

        Args:
            exchange: Name of the exchange

        Returns:
            List[str]: List of supported pairs or series

        Raises:
            KeyError: If the exchange doesn't exist in the configuration
        """
        exchange_config = self.config.exchanges[exchange]
        if exchange == "binance":
            return exchange_config.supported_pairs or []
        elif exchange == "fred":
            return exchange_config.supported_series or []
        return []
        
    def is_websocket_enabled(self, exchange: str) -> bool:
        """
        Check if WebSocket is enabled for a specific exchange.

        Args:
            exchange: Name of the exchange

        Returns:
            bool: True if WebSocket is enabled, False otherwise

        Raises:
            KeyError: If the exchange doesn't exist in the configuration
        """
        return self.config.exchanges[exchange].websocket.enabled 