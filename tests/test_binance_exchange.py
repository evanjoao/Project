"""
Tests for the Binance exchange implementation.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any, Tuple, AsyncGenerator
from unittest.mock import AsyncMock, patch, MagicMock
from ..binance_exchange import BinanceExchange
from ..exchange_interface import OrderType, OrderSide, OrderStatus
from ..rate_limiter import RateLimiter, RateLimitConfig

@pytest_asyncio.fixture
async def exchange() -> AsyncGenerator[BinanceExchange, None]:
    """Create a test exchange instance."""
    with patch('ccxt.async_support.binance') as mock_binance:
        # Create a mock exchange instance
        mock_exchange = AsyncMock()
        mock_exchange.close = AsyncMock()
        mock_exchange.set_sandbox_mode = MagicMock()  # Regular mock, not async
        mock_binance.return_value = mock_exchange

        # Create exchange instance with rate limiter
        exchange = BinanceExchange('test_key', 'test_secret', testnet=True)
        
        # Configure rate limiter
        rate_limiter = RateLimiter()
        config = RateLimitConfig(
            requests_per_second=10.0,  # Higher rate for tests
            burst_size=20,
            name="binance"
        )
        rate_limiter.add_limiter("binance", config)
        exchange.rate_limiter = rate_limiter

        # Set sandbox mode (not async)
        exchange.exchange.set_sandbox_mode(True)

        yield exchange
        await exchange.close()

@pytest.mark.asyncio
async def test_get_ticker_price(exchange):
    """Test getting ticker price."""
    mock_ticker = {'last': '50000.00'}
    exchange.exchange.fetch_ticker = AsyncMock(return_value=mock_ticker)
    
    price = await exchange.get_ticker_price('BTC/USDT')
    assert price == Decimal('50000.00')
    exchange.exchange.fetch_ticker.assert_called_once_with('BTC/USDT')

@pytest.mark.asyncio
async def test_get_balance(exchange):
    """Test getting balance."""
    mock_balance = {
        'BTC': {'free': '1.5', 'used': '0.5'},
        'USDT': {'free': '1000.0', 'used': '0.0'}
    }
    exchange.exchange.fetch_balance = AsyncMock(return_value=mock_balance)
    
    btc_balance = await exchange.get_balance('BTC')
    assert btc_balance == Decimal('1.5')
    
    usdt_balance = await exchange.get_balance('USDT')
    assert usdt_balance == Decimal('1000.0')

@pytest.mark.asyncio
async def test_create_order(exchange):
    """Test creating an order."""
    mock_order = {
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 1.0,
        'price': 50000.0,
        'status': 'open',
        'timestamp': 1609459200000,
        'lastTradeTimestamp': 1609459200000,
        'filled': 0.0,
        'average': None
    }
    exchange.exchange.create_order = AsyncMock(return_value=mock_order)
    
    order = await exchange.create_order(
        symbol='BTC/USDT',
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        amount=Decimal('1.0'),
        price=Decimal('50000.0')
    )
    
    assert order.order_id == '12345'
    assert order.symbol == 'BTC/USDT'
    assert order.order_type == OrderType.LIMIT
    assert order.side == OrderSide.BUY
    assert order.amount == Decimal('1.0')
    assert order.price == Decimal('50000.0')
    assert order.status == OrderStatus.OPEN

@pytest.mark.asyncio
async def test_get_order_status(exchange):
    """Test getting order status."""
    mock_order = {
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 1.0,
        'price': 50000.0,
        'status': 'closed',
        'timestamp': 1609459200000,
        'lastTradeTimestamp': 1609459200000,
        'filled': 1.0,
        'average': 50000.0
    }
    exchange.exchange.fetch_order = AsyncMock(return_value=mock_order)
    
    order = await exchange.get_order_status('12345', 'BTC/USDT')
    assert order.order_id == '12345'
    assert order.status == OrderStatus.CLOSED
    assert order.filled_amount == Decimal('1.0')
    assert order.average_price == Decimal('50000.0')

@pytest.mark.asyncio
async def test_cancel_order(exchange):
    """Test canceling an order."""
    mock_response = {
        'id': '12345',
        'symbol': 'BTC/USDT',
        'status': 'CANCELED'  # Status must be 'CANCELED' for the method to return True
    }
    exchange.exchange.cancel_order = AsyncMock(return_value=mock_response)
    
    result = await exchange.cancel_order('12345', 'BTC/USDT')
    assert result is True
    exchange.exchange.cancel_order.assert_called_once_with('12345', 'BTC/USDT')

@pytest.mark.asyncio
async def test_get_order_book(exchange: BinanceExchange):
    """Test getting order book."""
    mock_order_book = {
        'bids': [
            [50000.0, 1.0, 1609459200000],
            [49900.0, 2.0, 1609459200000]
        ],
        'asks': [
            [50100.0, 1.5, 1609459200000],
            [50200.0, 2.5, 1609459200000]
        ]
    }
    exchange.exchange.fetch_order_book = AsyncMock(return_value=mock_order_book)
    
    bids, asks = await exchange.get_order_book('BTC/USDT', limit=2)
    assert len(bids) == 2
    assert len(asks) == 2
    assert bids[0].price == Decimal('50000.0')
    assert bids[0].quantity == Decimal('1.0')
    assert asks[0].price == Decimal('50100.0')
    assert asks[0].quantity == Decimal('1.5')

@pytest.mark.asyncio
async def test_get_trading_fees(exchange: BinanceExchange):
    """Test getting trading fees."""
    mock_fees = {
        'maker': 0.001,
        'taker': 0.002
    }
    exchange.exchange.fetch_trading_fee = AsyncMock(return_value=mock_fees)
    
    fees = await exchange.get_trading_fees('BTC/USDT')
    assert fees['maker'] == Decimal('0.001')
    assert fees['taker'] == Decimal('0.002')

@pytest.mark.asyncio
async def test_get_recent_trades(exchange: BinanceExchange):
    """Test getting recent trades."""
    mock_trades = [
        {
            'id': '12345',
            'order': '67890',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 1.0,
            'price': 50000.0,
            'timestamp': 1609459200000,
            'fee': {'cost': 0.1, 'currency': 'USDT'}
        }
    ]
    exchange.exchange.fetch_trades = AsyncMock(return_value=mock_trades)
    
    trades = await exchange.get_recent_trades('BTC/USDT', limit=1)
    assert len(trades) == 1
    assert trades[0].trade_id == '12345'
    assert trades[0].order_id == '67890'
    assert trades[0].side == OrderSide.BUY
    assert trades[0].amount == Decimal('1.0')
    assert trades[0].price == Decimal('50000.0')
    assert trades[0].fee == Decimal('0.1')
    assert trades[0].fee_currency == 'USDT' 