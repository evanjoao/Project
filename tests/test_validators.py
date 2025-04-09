"""
Unit tests for the validators module.
"""

import pytest
from datetime import datetime, timedelta
from ..validators import (
    validate_trading_pair,
    validate_api_key,
    validate_api_secret,
    validate_datetime_range,
    validate_numeric_range,
    NumericRange
)

def test_validate_trading_pair():
    # Valid cases
    assert validate_trading_pair("BTC/USDT") == (True, None)
    assert validate_trading_pair("ETH/USDC") == (True, None)
    assert validate_trading_pair("XRP/BTC") == (True, None)
    
    # Invalid cases
    assert validate_trading_pair("btc/usdt") == (False, "Invalid trading pair format. Expected format: BASE/QUOTE (e.g., BTC/USDT)")
    assert validate_trading_pair("BTC-USDT") == (False, "Invalid trading pair format. Expected format: BASE/QUOTE (e.g., BTC/USDT)")
    assert validate_trading_pair("BTC") == (False, "Invalid trading pair format. Expected format: BASE/QUOTE (e.g., BTC/USDT)")

def test_validate_api_key():
    # Valid cases
    assert validate_api_key("12345678901234567890123456789012") == (True, None)
    assert validate_api_key("abcdefghijklmnopqrstuvwxyz123456") == (True, None)
    
    # Invalid cases
    assert validate_api_key("short") == (False, "Invalid API key format")
    assert validate_api_key("12345678901234567890123456789012!") == (False, "Invalid API key format")

def test_validate_api_secret():
    # Valid cases
    secret = "1" * 64
    assert validate_api_secret(secret) == (True, None)
    
    # Invalid cases
    assert validate_api_secret("short") == (False, "Invalid API secret format")
    assert validate_api_secret("1" * 63) == (False, "Invalid API secret format")

def test_validate_datetime_range():
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    
    # Valid cases
    assert validate_datetime_range(past, now) == (True, None)
    assert validate_datetime_range(now, future) == (True, None)
    assert validate_datetime_range("2024-01-01", "2024-01-02") == (True, None)
    
    # Invalid cases
    assert validate_datetime_range(now, past) == (False, "End time must be after start time")
    assert validate_datetime_range("invalid", "2024-01-02") == (False, "Invalid datetime format: Unknown string format: invalid")

def test_validate_numeric_range():
    # Valid cases
    assert validate_numeric_range(5.0, 0.0, 10.0) == (True, None)
    assert validate_numeric_range(5.0) == (True, None)
    assert validate_numeric_range(5.0, min_value=0.0) == (True, None)
    assert validate_numeric_range(5.0, max_value=10.0) == (True, None)
    
    # Invalid cases
    assert validate_numeric_range(5.0, 10.0, 20.0) == (False, "Value must be greater than or equal to 10.0")
    assert validate_numeric_range(25.0, 10.0, 20.0) == (False, "Value must be less than or equal to 20.0")

def test_numeric_range_model():
    # Valid cases
    range_valid = NumericRange(value=5.0, min_value=0.0, max_value=10.0)
    assert range_valid.value == 5.0
    
    # Invalid cases - test min value validation
    with pytest.raises(ValueError):
        NumericRange(value=5.0, min_value=10.0, max_value=20.0)
    
    # Invalid cases - test max value validation
    with pytest.raises(ValueError):
        NumericRange(value=25.0, min_value=10.0, max_value=20.0) 