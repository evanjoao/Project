"""
Tests for the exceptions module.
"""

import pytest
from ..exceptions import (
    ExchangeError,
    ValidationError,
    ConfigurationError,
    NetworkError,
    OrderError,
    InsufficientFundsError
)

def test_exchange_error():
    """Test base exchange error."""
    error = ExchangeError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)

def test_validation_error():
    """Test validation error."""
    error = ValidationError("Invalid input")
    assert str(error) == "Invalid input"
    assert isinstance(error, ExchangeError)

def test_configuration_error():
    """Test configuration error."""
    error = ConfigurationError("Invalid config")
    assert str(error) == "Invalid config"
    assert isinstance(error, ExchangeError)

def test_network_error():
    """Test network error."""
    error = NetworkError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, ExchangeError)

def test_order_error():
    """Test order error."""
    error = OrderError("Order failed")
    assert str(error) == "Order failed"
    assert isinstance(error, ExchangeError)

def test_insufficient_funds_error():
    """Test insufficient funds error."""
    error = InsufficientFundsError("Not enough funds")
    assert str(error) == "Not enough funds"
    assert isinstance(error, OrderError)

def test_error_inheritance():
    """Test exception inheritance hierarchy."""
    assert issubclass(ValidationError, ExchangeError)
    assert issubclass(ConfigurationError, ExchangeError)
    assert issubclass(NetworkError, ExchangeError)
    assert issubclass(OrderError, ExchangeError)
    assert issubclass(InsufficientFundsError, OrderError)
    assert issubclass(InsufficientFundsError, ExchangeError)

def test_error_with_details():
    """Test error with additional details."""
    error = OrderError("Order failed", details={"order_id": "123", "reason": "invalid_price"})
    assert str(error) == "Order failed"
    assert error.details == {"order_id": "123", "reason": "invalid_price"}
