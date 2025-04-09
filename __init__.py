"""
API package initialization.
Exposes the main components for interacting with cryptocurrency exchanges and economic data.
"""

from .exchange_interface import (
    ExchangeInterface,
    OrderType,
    OrderSide,
    OrderStatus,
    OrderBookEntry,
    OrderInfo
)
from .binance_exchange import BinanceExchange
from .binance_api import BinanceAPI
from .fred_api import FredAPI

__all__ = [
    'ExchangeInterface',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'OrderBookEntry',
    'OrderInfo',
    'BinanceExchange',
    'BinanceAPI',
    'FredAPI'
] 