from enum import Enum
from typing import Final, Dict

"""
Constants used in the API module, especially for interaction with the Binance exchange.
"""

# --- Binance REST API Endpoints (v3) --- #

# General Endpoints
EXCHANGE_INFO_ENDPOINT: Final[str] = "/v3/exchangeInfo"
SERVER_TIME_ENDPOINT: Final[str] = "/v3/time"

# Market Data Endpoints
TICKER_PRICE_ENDPOINT: Final[str] = "/v3/ticker/price"
KLINES_ENDPOINT: Final[str] = "/v3/klines"
ORDER_BOOK_ENDPOINT: Final[str] = "/v3/depth"
RECENT_TRADES_ENDPOINT: Final[str] = "/v3/trades"
AGG_TRADES_ENDPOINT: Final[str] = "/v3/aggTrades"

# Account Endpoints (Signed)
ACCOUNT_INFO_ENDPOINT: Final[str] = "/v3/account"
ORDER_ENDPOINT: Final[str] = "/v3/order"  # Includes POST, GET, DELETE
OPEN_ORDERS_ENDPOINT: Final[str] = "/v3/openOrders"
ALL_ORDERS_ENDPOINT: Final[str] = "/v3/allOrders"
MY_TRADES_ENDPOINT: Final[str] = "/v3/myTrades"

# WebSocket Streams (Base URL is defined in config.py)

# --- HTTP Methods --- #
class HttpMethod(str, Enum):
    """HTTP Methods used in API requests."""
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"

# --- Request/Response Headers & Parameters --- #
BINANCE_API_KEY_HEADER: Final[str] = "X-MBX-APIKEY"

# Common Parameter Names
PARAM_SYMBOL: Final[str] = "symbol"
PARAM_SIDE: Final[str] = "side"
PARAM_TYPE: Final[str] = "type"
PARAM_QUANTITY: Final[str] = "quantity"
PARAM_PRICE: Final[str] = "price"
PARAM_ORDER_ID: Final[str] = "orderId"
PARAM_ORIG_CLIENT_ORDER_ID: Final[str] = "origClientOrderId"
PARAM_TIMESTAMP: Final[str] = "timestamp"
PARAM_SIGNATURE: Final[str] = "signature"
PARAM_LIMIT: Final[str] = "limit"
PARAM_INTERVAL: Final[str] = "interval"
PARAM_START_TIME: Final[str] = "startTime"
PARAM_END_TIME: Final[str] = "endTime"

# --- Timeframes --- #
# Mapping for timeframe conversion (primarily used in utils.py)
TIMEFRAME_MAP: Final[Dict[str, str]] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M",
}

# --- Default Request Limits --- #
DEFAULT_KLINE_LIMIT: Final[int] = 500
DEFAULT_ORDER_BOOK_LIMIT: Final[int] = 100
DEFAULT_TRADES_LIMIT: Final[int] = 500

class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Order statuses."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"

class TimeInForce(Enum):
    """Time in force options."""
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill

class ExchangeName(Enum):
    """Exchange names."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"

class ErrorCode(Enum):
    """Error codes."""
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    NETWORK_ERROR = "NETWORK_ERROR"
    EXCHANGE_ERROR = "EXCHANGE_ERROR"

class TradingPair:
    """Trading pair utilities."""
    
    @staticmethod
    def is_valid(pair: str) -> bool:
        """Check if a trading pair is valid."""
        if not pair or "/" not in pair:
            return False
        
        parts = pair.split("/")
        if len(parts) != 2:
            return False
        
        base, quote = parts
        return bool(base and quote)
