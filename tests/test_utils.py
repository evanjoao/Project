"""Unit tests for the utils module."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from ..utils import (
    format_binance_order_response,
    convert_binance_timeframe,
    validate_symbol,
    format_number
)

def test_format_binance_order_response():
    """Test Binance order response formatting."""
    response = {
        'orderId': '123',
        'symbol': 'BTCUSDT',
        'price': '50000.0',
        'origQty': '1.0',
        'status': 'NEW',
        'side': 'BUY',
        'type': 'LIMIT',
        'time': 1617123456789
    }
    
    formatted = format_binance_order_response(response)
    
    assert formatted['order_id'] == '123'
    assert formatted['symbol'] == 'BTCUSDT'
    assert formatted['price'] == Decimal('50000.0')
    assert formatted['quantity'] == Decimal('1.0')
    assert formatted['status'] == 'new'
    assert formatted['side'] == 'buy'
    assert formatted['type'] == 'limit'
    assert isinstance(formatted['timestamp'], datetime)

def test_convert_binance_timeframe():
    """Test timeframe conversion."""
    assert convert_binance_timeframe('1h') == '1h'
    assert convert_binance_timeframe('4h') == '4h'
    assert convert_binance_timeframe('1d') == '1d'
    assert convert_binance_timeframe('invalid') == '1h'  # Default fallback

def test_validate_symbol():
    """Test symbol validation."""
    assert validate_symbol('BTCUSDT') is True
    assert validate_symbol('ETHUSDT') is True
    assert validate_symbol('btcusdt') is False  # Must be uppercase
    assert validate_symbol('BTC') is False  # Too short
    assert validate_symbol('123') is False  # Must be a valid symbol format

def test_format_number():
    """Test number formatting."""
    assert format_number(1.23456789, 2) == '1.23'
    assert format_number(1.23456789, 4) == '1.2346'
    assert format_number(1.0, 2) == '1'
    assert format_number(0, 2) == '0'
