"""
Tests for the API type definitions and data structures.
"""

import pytest
import time
from typing import Optional
from ..api_types import (
    Symbol,
    OrderID,
    Timestamp,
    Price,
    Quantity,
    OrderSide,
    OrderType,
    OrderStatus,
    TickerInfo,
    Order,
    AccountBalance,
    ApiErrorData
)

def test_primitive_type_aliases():
    """Test primitive type aliases."""
    symbol: Symbol = "BTCUSDT"
    order_id: OrderID = "12345"
    ts: Timestamp = int(time.time() * 1000)
    price: Price = 50000.1
    qty: Quantity = 0.001
    
    assert isinstance(symbol, str)
    assert isinstance(order_id, str)
    assert isinstance(ts, int)
    assert isinstance(price, float)
    assert isinstance(qty, float)

def test_order_side_literal():
    """Test OrderSide literal type."""
    valid_sides: list[OrderSide] = ["BUY", "SELL"]
    for side in valid_sides:
        assert side in ["BUY", "SELL"]
    
    # This should raise a type error in static type checking
    # invalid_side: OrderSide = "INVALID"  # type: ignore

def test_order_type_literal():
    """Test OrderType literal type."""
    valid_types: list[OrderType] = [
        "LIMIT",
        "MARKET",
        "STOP_LOSS",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT",
        "TAKE_PROFIT_LIMIT",
        "LIMIT_MAKER"
    ]
    for order_type in valid_types:
        assert order_type in valid_types
    
    # This should raise a type error in static type checking
    # invalid_type: OrderType = "INVALID"  # type: ignore

def test_order_status_literal():
    """Test OrderStatus literal type."""
    valid_statuses: list[OrderStatus] = [
        "NEW",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELED",
        "PENDING_CANCEL",
        "REJECTED",
        "EXPIRED"
    ]
    for status in valid_statuses:
        assert status in valid_statuses
    
    # This should raise a type error in static type checking
    # invalid_status: OrderStatus = "INVALID"  # type: ignore

def test_ticker_info():
    """Test TickerInfo TypedDict."""
    ticker = TickerInfo(symbol="ETHUSDT", price=4000.0)
    assert ticker["symbol"] == "ETHUSDT"
    assert ticker["price"] == 4000.0
    assert isinstance(ticker["symbol"], str)
    assert isinstance(ticker["price"], float)

def test_order():
    """Test Order NamedTuple."""
    ts = int(time.time() * 1000)
    order = Order(
        symbol="BTCUSDT",
        orderId="12345",
        clientOrderId="my_order_1",
        price=50000.1,
        origQty=0.001,
        executedQty=0.0,
        cummulativeQuoteQty=0.0,
        status="NEW",
        timeInForce="GTC",
        type="LIMIT",
        side="BUY",
        stopPrice=None,
        icebergQty=None,
        time=ts,
        updateTime=ts,
        isWorking=True,
        origQuoteOrderQty=None
    )
    
    assert order.symbol == "BTCUSDT"
    assert order.orderId == "12345"
    assert order.price == 50000.1
    assert order.origQty == 0.001
    assert order.status == "NEW"
    assert order.type == "LIMIT"
    assert order.side == "BUY"
    assert order.stopPrice is None
    assert order.icebergQty is None
    assert order.isWorking is True
    assert order.origQuoteOrderQty is None

def test_account_balance():
    """Test AccountBalance NamedTuple."""
    balance = AccountBalance(asset="BTC", free=1.5, locked=0.2)
    assert balance.asset == "BTC"
    assert balance.free == 1.5
    assert balance.locked == 0.2
    assert isinstance(balance.free, float)
    assert isinstance(balance.locked, float)

def test_api_error_data():
    """Test ApiErrorData TypedDict."""
    error_data = ApiErrorData(
        code=-1021,
        msg="Timestamp for this request was 1000ms ahead of the server time."
    )
    assert error_data["code"] == -1021
    assert "Timestamp" in error_data["msg"]
    assert isinstance(error_data["code"], int)
    assert isinstance(error_data["msg"], str)

def test_order_optional_fields():
    """Test Order NamedTuple with optional fields."""
    ts = int(time.time() * 1000)
    order = Order(
        symbol="BTCUSDT",
        orderId="12345",
        clientOrderId="my_order_1",
        price=50000.1,
        origQty=0.001,
        executedQty=0.0,
        cummulativeQuoteQty=0.0,
        status="NEW",
        timeInForce="GTC",
        type="LIMIT",
        side="BUY",
        stopPrice=51000.0,  # Optional field with value
        icebergQty=None,    # Optional field with None
        time=ts,
        updateTime=ts,
        isWorking=True,
        origQuoteOrderQty=50000.0  # Optional field with value
    )
    
    assert order.stopPrice == 51000.0
    assert order.icebergQty is None
    assert order.origQuoteOrderQty == 50000.0 