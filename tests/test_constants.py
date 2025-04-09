"""Unit tests for the constants module."""

import pytest
from decimal import Decimal
from src.api.constants import (
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce,
    TradingPair,
    ExchangeName,
    ErrorCode
)

def test_order_type_enum():
    """Test OrderType enum values."""
    assert OrderType.MARKET.value == "market"
    assert OrderType.LIMIT.value == "limit"
    assert OrderType.STOP_LOSS.value == "stop_loss"
    assert OrderType.TAKE_PROFIT.value == "take_profit"

def test_order_side_enum():
    """Test OrderSide enum values."""
    assert OrderSide.BUY.value == "buy"
    assert OrderSide.SELL.value == "sell"

def test_order_status_enum():
    """Test OrderStatus enum values."""
    assert OrderStatus.OPEN.value == "open"
    assert OrderStatus.CLOSED.value == "closed"
    assert OrderStatus.CANCELED.value == "canceled"
    assert OrderStatus.EXPIRED.value == "expired"
    assert OrderStatus.REJECTED.value == "rejected"

def test_time_in_force_enum():
    """Test TimeInForce enum values."""
    assert TimeInForce.GTC.value == "GTC"  # Good Till Cancel
    assert TimeInForce.IOC.value == "IOC"  # Immediate or Cancel
    assert TimeInForce.FOK.value == "FOK"  # Fill or Kill

def test_trading_pair_validation():
    """Test TradingPair validation."""
    # Valid pairs
    assert TradingPair.is_valid("BTC/USDT") is True
    assert TradingPair.is_valid("ETH/USDC") is True
    
    # Invalid pairs
    assert TradingPair.is_valid("BTC-USDT") is False
    assert TradingPair.is_valid("BTC") is False
    assert TradingPair.is_valid("") is False

def test_exchange_name_enum():
    """Test ExchangeName enum values."""
    assert ExchangeName.BINANCE.value == "binance"
    assert ExchangeName.COINBASE.value == "coinbase"
    assert ExchangeName.KRAKEN.value == "kraken"

def test_error_code_enum():
    """Test ErrorCode enum values."""
    assert ErrorCode.INVALID_PARAMETER.value == "INVALID_PARAMETER"
    assert ErrorCode.INSUFFICIENT_FUNDS.value == "INSUFFICIENT_FUNDS"
    assert ErrorCode.ORDER_NOT_FOUND.value == "ORDER_NOT_FOUND"
    assert ErrorCode.NETWORK_ERROR.value == "NETWORK_ERROR"
    assert ErrorCode.EXCHANGE_ERROR.value == "EXCHANGE_ERROR"
