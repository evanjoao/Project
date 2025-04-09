"""Unit tests for the types module."""

import pytest
from decimal import Decimal
from datetime import datetime
import time
from ..api_types import Order, Price, Quantity, Timestamp
from ..exchange_interface import TradeInfo, OrderBookEntry, OrderInfo, OrderStatus, OrderType, OrderSide

def test_order_creation():
    """Test Order object creation and properties."""
    current_time = int(time.time() * 1000)  # Convert to milliseconds
    order = Order(
        symbol="BTC/USDT",
        orderId="123",
        clientOrderId="client123",
        price=50000.0,  # float instead of Decimal
        origQty=1.0,    # float instead of Decimal
        executedQty=0.0, # float instead of Decimal
        cummulativeQuoteQty=0.0,
        status="NEW",   # Use string literal instead of enum
        timeInForce="GTC",
        type="LIMIT",   # Use string literal instead of enum
        side="BUY",     # Use string literal instead of enum
        stopPrice=None,
        icebergQty=None,
        time=current_time,
        updateTime=current_time,
        isWorking=True,
        origQuoteOrderQty=None
    )
    
    assert order.orderId == "123"
    assert order.symbol == "BTC/USDT"
    assert order.type == "LIMIT"
    assert order.side == "BUY"
    assert order.origQty == 1.0
    assert order.price == 50000.0
    assert order.status == "NEW"

def test_trade_creation():
    """Test Trade object creation and properties."""
    trade = TradeInfo(
        trade_id="456",
        order_id="123",
        symbol="BTC/USDT",
        side=OrderSide.BUY,  # Use enum value
        amount=Decimal("0.5"),
        price=Decimal("50000.0"),
        timestamp=datetime.now(),
        fee=Decimal("0.1"),
        fee_currency="USDT"
    )
    
    assert trade.trade_id == "456"
    assert trade.order_id == "123"
    assert trade.symbol == "BTC/USDT"
    assert trade.side == OrderSide.BUY  # Use enum value
    assert trade.amount == Decimal("0.5")
    assert trade.price == Decimal("50000.0")
    assert trade.fee == Decimal("0.1")
    assert trade.fee_currency == "USDT"

def test_order_book_entry_creation():
    """Test OrderBookEntry object creation and properties."""
    entry = OrderBookEntry(
        price=Decimal("50000.0"),
        amount=Decimal("1.0"),
        timestamp=datetime.now()
    )
    
    assert entry.price == Decimal("50000.0")
    assert entry.amount == Decimal("1.0")

def test_order_info_creation():
    """Test OrderInfo object creation and properties."""
    order_info = OrderInfo(
        order_id="123",
        symbol="BTC/USDT",
        order_type=OrderType.LIMIT,  # Use enum value
        side=OrderSide.BUY,  # Use enum value
        amount=Decimal("1.0"),
        price=Decimal("50000.0"),
        status=OrderStatus.OPEN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        filled_amount=Decimal("0.0"),
        average_price=None
    )
    
    assert order_info.order_id == "123"
    assert order_info.symbol == "BTC/USDT"
    assert order_info.order_type == OrderType.LIMIT  # Use enum value
    assert order_info.side == OrderSide.BUY  # Use enum value
    assert order_info.amount == Decimal("1.0")
    assert order_info.price == Decimal("50000.0")
    assert order_info.status == OrderStatus.OPEN
