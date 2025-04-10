"""
Abstract base class defining the interface for cryptocurrency exchange interactions.
Provides a standardized way to interact with different cryptocurrency exchanges.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Literal
from decimal import Decimal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class OrderType(str, Enum):
    """Types of orders supported by exchanges."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(str, Enum):
    """Order sides (buy/sell)."""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    """Possible order statuses."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"

class OrderBookEntry(BaseModel):
    """Structure for order book entries."""
    price: Decimal = Field(..., description="Price of the order")
    amount: Decimal = Field(..., description="Amount of the order")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the order")

class OrderInfo(BaseModel):
    """Structure for order information."""
    order_id: str = Field(..., description="Unique identifier of the order")
    symbol: str = Field(..., description="Trading pair symbol")
    order_type: OrderType = Field(..., description="Type of order")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    amount: Decimal = Field(..., description="Order amount in base currency")
    price: Optional[Decimal] = Field(None, description="Order price (for limit orders)")
    status: OrderStatus = Field(..., description="Current order status")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    filled_amount: Decimal = Field(Decimal('0'), description="Amount filled so far")
    average_price: Optional[Decimal] = Field(None, description="Average fill price")

class TradeInfo(BaseModel):
    """Structure for trade information."""
    trade_id: str = Field(..., description="Unique identifier of the trade")
    order_id: str = Field(..., description="Associated order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: OrderSide = Field(..., description="Trade side (buy/sell)")
    amount: Decimal = Field(..., description="Trade amount")
    price: Decimal = Field(..., description="Trade price")
    timestamp: datetime = Field(..., description="Trade timestamp")
    fee: Decimal = Field(..., description="Trading fee")
    fee_currency: str = Field(..., description="Currency of the fee")

class ExchangeInterface(ABC):
    """Abstract base class defining the interface for cryptocurrency exchange interactions."""
    
    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Get the current price for a trading pair."""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str) -> Decimal:
        """Get the balance of a specific asset."""
        pass
    
    @abstractmethod
    async def create_order(self, 
                    symbol: str, 
                    order_type: OrderType, 
                    side: OrderSide, 
                    amount: Decimal,
                    price: Optional[Decimal] = None) -> OrderInfo:
        """Create a new order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> OrderInfo:
        """Get the status of an order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 20) -> Tuple[List[OrderBookEntry], List[OrderBookEntry]]:
        """Get the current order book for a trading pair."""
        pass

    @abstractmethod
    async def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """Get the trading fees for a specific trading pair."""
        pass

    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeInfo]:
        """Get recent trades for a trading pair."""
        pass

    @abstractmethod
    async def subscribe_to_ticker(self, symbol: str, callback) -> None:
        """Subscribe to real-time ticker updates."""
        pass

    @abstractmethod
    async def subscribe_to_trades(self, symbol: str, callback) -> None:
        """Subscribe to real-time trade updates."""
        pass

    @abstractmethod
    async def subscribe_to_order_book(self, symbol: str, callback) -> None:
        """Subscribe to real-time order book updates."""
        pass 