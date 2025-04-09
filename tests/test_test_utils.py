"""Tests for the test utilities module."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from . import (
    generate_order_id,
    create_mock_order,
    create_mock_trade,
    assert_decimal_equal,
    assert_order_valid,
    setup_test_environment
)

def test_generate_order_id():
    """Test order ID generation."""
    order_id = generate_order_id()
    assert len(order_id) == 10
    assert order_id.isalnum()
    assert order_id.isupper()

def test_create_mock_order():
    """Test mock order creation."""
    order = create_mock_order()
    assert_order_valid(order)
    assert order['symbol'] == "BTC/USDT"
    assert order['type'] == "limit"
    assert order['side'] == "buy"
    assert Decimal(order['price']) == Decimal('50000.0')
    assert Decimal(order['amount']) == Decimal('1.0')
    assert order['status'] == "new"

def test_create_mock_trade():
    """Test mock trade creation."""
    trade = create_mock_trade()
    assert trade['symbol'] == "BTC/USDT"
    assert trade['side'] == "buy"
    assert Decimal(trade['price']) == Decimal('50000.0')
    assert Decimal(trade['amount']) == Decimal('1.0')
    assert Decimal(trade['fee']['cost']) == Decimal('0.1')  # type: ignore
    assert trade['fee']['currency'] == "USDT"  # type: ignore
    assert 'timestamp' in trade
    assert 'datetime' in trade

def test_assert_decimal_equal():
    """Test decimal equality assertion."""
    assert_decimal_equal(Decimal('1.23456789'), Decimal('1.23456789'))
    assert_decimal_equal(Decimal('1.23456789'), Decimal('1.23456790'), places=7)
    
    with pytest.raises(AssertionError):
        assert_decimal_equal(Decimal('1.23456789'), Decimal('1.23456790'), places=8)

def test_assert_order_valid():
    """Test order validation assertion."""
    valid_order = create_mock_order()
    assert_order_valid(valid_order)
    
    invalid_order = valid_order.copy()
    invalid_order.pop('id')
    with pytest.raises(AssertionError):
        assert_order_valid(invalid_order)
    
    invalid_order = valid_order.copy()
    invalid_order['price'] = '-1'
    with pytest.raises(AssertionError):
        assert_order_valid(invalid_order)

def test_setup_test_environment():
    """Test test environment setup."""
    config = setup_test_environment()
    assert config['api_key'] == 'test_api_key'
    assert config['api_secret'] == 'test_api_secret'
    assert config['testnet'] is True
    assert config['timeout'] == 30000
    assert config['enableRateLimit'] is True 