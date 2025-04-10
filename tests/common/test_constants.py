"""
Tests for the constants module.

This module contains tests to verify that all constants are properly defined
and accessible in the expected format.
"""

import pytest
from src.common.constants import (
    # Time intervals
    TimeInterval,
    INTERVAL_1M, INTERVAL_5M, INTERVAL_15M, INTERVAL_1H, INTERVAL_4H, INTERVAL_1D,
    
    # Trading constants
    TradingConstants,
    MAX_POSITION_SIZE, MIN_POSITION_SIZE, DEFAULT_LEVERAGE, MAX_LEVERAGE,
    
    # Risk management
    RiskConstants,
    MAX_DRAWDOWN, STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE,
    
    # API related
    APIConstants,
    API_RATE_LIMIT, API_TIMEOUT, WEBSOCKET_PING_INTERVAL,
    
    # Data storage
    DataConstants,
    DATA_CACHE_TTL, MAX_HISTORICAL_DAYS,
    
    # Logging
    LoggingConstants,
    LOG_LEVEL, LOG_FORMAT,
    
    # Database
    DatabaseConstants,
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT,
)


class TestTimeIntervals:
    """Tests for time interval constants."""
    
    def test_time_interval_enum(self):
        """Test that TimeInterval enum contains all expected values."""
        assert TimeInterval.ONE_MINUTE == '1m'
        assert TimeInterval.FIVE_MINUTES == '5m'
        assert TimeInterval.FIFTEEN_MINUTES == '15m'
        assert TimeInterval.ONE_HOUR == '1h'
        assert TimeInterval.FOUR_HOURS == '4h'
        assert TimeInterval.ONE_DAY == '1d'
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match enum values."""
        assert INTERVAL_1M == TimeInterval.ONE_MINUTE
        assert INTERVAL_5M == TimeInterval.FIVE_MINUTES
        assert INTERVAL_15M == TimeInterval.FIFTEEN_MINUTES
        assert INTERVAL_1H == TimeInterval.ONE_HOUR
        assert INTERVAL_4H == TimeInterval.FOUR_HOURS
        assert INTERVAL_1D == TimeInterval.ONE_DAY


class TestTradingConstants:
    """Tests for trading constants."""
    
    def test_trading_constants_class(self):
        """Test that TradingConstants class contains all expected values."""
        assert TradingConstants.MAX_POSITION_SIZE == 0.1
        assert TradingConstants.MIN_POSITION_SIZE == 0.01
        assert TradingConstants.DEFAULT_LEVERAGE == 1
        assert TradingConstants.MAX_LEVERAGE == 20
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert MAX_POSITION_SIZE == TradingConstants.MAX_POSITION_SIZE
        assert MIN_POSITION_SIZE == TradingConstants.MIN_POSITION_SIZE
        assert DEFAULT_LEVERAGE == TradingConstants.DEFAULT_LEVERAGE
        assert MAX_LEVERAGE == TradingConstants.MAX_LEVERAGE


class TestRiskConstants:
    """Tests for risk management constants."""
    
    def test_risk_constants_class(self):
        """Test that RiskConstants class contains all expected values."""
        assert RiskConstants.MAX_DRAWDOWN == 0.15
        assert RiskConstants.STOP_LOSS_PERCENTAGE == 0.02
        assert RiskConstants.TAKE_PROFIT_PERCENTAGE == 0.04
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert MAX_DRAWDOWN == RiskConstants.MAX_DRAWDOWN
        assert STOP_LOSS_PERCENTAGE == RiskConstants.STOP_LOSS_PERCENTAGE
        assert TAKE_PROFIT_PERCENTAGE == RiskConstants.TAKE_PROFIT_PERCENTAGE


class TestAPIConstants:
    """Tests for API-related constants."""
    
    def test_api_constants_class(self):
        """Test that APIConstants class contains all expected values."""
        assert APIConstants.RATE_LIMIT == 1200
        assert APIConstants.TIMEOUT == 30
        assert APIConstants.WEBSOCKET_PING_INTERVAL == 30
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert API_RATE_LIMIT == APIConstants.RATE_LIMIT
        assert API_TIMEOUT == APIConstants.TIMEOUT
        assert WEBSOCKET_PING_INTERVAL == APIConstants.WEBSOCKET_PING_INTERVAL


class TestDataConstants:
    """Tests for data storage constants."""
    
    def test_data_constants_class(self):
        """Test that DataConstants class contains all expected values."""
        assert DataConstants.CACHE_TTL == 3600
        assert DataConstants.MAX_HISTORICAL_DAYS == 365
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert DATA_CACHE_TTL == DataConstants.CACHE_TTL
        assert MAX_HISTORICAL_DAYS == DataConstants.MAX_HISTORICAL_DAYS


class TestLoggingConstants:
    """Tests for logging constants."""
    
    def test_logging_constants_class(self):
        """Test that LoggingConstants class contains all expected values."""
        assert LoggingConstants.LEVEL == 'INFO'
        assert LoggingConstants.FORMAT == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert LOG_LEVEL == LoggingConstants.LEVEL
        assert LOG_FORMAT == LoggingConstants.FORMAT


class TestDatabaseConstants:
    """Tests for database constants."""
    
    def test_database_constants_class(self):
        """Test that DatabaseConstants class contains all expected values."""
        assert DatabaseConstants.POOL_SIZE == 5
        assert DatabaseConstants.MAX_OVERFLOW == 10
        assert DatabaseConstants.POOL_TIMEOUT == 30
    
    def test_backward_compatibility(self):
        """Test that backward compatibility constants match class values."""
        assert DB_POOL_SIZE == DatabaseConstants.POOL_SIZE
        assert DB_MAX_OVERFLOW == DatabaseConstants.MAX_OVERFLOW
        assert DB_POOL_TIMEOUT == DatabaseConstants.POOL_TIMEOUT 