"""
Tests for the exchange interface implementation.
"""

from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from typing import List, Tuple

from ..exchange_interface import (
    OrderBookEntry,
    OrderInfo,
    OrderType,
    OrderSide,
    OrderStatus,
    TradeInfo
)
from ..binance_exchange import BinanceExchange

@pytest.fixture
def mock_ccxt():
    """Fixture providing a mocked CCXT exchange."""
    with patch('ccxt.async_support.binance') as mock:
        mock_exchange = AsyncMock()
        mock_exchange.set_sandbox_mode = Mock()  # Regular mock, not async
        mock.return_value = mock_exchange
        yield mock

@pytest.fixture
def binance_exchange(mock_ccxt):
    """Fixture providing a BinanceExchange instance."""
    exchange = BinanceExchange(
        api_key="test_key",
        api_secret="test_secret",
        testnet=True
    )
    return exchange

@pytest.mark.asyncio
async def test_get_ticker_price(binance_exchange, mock_ccxt):
    """Test getting ticker price."""
    mock_ccxt.return_value.fetch_ticker.return_value = {
        'last': 50000.0
    }
    
    price = await binance_exchange.get_ticker_price("BTC/USDT")
    assert price == Decimal('50000.0')
    mock_ccxt.return_value.fetch_ticker.assert_called_once_with("BTC/USDT")

@pytest.mark.asyncio
async def test_get_balance(binance_exchange, mock_ccxt):
    """Test getting balance."""
    mock_ccxt.return_value.fetch_balance.return_value = {
        'BTC': {
            'free': 1.0,
            'used': 0.5,
            'total': 1.5
        }
    }
    
    balance = await binance_exchange.get_balance('BTC')
    assert balance == Decimal('1.0')  # Should return free balance
    mock_ccxt.return_value.fetch_balance.assert_called_once()

@pytest.mark.asyncio
async def test_create_order(binance_exchange, mock_ccxt):
    """Test creating an order."""
    mock_ccxt.return_value.create_order.return_value = {
        'id': '123',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 1.0,
        'price': 50000.0,
        'status': 'open',
        'timestamp': 1616169600000,
        'lastTradeTimestamp': 1616169600000,
        'filled': 0.0,
        'average': None
    }
    
    order = await binance_exchange.create_order(
        symbol='BTC/USDT',
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        amount=Decimal('1.0'),
        price=Decimal('50000.0')
    )
    assert isinstance(order, OrderInfo)
    assert order.order_id == '123'
    assert order.symbol == 'BTC/USDT'
    assert order.order_type == OrderType.LIMIT
    assert order.side == OrderSide.BUY
    assert order.amount == Decimal('1.0')
    assert order.price == Decimal('50000.0')
    assert order.status == OrderStatus.OPEN
    mock_ccxt.return_value.create_order.assert_called_once_with(
        symbol='BTC/USDT',
        type='limit',
        side='buy',
        amount=1.0,
        price=50000.0
    )

@pytest.mark.asyncio
async def test_get_order_status(binance_exchange, mock_ccxt):
    """Test getting order status."""
    mock_ccxt.return_value.fetch_order.return_value = {
        'id': '123',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 1.0,
        'price': 50000.0,
        'status': 'open',
        'timestamp': 1616169600000,
        'lastTradeTimestamp': 1616169600000,
        'filled': 0.0,
        'average': None
    }
    
    order = await binance_exchange.get_order_status('123', 'BTC/USDT')
    assert isinstance(order, OrderInfo)
    assert order.order_id == '123'
    assert order.symbol == 'BTC/USDT'
    assert order.order_type == OrderType.LIMIT
    assert order.side == OrderSide.BUY
    assert order.status == OrderStatus.OPEN
    mock_ccxt.return_value.fetch_order.assert_called_once_with('123', 'BTC/USDT')

@pytest.mark.asyncio
async def test_cancel_order(binance_exchange, mock_ccxt):
    """Test canceling an order."""
    mock_ccxt.return_value.cancel_order.return_value = {
        'id': '123',
        'symbol': 'BTC/USDT',
        'status': 'CANCELED'
    }
    
    result = await binance_exchange.cancel_order('123', 'BTC/USDT')
    assert result is True
    mock_ccxt.return_value.cancel_order.assert_called_once_with('123', 'BTC/USDT')

@pytest.mark.asyncio
async def test_get_order_book(binance_exchange, mock_ccxt):
    """Test getting order book."""
    mock_ccxt.return_value.fetch_order_book.return_value = {
        'bids': [[50000.0, 1.0, 1616169600000], [49900.0, 2.0, 1616169600000]],
        'asks': [[50100.0, 1.5, 1616169600000], [50200.0, 2.5, 1616169600000]]
    }
    
    bids, asks = await binance_exchange.get_order_book('BTC/USDT')
    assert len(bids) == 2
    assert len(asks) == 2
    
    # Check first bid
    first_bid = bids[0]  # type: ignore
    assert first_bid.price == Decimal('50000.0')
    assert first_bid.quantity == Decimal('1.0')
    
    # Check first ask
    first_ask = asks[0]  # type: ignore
    assert first_ask.price == Decimal('50100.0')
    assert first_ask.quantity == Decimal('1.5')
    
    mock_ccxt.return_value.fetch_order_book.assert_called_once_with('BTC/USDT', 20)

@pytest.mark.asyncio
async def test_get_trading_fees(binance_exchange, mock_ccxt):
    """Test getting trading fees."""
    mock_ccxt.return_value.fetch_trading_fee.return_value = {
        'maker': '0.001',
        'taker': '0.001'
    }
    
    fees = await binance_exchange.get_trading_fees('BTC/USDT')
    assert isinstance(fees, dict)
    assert fees['maker'] == Decimal('0.001')
    assert fees['taker'] == Decimal('0.001')
    mock_ccxt.return_value.fetch_trading_fee.assert_called_once_with('BTC/USDT')

@pytest.mark.asyncio
async def test_get_recent_trades(binance_exchange, mock_ccxt):
    """Test getting recent trades."""
    mock_ccxt.return_value.fetch_trades.return_value = [
        {
            'id': '123',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 1.0,
            'price': 50000.0,
            'timestamp': 1616169600000,
            'fee': {'cost': 0.1, 'currency': 'USDT'}
        }
    ]
    
    trades = await binance_exchange.get_recent_trades('BTC/USDT')
    assert isinstance(trades, list)
    assert len(trades) == 1
    trade = trades[0]
    assert isinstance(trade, TradeInfo)
    assert trade.trade_id == '123'
    assert trade.symbol == 'BTC/USDT'
    assert trade.side == OrderSide.BUY
    assert trade.amount == Decimal('1.0')
    assert trade.price == Decimal('50000.0')
    assert trade.fee == Decimal('0.1')
    assert trade.fee_currency == 'USDT'
    mock_ccxt.return_value.fetch_trades.assert_called_once_with('BTC/USDT', limit=100)
