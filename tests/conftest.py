"""
Shared test fixtures and configuration.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Type, cast, Generator, TypeVar, Callable
from ..exchange_interface import (
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo,
    TradeInfo
)
from marshmallow import fields
from ..serializers import BaseSerializer
from ..exceptions import APIError
from ..binance_api import BinanceAPI
from ..binance_exchange import BinanceExchange
from unittest.mock import MagicMock, AsyncMock

T = TypeVar('T')

@pytest.fixture
def sample_order_info() -> OrderInfo:
    """Fixture providing a sample OrderInfo instance."""
    return OrderInfo(
        order_id="123",
        symbol="BTC/USDT",
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        amount=Decimal("1.0"),
        price=Decimal("50000.0"),
        status=OrderStatus.OPEN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        filled_amount=Decimal("0.0"),
        average_price=None
    )

@pytest.fixture
def sample_trade_info() -> TradeInfo:
    """Fixture providing a sample TradeInfo instance."""
    return TradeInfo(
        trade_id="123",
        order_id="456",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        amount=Decimal("1.0"),
        price=Decimal("50000.0"),
        timestamp=datetime.now(),
        fee=Decimal("0.1"),
        fee_currency="USDT"
    )

@pytest.fixture
def sample_order_book_entry() -> OrderBookEntry:
    """Fixture providing a sample OrderBookEntry instance."""
    return OrderBookEntry(
        price=Decimal("50000.0"),
        amount=Decimal("1.0"),
        timestamp=datetime.now()
    )

class SampleSerializer(BaseSerializer):
    """Sample serializer class for testing serialization functionality."""
    name = fields.Str(required=True)
    age = fields.Int(required=True)
    email = fields.Email(required=True)

@pytest.fixture
def test_serializer() -> Type[SampleSerializer]:
    """Fixture to provide SampleSerializer class."""
    return SampleSerializer

@pytest.fixture
def valid_serializer_data() -> Dict[str, Any]:
    """Fixture providing valid test data for serializer tests."""
    return {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    }

@pytest.fixture
def invalid_serializer_data() -> Dict[str, Any]:
    """Fixture providing invalid test data for serializer tests."""
    return {
        "name": "John Doe",
        "age": "not_a_number",
        "email": "invalid_email"
    }

@pytest.fixture
def mock_response() -> Dict[str, Any]:
    """Fixture providing a mock API response."""
    return {
        "status": "success",
        "data": {
            "price": "50000.0",
            "volume": "1.0"
        }
    }

@pytest.fixture
def mock_binance_api() -> MagicMock:
    """Fixture providing a mock BinanceAPI instance."""
    api = MagicMock(spec=BinanceAPI)
    api.get_exchange_info = AsyncMock(return_value={
        "symbols": [{
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "filters": [
                {
                    "filterType": "PRICE_FILTER",
                    "minPrice": "0.01",
                    "maxPrice": "1000000.00",
                    "tickSize": "0.01"
                },
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00000100",
                    "maxQty": "100000.00000000",
                    "stepSize": "0.00000100"
                }
            ]
        }]
    })
    api.get_order_book = AsyncMock(return_value={
        "lastUpdateId": 123456,
        "bids": [["50000.0", "1.0"]],
        "asks": [["50100.0", "1.0"]]
    })
    api.create_order = AsyncMock(return_value={
        "orderId": "123",
        "symbol": "BTCUSDT",
        "status": "NEW",
        "clientOrderId": "test_order",
        "transactTime": int(datetime.now().timestamp() * 1000)
    })
    api.get_order = AsyncMock(return_value={
        "orderId": "123",
        "symbol": "BTCUSDT",
        "status": "NEW",
        "clientOrderId": "test_order",
        "price": "50000.0",
        "origQty": "1.0",
        "executedQty": "0.0",
        "type": "LIMIT",
        "side": "BUY",
        "time": int(datetime.now().timestamp() * 1000),
        "updateTime": int(datetime.now().timestamp() * 1000)
    })
    api.cancel_order = AsyncMock(return_value={
        "orderId": "123",
        "symbol": "BTCUSDT",
        "status": "CANCELED",
        "clientOrderId": "test_order",
        "transactTime": int(datetime.now().timestamp() * 1000)
    })
    return api

@pytest.fixture
def mock_binance_exchange(mock_binance_api: MagicMock) -> BinanceExchange:
    """Fixture providing a mock BinanceExchange instance."""
    exchange = BinanceExchange(api_key="test_key", api_secret="test_secret")
    setattr(exchange, '_api', mock_binance_api)
    return exchange

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Fixture providing an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
