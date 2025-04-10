"""
Tests for the exceptions module.

This module contains tests to verify that all custom exceptions are properly defined
and can be raised and caught as expected.
"""

import pytest
from src.common.exceptions import (
    # Base exceptions
    TradingError, APIError, DataError, ValidationError, ConfigurationError,
    
    # Trading exceptions
    InsufficientFundsError, OrderError, PositionError, RiskLimitError,
    
    # API exceptions
    RateLimitError, AuthenticationError, ConnectionError, APIResponseError,
    
    # Data exceptions
    DataFetchError, DataProcessingError, DataStorageError, DataNotFoundError,
    
    # Validation exceptions
    ParameterValidationError, DataValidationError,
    
    # Configuration exceptions
    MissingConfigError, InvalidConfigError,
)


class TestBaseExceptions:
    """Tests for the base exception classes."""
    
    def test_trading_error(self):
        """Test that TradingError can be raised and caught."""
        with pytest.raises(TradingError):
            raise TradingError("Test trading error")
    
    def test_api_error(self):
        """Test that APIError can be raised and caught."""
        with pytest.raises(APIError):
            raise APIError("Test API error")
    
    def test_data_error(self):
        """Test that DataError can be raised and caught."""
        with pytest.raises(DataError):
            raise DataError("Test data error")
    
    def test_validation_error(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")
    
    def test_configuration_error(self):
        """Test that ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test configuration error")


class TestTradingExceptions:
    """Tests for trading-related exceptions."""
    
    def test_insufficient_funds_error(self):
        """Test that InsufficientFundsError can be raised and caught."""
        with pytest.raises(InsufficientFundsError):
            raise InsufficientFundsError("Insufficient funds")
        
        # Test inheritance
        with pytest.raises(TradingError):
            raise InsufficientFundsError("Insufficient funds")
    
    def test_order_error(self):
        """Test that OrderError can be raised and caught."""
        with pytest.raises(OrderError):
            raise OrderError("Order error")
        
        # Test inheritance
        with pytest.raises(TradingError):
            raise OrderError("Order error")
    
    def test_position_error(self):
        """Test that PositionError can be raised and caught."""
        with pytest.raises(PositionError):
            raise PositionError("Position error")
        
        # Test inheritance
        with pytest.raises(TradingError):
            raise PositionError("Position error")
    
    def test_risk_limit_error(self):
        """Test that RiskLimitError can be raised and caught."""
        with pytest.raises(RiskLimitError):
            raise RiskLimitError("Risk limit exceeded")
        
        # Test inheritance
        with pytest.raises(TradingError):
            raise RiskLimitError("Risk limit exceeded")


class TestAPIExceptions:
    """Tests for API-related exceptions."""
    
    def test_rate_limit_error(self):
        """Test that RateLimitError can be raised and caught."""
        with pytest.raises(RateLimitError):
            raise RateLimitError("Rate limit exceeded")
        
        # Test inheritance
        with pytest.raises(APIError):
            raise RateLimitError("Rate limit exceeded")
    
    def test_authentication_error(self):
        """Test that AuthenticationError can be raised and caught."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Authentication failed")
        
        # Test inheritance
        with pytest.raises(APIError):
            raise AuthenticationError("Authentication failed")
    
    def test_connection_error(self):
        """Test that ConnectionError can be raised and caught."""
        with pytest.raises(ConnectionError):
            raise ConnectionError("Connection failed")
        
        # Test inheritance
        with pytest.raises(APIError):
            raise ConnectionError("Connection failed")
    
    def test_api_response_error(self):
        """Test that APIResponseError can be raised and caught."""
        with pytest.raises(APIResponseError):
            raise APIResponseError("Invalid API response")
        
        # Test inheritance
        with pytest.raises(APIError):
            raise APIResponseError("Invalid API response")


class TestDataExceptions:
    """Tests for data-related exceptions."""
    
    def test_data_fetch_error(self):
        """Test that DataFetchError can be raised and caught."""
        with pytest.raises(DataFetchError):
            raise DataFetchError("Failed to fetch data")
        
        # Test inheritance
        with pytest.raises(DataError):
            raise DataFetchError("Failed to fetch data")
    
    def test_data_processing_error(self):
        """Test that DataProcessingError can be raised and caught."""
        with pytest.raises(DataProcessingError):
            raise DataProcessingError("Failed to process data")
        
        # Test inheritance
        with pytest.raises(DataError):
            raise DataProcessingError("Failed to process data")
    
    def test_data_storage_error(self):
        """Test that DataStorageError can be raised and caught."""
        with pytest.raises(DataStorageError):
            raise DataStorageError("Failed to store data")
        
        # Test inheritance
        with pytest.raises(DataError):
            raise DataStorageError("Failed to store data")
    
    def test_data_not_found_error(self):
        """Test that DataNotFoundError can be raised and caught."""
        with pytest.raises(DataNotFoundError):
            raise DataNotFoundError("Data not found")
        
        # Test inheritance
        with pytest.raises(DataError):
            raise DataNotFoundError("Data not found")


class TestValidationExceptions:
    """Tests for validation-related exceptions."""
    
    def test_parameter_validation_error(self):
        """Test that ParameterValidationError can be raised and caught."""
        with pytest.raises(ParameterValidationError):
            raise ParameterValidationError("Invalid parameter")
        
        # Test inheritance
        with pytest.raises(ValidationError):
            raise ParameterValidationError("Invalid parameter")
    
    def test_data_validation_error(self):
        """Test that DataValidationError can be raised and caught."""
        with pytest.raises(DataValidationError):
            raise DataValidationError("Invalid data")
        
        # Test inheritance
        with pytest.raises(ValidationError):
            raise DataValidationError("Invalid data")


class TestConfigurationExceptions:
    """Tests for configuration-related exceptions."""
    
    def test_missing_config_error(self):
        """Test that MissingConfigError can be raised and caught."""
        with pytest.raises(MissingConfigError):
            raise MissingConfigError("Missing configuration")
        
        # Test inheritance
        with pytest.raises(ConfigurationError):
            raise MissingConfigError("Missing configuration")
    
    def test_invalid_config_error(self):
        """Test that InvalidConfigError can be raised and caught."""
        with pytest.raises(InvalidConfigError):
            raise InvalidConfigError("Invalid configuration")
        
        # Test inheritance
        with pytest.raises(ConfigurationError):
            raise InvalidConfigError("Invalid configuration") 