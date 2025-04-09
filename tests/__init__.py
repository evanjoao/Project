"""Test utilities for the Binance API integration.

This module provides common test fixtures, mock data generators, and assertion helpers
for testing the Binance API integration.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, cast
from unittest.mock import AsyncMock, patch
import random
import string

# Test Configuration
pytest_plugins = ['pytest_asyncio']

# Base Fixtures
@pytest.fixture
def mock_decimal():
    """Fixture to ensure consistent decimal handling in tests."""
    return Decimal

@pytest.fixture
def mock_datetime():
    """Fixture to ensure consistent datetime handling in tests."""
    return datetime

@pytest.fixture
def mock_binance_client():
    """Fixture to create a mock Binance client."""
    with patch('ccxt.async_support.binance') as mock_binance:
        yield mock_binance

# Mock Data Generators
def generate_order_id(length=10):
    """Generate a random order ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_mock_order(
    symbol="BTC/USDT",
    order_type="limit",
    side="buy",
    price=50000.0,
    amount=1.0,
    status="new"
):
    """Create a mock order response."""
    current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        'id': generate_order_id(),
        'symbol': symbol,
        'type': order_type,
        'side': side,
        'price': str(price),
        'amount': str(amount),
        'status': status,
        'timestamp': current_time,
        'datetime': datetime.fromtimestamp(current_time / 1000, timezone.utc).isoformat(),
        'filled': '0.0',
        'remaining': str(amount),
        'cost': '0.0',
        'fee': None
    }

def create_mock_trade(
    symbol="BTC/USDT",
    side="buy",
    price=50000.0,
    amount=1.0,
    fee=0.1
):
    """Create a mock trade response."""
    current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        'id': generate_order_id(),
        'symbol': symbol,
        'order': generate_order_id(),
        'type': 'limit',
        'side': side,
        'price': str(price),
        'amount': str(amount),
        'cost': str(price * amount),
        'fee': {'cost': str(fee), 'currency': 'USDT'},
        'timestamp': current_time,
        'datetime': datetime.fromtimestamp(current_time / 1000, timezone.utc).isoformat()
    }

# Assertion Helpers
def assert_decimal_equal(actual: Decimal, expected: Decimal, places: int = 8) -> None:
    """Assert that two Decimal values are equal within a specified precision."""
    assert abs(actual - expected) < Decimal('0.1') ** places

def assert_order_valid(order: Dict[str, Any]) -> None:
    """Assert that an order object has all required fields and valid values."""
    required_fields = ['id', 'symbol', 'type', 'side', 'price', 'amount', 'status']
    for field in required_fields:
        assert field in order
        assert order[field] is not None
    
    assert Decimal(cast(Dict[str, str], order)['price']) > 0
    assert Decimal(cast(Dict[str, str], order)['amount']) > 0
    assert cast(Dict[str, str], order)['status'] in ['new', 'open', 'closed', 'canceled', 'expired', 'rejected']

# Environment Setup
def setup_test_environment():
    """Set up the test environment with default configurations."""
    return {
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'testnet': True,
        'timeout': 30000,
        'enableRateLimit': True
    } 