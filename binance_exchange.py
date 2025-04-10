"""
Binance exchange implementation using CCXT library.
Provides a concrete implementation of the ExchangeInterface for Binance.
"""

import ccxt.async_support as ccxt
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Callable, Union, TypedDict, Any
from datetime import datetime
import asyncio
import logging
from .exchange_interface import (
    ExchangeInterface,
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo,
    TradeInfo
)
from .rate_limiter import RateLimiter, RateLimitConfig
from .exceptions import APIError, RateLimitError, OrderError
from .api_types import OrderBookEntry  # Remove OrderInfo from here

logger = logging.getLogger(__name__)

class CCXTConfig(TypedDict, total=False):
    enableRateLimit: bool
    apiKey: str
    secret: str
    passphrase: str
    password: str
    privateKey: str
    walletAddress: str
    uid: str
    verbose: bool
    testnet: bool
    sandbox: bool
    options: Dict[str, Any]
    httpsProxy: str
    socksProxy: str
    wssProxy: str
    proxy: str
    rateLimit: int

class BinanceExchange(ExchangeInterface):
    """Binance exchange implementation using CCXT."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False):
        """
        Initialize Binance exchange client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: False)
        """
        config: CCXTConfig = {
            'enableRateLimit': True,
            'apiKey': api_key or '',
            'secret': api_secret or ''
        }
        
        self.exchange = ccxt.binance(config)  # type: ignore[arg-type]
        
        if testnet:
            self.exchange.set_sandbox_mode(True)
            
        self.rate_limiter = RateLimiter()
        rate_config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=20,
            name="binance"
        )
        self.rate_limiter.add_limiter("binance", rate_config)  # 10 requests per second, burst of 20
        
        self._ws_clients = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def close(self):
        """Close all connections."""
        await self.exchange.close()
        for client in self._ws_clients.values():
            await client.close()
            
    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert internal order type to CCXT order type."""
        return order_type.value
        
    def _convert_order_side(self, side: OrderSide) -> str:
        """Convert internal order side to CCXT order side."""
        return side.value
        
    def _convert_order_status(self, status: str) -> OrderStatus:
        """Convert CCXT order status to internal order status."""
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELED,
            'expired': OrderStatus.EXPIRED,
            'rejected': OrderStatus.REJECTED
        }
        return status_map.get(status.lower(), OrderStatus.REJECTED)
        
    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Get the current price for a trading pair."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        ticker = await self.exchange.fetch_ticker(symbol)
        return Decimal(str(ticker['last']))
        
    async def get_balance(self, asset: str) -> Decimal:
        """Get the balance of a specific asset."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        balance = await self.exchange.fetch_balance()
        return Decimal(str(balance.get(asset, {}).get('free', '0')))
        
    async def create_order(self,
                    symbol: str,
                    order_type: OrderType,
                    side: OrderSide,
                    amount: Decimal,
                    price: Optional[Decimal] = None) -> OrderInfo:
        """Create a new order."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        # Create order with CCXT
        order = await self.exchange.create_order(
            symbol=symbol,
            type=order_type.value.lower(),  # type: ignore
            side=side.value.lower(),  # type: ignore
            amount=float(amount),
            price=float(price) if price else None
        )
        
        # Ensure we have valid data
        if not order or 'id' not in order:
            raise Exception("Invalid order response from exchange")
            
        # Convert timestamps safely
        timestamp = float(str(order['timestamp'])) if order.get('timestamp') else 0
        last_trade_timestamp = float(str(order['lastTradeTimestamp'])) if order.get('lastTradeTimestamp') else 0
            
        return OrderInfo(
            order_id=str(order['id']),
            symbol=str(order['symbol']),
            order_type=order_type,
            side=side,
            amount=Decimal(str(order['amount'])),
            price=Decimal(str(order['price'])) if order.get('price') else None,
            status=self._convert_order_status(str(order['status'])),
            created_at=datetime.fromtimestamp(timestamp / 1000),
            updated_at=datetime.fromtimestamp(last_trade_timestamp / 1000) if last_trade_timestamp else datetime.now(),
            filled_amount=Decimal(str(order.get('filled', '0'))),
            average_price=Decimal(str(order['average'])) if order.get('average') else None
        )
        
    async def get_order_status(self, order_id: str, symbol: str) -> OrderInfo:
        """
        Get the status of an order.
        
        Args:
            order_id: The order ID
            symbol: The trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            OrderInfo containing the order status and details
        """
        if not self.rate_limiter.acquire('binance'):
            raise RateLimitError("Rate limit exceeded")
            
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            
            # Ensure we have valid data
            if not order or 'id' not in order:
                raise OrderError("Invalid order response from exchange")
                
            # Convert timestamps safely
            timestamp = float(str(order['timestamp'])) if order.get('timestamp') else 0
            last_trade_timestamp = float(str(order['lastTradeTimestamp'])) if order.get('lastTradeTimestamp') else 0
                
            return OrderInfo(
                order_id=str(order['id']),
                symbol=str(order['symbol']),
                order_type=OrderType(str(order['type'])),
                side=OrderSide(str(order['side'])),
                amount=Decimal(str(order['amount'])),
                price=Decimal(str(order['price'])) if order.get('price') else None,
                status=self._convert_order_status(str(order['status'])),
                created_at=datetime.fromtimestamp(timestamp / 1000),
                updated_at=datetime.fromtimestamp(last_trade_timestamp / 1000) if last_trade_timestamp else datetime.now(),
                filled_amount=Decimal(str(order.get('filled', '0'))),
                average_price=Decimal(str(order['average'])) if order.get('average') else None
            )
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {str(e)}")
            raise OrderError(f"Failed to get order status: {str(e)}")

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: The order ID to cancel
            symbol: The trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            True if the order was successfully canceled
        """
        if not self.rate_limiter.acquire('binance'):
            raise RateLimitError("Rate limit exceeded")
            
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            return result.get('status') == 'CANCELED'
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {str(e)}")
            raise OrderError(f"Failed to cancel order: {str(e)}")
            
    async def get_order_book(self, symbol: str, limit: int = 20) -> Tuple[List[OrderBookEntry], List[OrderBookEntry]]:
        """Get the current order book for a trading pair."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        order_book = await self.exchange.fetch_order_book(symbol, limit)
        
        current_time = datetime.now()
        
        bids = [
            OrderBookEntry(
                price=Decimal(str(price)),
                quantity=Decimal(str(amount)),
                timestamp=current_time
            )
            for price, amount, timestamp in order_book['bids']
        ]
        
        asks = [
            OrderBookEntry(
                price=Decimal(str(price)),
                quantity=Decimal(str(amount)),
                timestamp=current_time
            )
            for price, amount, timestamp in order_book['asks']
        ]
        
        return bids, asks
        
    async def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """Get the trading fees for a specific trading pair."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        fees = await self.exchange.fetch_trading_fee(symbol)
        return {
            'maker': Decimal(str(fees.get('maker', '0'))),
            'taker': Decimal(str(fees.get('taker', '0')))
        }
        
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeInfo]:
        """Get recent trades for a trading pair."""
        if not self.rate_limiter.acquire('binance'):
            raise Exception("Rate limit exceeded")
            
        trades = await self.exchange.fetch_trades(symbol, limit=limit)
        
        result = []
        for trade in trades:
            # Extract fee information safely
            fee_cost = Decimal('0')
            fee_currency = ''
            
            if trade.get('fee'):
                fee = trade['fee']
                if isinstance(fee, dict) and 'cost' in fee:
                    fee_cost = Decimal(str(fee['cost']))
                if isinstance(fee, dict) and 'currency' in fee:
                    fee_currency = str(fee['currency'])
            
            # Convert timestamp safely
            timestamp = float(str(trade['timestamp'])) if trade.get('timestamp') else 0
            
            result.append(TradeInfo(
                trade_id=str(trade['id']),
                order_id=str(trade.get('order', '')),
                symbol=str(trade['symbol']),
                side=OrderSide(str(trade['side'])),
                amount=Decimal(str(trade['amount'])),
                price=Decimal(str(trade['price'])),
                timestamp=datetime.fromtimestamp(timestamp / 1000),
                fee=fee_cost,
                fee_currency=fee_currency
            ))
            
        return result
        
    async def subscribe_to_ticker(self, symbol: str, callback: Callable) -> None:
        """Subscribe to real-time ticker updates."""
        # Implementation depends on specific WebSocket client being used
        pass
        
    async def subscribe_to_trades(self, symbol: str, callback: Callable) -> None:
        """Subscribe to real-time trade updates."""
        # Implementation depends on specific WebSocket client being used
        pass
        
    async def subscribe_to_order_book(self, symbol: str, callback: Callable) -> None:
        """Subscribe to real-time order book updates."""
        # Implementation depends on specific WebSocket client being used
        pass 