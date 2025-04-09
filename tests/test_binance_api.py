"""
Tests for the Binance API implementation.
"""

import pytest
import time
from decimal import Decimal
from typing import Dict, Any, Generator, cast, List
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from ..binance_api import BinanceAPI, KlineInfo
from ..exchange_interface import OrderBookEntry
from ..exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    InvalidRequestError
)

@pytest.fixture
def mock_response() -> MagicMock:
    """Fixture providing a mock response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"success": True}
    return mock

@pytest.fixture
def mock_session(mock_response: MagicMock) -> Generator[MagicMock, None, None]:
    """Fixture providing a mock session."""
    with patch('requests.Session') as mock:
        session = MagicMock()
        session.request.return_value = mock_response
        mock.return_value = session
        yield session

@pytest.fixture
def api(mock_session: MagicMock) -> Generator[BinanceAPI, None, None]:
    """Fixture providing a BinanceAPI instance."""
    with patch.object(BinanceAPI, 'subscribe_to_order_book', new_callable=AsyncMock) as mock:
        mock.return_value = None
        api = BinanceAPI(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        yield api

def test_init_with_credentials():
    """Test initialization with credentials."""
    with patch.object(BinanceAPI, 'subscribe_to_order_book', new_callable=AsyncMock) as mock:
        mock.return_value = None
        api = BinanceAPI(api_key="test_key", api_secret="test_secret")
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.testnet is False

def test_init_with_testnet():
    """Test initialization with testnet."""
    with patch.object(BinanceAPI, 'subscribe_to_order_book', new_callable=AsyncMock) as mock:
        mock.return_value = None
        api = BinanceAPI(testnet=True)
        assert "testnet.binance.vision" in api.base_url
        assert "testnet.binancefuture.com" in api.futures_url
        assert "testnet.binance.vision" in api.ws_url

def test_generate_signature(api):
    """Test signature generation."""
    params = {"timestamp": 1234567890, "symbol": "BTCUSDT"}
    signature = api._generate_signature(params)
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 produces 64 character hex string

def test_request_success(api, mock_session):
    """Test successful API request."""
    response = api._request("GET", "/test", {"param": "value"})
    assert response == {"success": True}
    mock_session.request.assert_called_once()

def test_request_authentication_error(api, mock_session):
    """Test API request with authentication error."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"code": -2015, "msg": "Invalid API key"}
    mock_session.request.return_value = mock_response
    
    with pytest.raises(AuthenticationError):
        api._request("GET", "/test")

def test_request_rate_limit_error(api, mock_session):
    """Test API request with rate limit error."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"code": -1021, "msg": "Rate limit exceeded"}
    mock_session.request.return_value = mock_response
    
    with pytest.raises(RateLimitError):
        api._request("GET", "/test")

def test_request_invalid_request_error(api, mock_session):
    """Test API request with invalid request error."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"code": -1121, "msg": "Invalid symbol"}
    mock_session.request.return_value = mock_response
    
    with pytest.raises(InvalidRequestError):
        api._request("GET", "/test")

def test_get_exchange_info(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test getting exchange information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "timezone": "UTC",
        "serverTime": 1234567890,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT"
            }
        ]
    }
    mock_session.request.return_value = mock_response
    
    info = api.get_exchange_info()
    assert "timezone" in info
    assert "symbols" in info
    assert len(cast(Dict[str, Any], info)["symbols"]) > 0

def test_get_symbol_price(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test getting symbol price."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "BTCUSDT",
        "price": "50000.00"
    }
    mock_session.request.return_value = mock_response
    
    price_info = api.get_symbol_price("BTCUSDT")
    assert cast(Dict[str, str], price_info)["symbol"] == "BTCUSDT"
    assert "price" in price_info

@pytest.mark.asyncio
async def test_get_klines(api: BinanceAPI) -> None:
    """Test getting kline data."""
    klines = await api.get_klines("BTCUSDT", "1m", limit=1)
    assert len(klines) == 1
    assert isinstance(klines[0], dict)
    assert cast(Dict[str, str], klines[0])["symbol"] == "BTCUSDT"

def test_create_order(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test creating an order."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "BTCUSDT",
        "orderId": 12345,
        "clientOrderId": "test_order",
        "transactTime": 1499827319559,
        "price": "0.00000000",
        "origQty": "0.00100000",
        "executedQty": "0.00000000",
        "status": "NEW",
        "timeInForce": "GTC",
        "type": "MARKET",
        "side": "BUY"
    }
    mock_session.request.return_value = mock_response
    
    order = api.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.001
    )
    assert cast(Dict[str, Any], order)["symbol"] == "BTCUSDT"
    assert cast(Dict[str, Any], order)["orderId"] == 12345
    assert cast(Dict[str, Any], order)["status"] == "NEW"

def test_cancel_order():
    """Test canceling an order."""
    mock_response = {
        'orderId': '12345',
        'symbol': 'BTC/USDT',
        'status': 'CANCELED'
    }
    with patch('src.api.binance_api.BinanceAPI._request') as mock_request:
        mock_request.return_value = mock_response
        api = BinanceAPI('test_key', 'test_secret')
        result = api.cancel_order('12345', 'BTC/USDT')
        assert result == mock_response

def test_get_order(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test getting order information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "BTCUSDT",
        "orderId": 12345,
        "clientOrderId": "test_order",
        "price": "0.00100000",
        "origQty": "100.00000000",
        "executedQty": "0.00000000",
        "status": "NEW",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "side": "BUY"
    }
    mock_session.request.return_value = mock_response
    
    order = api.get_order("BTCUSDT", order_id=12345)
    assert cast(Dict[str, Any], order)["symbol"] == "BTCUSDT"
    assert cast(Dict[str, Any], order)["orderId"] == 12345
    assert cast(Dict[str, Any], order)["status"] == "NEW"

def test_get_open_orders(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test getting open orders."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "clientOrderId": "test_order",
            "price": "0.00100000",
            "origQty": "100.00000000",
            "executedQty": "0.00000000",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY"
        }
    ]
    mock_session.request.return_value = mock_response
    
    orders = api.get_open_orders("BTCUSDT")
    assert len(orders) == 1
    assert cast(Dict[str, Any], orders[0])["symbol"] == "BTCUSDT"
    assert cast(Dict[str, Any], orders[0])["status"] == "NEW"

def test_get_balance(api: BinanceAPI, mock_session: MagicMock) -> None:
    """Test getting account balance."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "balances": [
            {
                "asset": "BTC",
                "free": "0.00100000",
                "locked": "0.00000000"
            },
            {
                "asset": "USDT",
                "free": "100.00000000",
                "locked": "0.00000000"
            }
        ]
    }
    mock_session.request.return_value = mock_response
    
    balances = api.get_balance()
    assert len(balances) == 2
    assert cast(List[Dict[str, Any]], balances)[0]["asset"] == "BTC"
    assert cast(List[Dict[str, Any]], balances)[1]["asset"] == "USDT"

def test_get_ticker_price_decimal(api, mock_session):
    """Test getting ticker price as Decimal."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "BTCUSDT",
        "price": "50000.00"
    }
    mock_session.request.return_value = mock_response
    
    price = api.get_ticker_price("BTCUSDT")
    assert isinstance(price, Decimal)
    assert price == Decimal("50000.00")

@pytest.mark.asyncio
async def test_get_order_book(api):
    """Test getting order book."""
    bids, asks = await api.get_order_book("BTCUSDT")
    assert isinstance(bids, list)
    assert isinstance(asks, list)
    assert len(bids) > 0
    assert len(asks) > 0
    assert isinstance(bids[0], OrderBookEntry)
    assert isinstance(asks[0], OrderBookEntry) 