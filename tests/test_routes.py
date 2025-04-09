"""Unit tests for API routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime
from ..routes import router, get_exchange
from ..exchange_interface import (
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo,
    TradeInfo
)
from .mock_exchange import MockExchange

# Create mock exchange instance
mock_exchange = MockExchange()

# Create test app with router
app = FastAPI()
app.include_router(router)

# Replace the real exchange with a mock for testing
app.dependency_overrides[get_exchange] = lambda: mock_exchange

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Fixture providing authentication headers."""
    return {"Authorization": "Bearer test_token"}

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_markets():
    """Test getting available markets."""
    response = client.get("/api/markets")
    assert response.status_code == 200
    data = response.json()
    assert "markets" in data
    assert isinstance(data["markets"], list)
    assert len(data["markets"]) == 2
    assert data["markets"][0]["symbol"] == "BTC/USDT"
    assert data["markets"][1]["symbol"] == "ETH/USDT"

def test_get_order_book():
    """Test getting order book for a symbol."""
    symbol = "BTC/USDT"
    response = client.get("/api/orderbook", params={"symbol": symbol})
    assert response.status_code == 200
    data = response.json()
    assert "bids" in data
    assert "asks" in data
    assert isinstance(data["bids"], list)
    assert isinstance(data["asks"], list)
    assert len(data["bids"]) == 2
    assert len(data["asks"]) == 2

def test_create_order(auth_headers):
    """Test creating a new order."""
    order_data = {
        "symbol": "BTC/USDT",
        "order_type": "limit",
        "side": "buy",
        "quantity": 1.0,
        "price": 50000.0
    }
    response = client.post("/api/orders", json=order_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["symbol"] == order_data["symbol"]
    assert data["status"] == "open"

def test_get_order(auth_headers):
    """Test getting order details."""
    # First create an order
    order_data = {
        "symbol": "BTC/USDT",
        "order_type": "limit",
        "side": "buy",
        "quantity": 1.0,
        "price": 50000.0
    }
    create_response = client.post("/api/orders", json=order_data, headers=auth_headers)
    assert create_response.status_code == 200
    order_id = create_response.json()["order_id"]
    
    # Then get its details
    response = client.get(f"/api/orders/{order_id}", params={"symbol": "BTC/USDT"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id
    assert "status" in data
    assert "symbol" in data
    assert "side" in data
    assert "quantity" in data

def test_cancel_order(auth_headers):
    """Test canceling an order."""
    # First create an order
    order_data = {
        "symbol": "BTC/USDT",
        "order_type": "limit",
        "side": "buy",
        "quantity": 1.0,
        "price": 50000.0
    }
    create_response = client.post("/api/orders", json=order_data, headers=auth_headers)
    assert create_response.status_code == 200
    order_id = create_response.json()["order_id"]
    
    # Then cancel it
    response = client.delete(f"/api/orders/{order_id}", params={"symbol": "BTC/USDT"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id
    assert data["status"] == "CANCELED"

def test_get_trades(auth_headers):
    """Test getting trade history."""
    symbol = "BTC/USDT"
    response = client.get("/api/trades", params={"symbol": symbol}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "trades" in data
    assert isinstance(data["trades"], list)
    assert len(data["trades"]) == 2
    assert data["trades"][0]["symbol"] == symbol
    assert data["trades"][1]["symbol"] == symbol

def test_get_market_data():
    """Test getting market data for a symbol."""
    symbol = "BTC/USDT"
    response = client.get("/api/market", params={"symbol": symbol})
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == symbol
    assert "bid" in data
    assert "ask" in data
    assert "last_price" in data
    assert "volume_24h" in data
    assert "timestamp" in data

def test_get_economic_indicator():
    """Test getting economic indicator data."""
    indicator_id = "GDP"
    response = client.get(f"/api/economic/{indicator_id}")
    assert response.status_code in [200, 400]  # 400 for API errors
    if response.status_code == 200:
        data = response.json()
        assert data["indicator_id"] == indicator_id
        assert "value" in data
        assert "date" in data
        assert "frequency" in data

def test_get_economic_indicator_with_dates():
    """Test getting economic indicator data with date range."""
    indicator_id = "GDP"
    params = {
        "start_date": "2023-01-01T00:00:00",
        "end_date": "2023-12-31T23:59:59"
    }
    response = client.get(f"/api/economic/{indicator_id}", params=params)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert data["indicator_id"] == indicator_id
        assert "value" in data
        assert "date" in data
        assert "frequency" in data

def test_invalid_order_data(auth_headers):
    """Test creating order with invalid data."""
    invalid_order = {
        "symbol": "BTC/USDT",
        "order_type": "INVALID_TYPE",
        "side": "BUY",
        "quantity": -1.0,  # Invalid quantity
        "price": 50000.0
    }
    response = client.post("/api/orders", json=invalid_order, headers=auth_headers)
    assert response.status_code == 422  # FastAPI validation error
    assert "detail" in response.json()

def test_unauthorized_access():
    """Test accessing protected endpoints without authentication."""
    response = client.get("/api/orders/123", params={"symbol": "BTC/USDT"})
    assert response.status_code == 401

def test_invalid_market_symbol():
    """Test using invalid trading pair symbol."""
    symbol = "INVALID/PAIR"
    response = client.get("/api/market", params={"symbol": symbol})
    assert response.status_code == 400
    assert "detail" in response.json()

def test_invalid_economic_indicator():
    """Test using invalid economic indicator ID."""
    indicator_id = "INVALID_INDICATOR"
    response = client.get(f"/api/economic/{indicator_id}")
    assert response.status_code == 400
    assert "detail" in response.json()
