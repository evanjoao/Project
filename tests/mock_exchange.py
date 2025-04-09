"""Mock exchange for testing."""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Tuple, TypedDict, Callable, Any
from ..exchange_interface import (
    ExchangeInterface,
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo,
    TradeInfo
)

class MarketInfo(TypedDict):
    symbol: str
    base: str
    quote: str
    active: bool

class MockExchange(ExchangeInterface):
    """Mock exchange implementation for testing."""
    
    def __init__(self):
        """Initialize mock exchange."""
        self.markets: List[MarketInfo] = [
            {
                "symbol": "BTC/USDT",
                "base": "BTC",
                "quote": "USDT",
                "active": True
            },
            {
                "symbol": "ETH/USDT",
                "base": "ETH",
                "quote": "USDT",
                "active": True
            }
        ]
        self.orders: Dict[str, OrderInfo] = {}
        self.trades = []
        self.next_order_id = 1
        self.next_trade_id = 1
        self.exchange = self  # Make it compatible with CCXT style access
        self.balances: Dict[str, Decimal] = {
            "BTC": Decimal("1.0"),
            "USDT": Decimal("50000.0")
        }
        
    async def fetch_markets(self):
        """Fetch markets in CCXT format."""
        return [
            {
                "symbol": market["symbol"],
                "base": market["base"],
                "quote": market["quote"],
                "active": market["active"]
            }
            for market in self.markets
        ]
        
    def _get_market_info(self, symbol: str) -> MarketInfo:
        """Get market information for a symbol."""
        for market in self.markets:
            if market["symbol"] == symbol:
                return market
        raise ValueError(f"Invalid symbol: {symbol}")
        
    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Get the current price for a trading pair."""
        self._get_market_info(symbol)  # Validate symbol exists
        return Decimal("50000.0")
        
    async def get_balance(self, asset: str) -> Decimal:
        """Get the balance of a specific asset."""
        return self.balances.get(asset, Decimal("0"))
        
    async def create_order(self, 
                    symbol: str, 
                    order_type: OrderType, 
                    side: OrderSide, 
                    amount: Decimal,
                    price: Optional[Decimal] = None) -> OrderInfo:
        """Create a new order."""
        self._get_market_info(symbol)  # Validate symbol exists
        order_id = str(self.next_order_id)
        self.next_order_id += 1
        order = OrderInfo(
            order_id=order_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            status=OrderStatus.OPEN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            filled_amount=Decimal("0"),
            average_price=None
        )
        self.orders[order_id] = order
        return order
        
    async def get_order_status(self, order_id: str, symbol: str) -> OrderInfo:
        """Get the status of an order."""
        if order_id not in self.orders:
            raise ValueError(f"Order not found: {order_id}")
        return self.orders[order_id]
        
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        if order_id not in self.orders:
            raise ValueError(f"Order not found: {order_id}")
        order = self.orders[order_id]
        order.status = OrderStatus.CANCELED
        order.updated_at = datetime.now()
        return True
        
    async def get_order_book(self, symbol: str, limit: int = 20) -> Tuple[List[OrderBookEntry], List[OrderBookEntry]]:
        """Get the current order book for a trading pair."""
        self._get_market_info(symbol)  # Validate symbol exists
            
        bids = [
            OrderBookEntry(
                price=Decimal("49900.0"),
                amount=Decimal("1.0"),
                timestamp=datetime.now()
            ),
            OrderBookEntry(
                price=Decimal("49800.0"),
                amount=Decimal("2.0"),
                timestamp=datetime.now()
            )
        ]
        
        asks = [
            OrderBookEntry(
                price=Decimal("50100.0"),
                amount=Decimal("1.0"),
                timestamp=datetime.now()
            ),
            OrderBookEntry(
                price=Decimal("50200.0"),
                amount=Decimal("2.0"),
                timestamp=datetime.now()
            )
        ]
        
        return bids[:limit], asks[:limit]
        
    async def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """Get the trading fees for a specific trading pair."""
        self._get_market_info(symbol)  # Validate symbol exists
        return {
            "maker": Decimal("0.001"),
            "taker": Decimal("0.001")
        }
        
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeInfo]:
        """Get recent trades for a trading pair."""
        self._get_market_info(symbol)  # Validate symbol exists
            
        trades = [
            TradeInfo(
                trade_id="1",
                order_id="1",
                symbol=symbol,
                side=OrderSide.BUY,
                amount=Decimal("1.0"),
                price=Decimal("50000.0"),
                timestamp=datetime.now(),
                fee=Decimal("0.001"),
                fee_currency="USDT"
            ),
            TradeInfo(
                trade_id="2",
                order_id="2",
                symbol=symbol,
                side=OrderSide.SELL,
                amount=Decimal("0.5"),
                price=Decimal("50100.0"),
                timestamp=datetime.now(),
                fee=Decimal("0.001"),
                fee_currency="USDT"
            )
        ]
        
        return trades[:limit]
        
    async def subscribe_to_ticker(self, symbol: str, callback) -> None:
        """Subscribe to real-time ticker updates."""
        pass
        
    async def subscribe_to_trades(self, symbol: str, callback) -> None:
        """Subscribe to real-time trade updates."""
        pass
        
    async def subscribe_to_order_book(self, symbol: str, callback) -> None:
        """Subscribe to real-time order book updates."""
        pass 