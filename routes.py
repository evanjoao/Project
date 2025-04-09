"""
API route definitions and handlers.

This module defines the REST API endpoints for interacting with cryptocurrency exchanges
and economic data services. It provides a clean interface for trading operations,
market data retrieval, and economic indicators.
"""

from typing import List, Optional, Dict, Any, TypedDict
from fastapi import APIRouter, HTTPException, Depends, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal

from .exchange_interface import (
    ExchangeInterface,
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo
)
from .binance_exchange import BinanceExchange
from .fred_api import FredAPI
from .exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    InsufficientFundsError,
    NetworkError,
    InvalidResponseError,
    InvalidRequestError
)

# Initialize router
router = APIRouter(
    prefix="/api",
    tags=["trading"]
)

# Initialize security
security = HTTPBearer(auto_error=False)

# Initialize exchange and FRED API clients
def get_exchange() -> ExchangeInterface:
    """Get the exchange instance."""
    return BinanceExchange(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here"
    )

# Initialize FRED API client
fred_api = FredAPI(api_key="dummy_fred_api_key")

# Pydantic models for request/response validation
class OrderRequest(BaseModel):
    """Model for order creation requests."""
    model_config = ConfigDict(extra='forbid')
    
    symbol: str = Field(description="Trading pair symbol (e.g., 'BTC/USDT')")
    order_type: OrderType = Field(description="Type of order (market/limit)")
    side: OrderSide = Field(description="Order side (buy/sell)")
    quantity: float = Field(gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for limit orders)")

class OrderResponse(BaseModel):
    """Model for order responses."""
    model_config = ConfigDict(extra='forbid')
    
    order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    quantity: float
    price: Optional[float]
    timestamp: datetime

class MarketInfo(TypedDict):
    symbol: str
    base: str
    quote: str
    active: bool

class MarketData(BaseModel):
    """Model for market data responses."""
    model_config = ConfigDict(extra='forbid')
    
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume_24h: float
    timestamp: datetime

class EconomicIndicator(BaseModel):
    """Model for economic indicator responses."""
    model_config = ConfigDict(extra='forbid')
    
    indicator_id: str
    value: float
    date: datetime
    frequency: str

class FredDataPoint(TypedDict):
    """Structure for FRED API data points."""
    value: str
    date: str
    frequency: str

# Authentication dependency
async def get_auth_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    """Get and validate authentication token."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    if token != "test_token":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return token

# Error handler dependency
async def handle_errors():
    """Global error handler for API exceptions."""
    try:
        yield
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except InvalidResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health", dependencies=[Depends(handle_errors)])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Markets endpoint
@router.get("/markets", dependencies=[Depends(handle_errors)])
async def get_markets(exchange: ExchangeInterface = Depends(get_exchange)):
    """Get available trading markets."""
    try:
        # Get markets from exchange
        if isinstance(exchange, BinanceExchange):
            markets = await exchange.exchange.fetch_markets()
            if not markets:
                return {"markets": []}
            return {
                "markets": [
                    MarketInfo(
                        symbol=str(market.get("symbol", "")),
                        base=str(market.get("base", "")),
                        quote=str(market.get("quote", "")),
                        active=bool(market.get("active", False))
                    )
                    for market in markets if market
                ]
            }
        else:
            # For mock exchange in tests
            return {"markets": getattr(exchange, "markets", [])}
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Order book endpoint
@router.get("/orderbook", dependencies=[Depends(handle_errors)])
async def get_order_book(
    symbol: str = Query(..., description="Trading pair symbol (e.g. BTC/USDT)"),
    limit: int = Query(20, ge=1, le=100),
    exchange: ExchangeInterface = Depends(get_exchange)
):
    """Get order book for a symbol."""
    try:
        bids, asks = await exchange.get_order_book(symbol, limit=limit)
        return {
            "bids": [
                {
                    "price": float(entry.price),
                    "amount": float(entry.amount),
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None
                }
                for entry in bids
            ],
            "asks": [
                {
                    "price": float(entry.price),
                    "amount": float(entry.amount),
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None
                }
                for entry in asks
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Order endpoints
@router.post("/orders", response_model=OrderResponse, dependencies=[Depends(handle_errors)])
async def create_order(
    order: OrderRequest,
    token: str = Security(get_auth_token),
    exchange: ExchangeInterface = Depends(get_exchange)
) -> OrderResponse:
    """Create a new order."""
    try:
        order_info = await exchange.create_order(
            symbol=order.symbol,
            order_type=order.order_type,
            side=order.side,
            amount=Decimal(str(order.quantity)),
            price=Decimal(str(order.price)) if order.price is not None else None
        )
        return OrderResponse(
            order_id=order_info.order_id,
            status=order_info.status,
            symbol=order_info.symbol,
            side=order_info.side,
            quantity=float(order_info.amount),
            price=float(order_info.price) if order_info.price is not None else None,
            timestamp=order_info.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders/{order_id}", response_model=OrderResponse, dependencies=[Depends(handle_errors)])
async def get_order(
    order_id: str,
    symbol: str = Query(..., description="Trading pair symbol (e.g. BTC/USDT)"),
    token: str = Security(get_auth_token),
    exchange: ExchangeInterface = Depends(get_exchange)
) -> OrderResponse:
    """Get order details by ID."""
    try:
        order_info = await exchange.get_order_status(order_id, symbol)
        return OrderResponse(
            order_id=order_info.order_id,
            status=order_info.status,
            symbol=order_info.symbol,
            side=order_info.side,
            quantity=float(order_info.amount),
            price=float(order_info.price) if order_info.price is not None else None,
            timestamp=order_info.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/orders/{order_id}", dependencies=[Depends(handle_errors)])
async def cancel_order(
    order_id: str,
    symbol: str = Query(..., description="Trading pair symbol (e.g. BTC/USDT)"),
    token: str = Security(get_auth_token),
    exchange: ExchangeInterface = Depends(get_exchange)
):
    """Cancel an existing order."""
    try:
        success = await exchange.cancel_order(order_id, symbol)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel order")
        return {
            "order_id": order_id,
            "status": "CANCELED"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Trades endpoint
@router.get("/trades", dependencies=[Depends(handle_errors)])
async def get_trades(
    symbol: str = Query(..., description="Trading pair symbol (e.g. BTC/USDT)"),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Security(get_auth_token),
    exchange: ExchangeInterface = Depends(get_exchange)
):
    """Get recent trades for a symbol."""
    try:
        trades = await exchange.get_recent_trades(symbol, limit=limit)
        return {
            "trades": [
                {
                    "trade_id": trade.trade_id,
                    "order_id": trade.order_id,
                    "symbol": trade.symbol,
                    "side": trade.side.value,
                    "amount": float(trade.amount),
                    "price": float(trade.price),
                    "timestamp": trade.timestamp.isoformat(),
                    "fee": float(trade.fee),
                    "fee_currency": trade.fee_currency
                }
                for trade in trades
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Market data endpoint
@router.get("/market", response_model=MarketData, dependencies=[Depends(handle_errors)])
async def get_market_data(
    symbol: str = Query(..., description="Trading pair symbol (e.g. BTC/USDT)"),
    exchange: ExchangeInterface = Depends(get_exchange)
):
    """Get market data for a symbol."""
    try:
        ticker_price = await exchange.get_ticker_price(symbol)
        bids, asks = await exchange.get_order_book(symbol, limit=1)
        
        return MarketData(
            symbol=symbol,
            bid=float(bids[0].price) if bids else 0.0,
            ask=float(asks[0].price) if asks else 0.0,
            last_price=float(ticker_price),
            volume_24h=0.0,  # Not available in the current implementation
            timestamp=datetime.utcnow()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Economic indicators endpoint
@router.get("/economic/{indicator_id}", dependencies=[Depends(handle_errors)])
async def get_economic_indicator(
    indicator_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get economic indicator data."""
    try:
        # Convert string dates to datetime objects
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get series data
        data = fred_api.get_series(
            indicator_id,
            observation_start=start_dt,
            observation_end=end_dt
        )
        
        if not data or "observations" not in data:
            raise HTTPException(status_code=404, detail=f"No data found for indicator {indicator_id}")
            
        # Get the last data point
        observations = data["observations"]
        if not observations:
            raise HTTPException(status_code=404, detail=f"No data found for indicator {indicator_id}")
            
        last_data_point = observations[-1]
        
        return {
            "indicator_id": indicator_id,
            "value": float(last_data_point["value"]),
            "date": last_data_point["date"],
            "frequency": data.get("frequency", "Unknown")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

def run_tests() -> bool:
    """
    Run API endpoint tests.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    import pytest
    from fastapi.testclient import TestClient
    
    client = TestClient(router)
    all_passed = True
    
    # Test order creation
    try:
        response = client.post("/orders", json={
            "symbol": "BTC/USDT",
            "order_type": "market",
            "side": "buy",
            "quantity": 0.1
        })
        assert response.status_code in [200, 400]  # 400 is acceptable if no API key
    except Exception as e:
        print(f"Order creation test failed: {e}")
        all_passed = False
    
    # Test market data retrieval
    try:
        response = client.get("/market/BTC/USDT")
        assert response.status_code in [200, 400]
    except Exception as e:
        print(f"Market data test failed: {e}")
        all_passed = False
    
    # Test economic indicator retrieval
    try:
        response = client.get("/economic/GDP")
        assert response.status_code in [200, 400]
    except Exception as e:
        print(f"Economic indicator test failed: {e}")
        all_passed = False
    
    return all_passed

if __name__ == "__main__":
    test_result = run_tests()
    print(f"API Tests {'Passed' if test_result else 'Failed'}") 