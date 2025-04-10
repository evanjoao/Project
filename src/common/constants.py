"""
Common constants used throughout the project.

This module defines constants used across the trading application, including
time intervals, trading parameters, risk management settings, API configurations,
and system settings.
"""

from enum import Enum
from typing import Dict, Any, Final

# Time intervals
class TimeInterval(str, Enum):
    """Enumeration of time intervals used for data aggregation and analysis."""
    ONE_MINUTE = '1m'
    FIVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    ONE_HOUR = '1h'
    FOUR_HOURS = '4h'
    ONE_DAY = '1d'

# Trading constants
class TradingConstants:
    """Constants related to trading operations and position sizing."""
    MAX_POSITION_SIZE: Final[float] = 0.1  # Maximum position size as percentage of portfolio
    MIN_POSITION_SIZE: Final[float] = 0.01  # Minimum position size as percentage of portfolio
    DEFAULT_LEVERAGE: Final[int] = 1
    MAX_LEVERAGE: Final[int] = 20

# Risk management
class RiskConstants:
    """Constants related to risk management and position protection."""
    MAX_DRAWDOWN: Final[float] = 0.15  # Maximum allowed drawdown
    STOP_LOSS_PERCENTAGE: Final[float] = 0.02  # Default stop loss percentage
    TAKE_PROFIT_PERCENTAGE: Final[float] = 0.04  # Default take profit percentage

# API related
class APIConstants:
    """Constants related to API interactions and rate limiting."""
    RATE_LIMIT: Final[int] = 1200  # Requests per minute
    TIMEOUT: Final[int] = 30  # Seconds
    WEBSOCKET_PING_INTERVAL: Final[int] = 30  # Seconds

# Data storage
class DataConstants:
    """Constants related to data storage and caching."""
    CACHE_TTL: Final[int] = 3600  # Time to live for cached data in seconds
    MAX_HISTORICAL_DAYS: Final[int] = 365  # Maximum days of historical data to store

# Logging
class LoggingConstants:
    """Constants related to logging configuration."""
    LEVEL: Final[str] = 'INFO'
    FORMAT: Final[str] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Database
class DatabaseConstants:
    """Constants related to database connection pooling."""
    POOL_SIZE: Final[int] = 5
    MAX_OVERFLOW: Final[int] = 10
    POOL_TIMEOUT: Final[int] = 30

# For backward compatibility
# These mappings allow existing code to continue working without changes
INTERVAL_1M: Final[str] = TimeInterval.ONE_MINUTE
INTERVAL_5M: Final[str] = TimeInterval.FIVE_MINUTES
INTERVAL_15M: Final[str] = TimeInterval.FIFTEEN_MINUTES
INTERVAL_1H: Final[str] = TimeInterval.ONE_HOUR
INTERVAL_4H: Final[str] = TimeInterval.FOUR_HOURS
INTERVAL_1D: Final[str] = TimeInterval.ONE_DAY

MAX_POSITION_SIZE: Final[float] = TradingConstants.MAX_POSITION_SIZE
MIN_POSITION_SIZE: Final[float] = TradingConstants.MIN_POSITION_SIZE
DEFAULT_LEVERAGE: Final[int] = TradingConstants.DEFAULT_LEVERAGE
MAX_LEVERAGE: Final[int] = TradingConstants.MAX_LEVERAGE

MAX_DRAWDOWN: Final[float] = RiskConstants.MAX_DRAWDOWN
STOP_LOSS_PERCENTAGE: Final[float] = RiskConstants.STOP_LOSS_PERCENTAGE
TAKE_PROFIT_PERCENTAGE: Final[float] = RiskConstants.TAKE_PROFIT_PERCENTAGE

API_RATE_LIMIT: Final[int] = APIConstants.RATE_LIMIT
API_TIMEOUT: Final[int] = APIConstants.TIMEOUT
WEBSOCKET_PING_INTERVAL: Final[int] = APIConstants.WEBSOCKET_PING_INTERVAL

DATA_CACHE_TTL: Final[int] = DataConstants.CACHE_TTL
MAX_HISTORICAL_DAYS: Final[int] = DataConstants.MAX_HISTORICAL_DAYS

LOG_LEVEL: Final[str] = LoggingConstants.LEVEL
LOG_FORMAT: Final[str] = LoggingConstants.FORMAT

DB_POOL_SIZE: Final[int] = DatabaseConstants.POOL_SIZE
DB_MAX_OVERFLOW: Final[int] = DatabaseConstants.MAX_OVERFLOW
DB_POOL_TIMEOUT: Final[int] = DatabaseConstants.POOL_TIMEOUT
