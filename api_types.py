"""
Defines custom types, type aliases, and data structures for the API interactions.

This module centralizes type definitions used across the `src.api` package
to improve readability, maintainability, and enable static type checking.
"""

from typing_extensions import TypeAlias, Literal, TypedDict, NamedTuple, Optional, List
import time
from decimal import Decimal
from datetime import datetime

# --- Primitive Type Aliases ---

Symbol: TypeAlias = str
"""Represents a trading pair symbol (e.g., 'BTCUSDT')."""

OrderID: TypeAlias = str
"""Represents a unique identifier for an order."""

Timestamp: TypeAlias = int
"""Represents a Unix timestamp in milliseconds."""

Price: TypeAlias = float
"""Represents the price of an asset."""

Quantity: TypeAlias = float
"""Represents the quantity of an asset."""

# --- Enum-like Types ---

OrderSide = Literal["BUY", "SELL"]
"""Represents the side of an order."""

OrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP_LOSS",
    "STOP_LOSS_LIMIT",
    "TAKE_PROFIT",
    "TAKE_PROFIT_LIMIT",
    "LIMIT_MAKER",
]
"""Represents the type of an order."""

OrderStatus = Literal[
    "NEW",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELED",
    "PENDING_CANCEL",
    "REJECTED",
    "EXPIRED",
]
"""Represents the status of an order."""

# --- Data Structures ---


class TickerInfo(TypedDict):
    """Represents ticker price information for a symbol."""

    symbol: Symbol
    price: Price


class Order(NamedTuple):
    """Represents details of a trading order."""

    symbol: Symbol
    orderId: OrderID
    clientOrderId: str
    price: Price
    origQty: Quantity
    executedQty: Quantity
    cummulativeQuoteQty: float
    status: OrderStatus
    timeInForce: str # GTC, IOC, FOK
    type: OrderType
    side: OrderSide
    stopPrice: Optional[Price]
    icebergQty: Optional[Quantity]
    time: Timestamp
    updateTime: Timestamp
    isWorking: bool
    origQuoteOrderQty: Optional[Quantity]


class AccountBalance(NamedTuple):
    """Represents the balance of a specific asset in the account."""

    asset: str
    free: Quantity
    locked: Quantity


# --- Exception/Error Types (Potentially) ---
# Although exceptions.py exists, we could define specific error data structures here if needed.

class ApiErrorData(TypedDict):
    """Structure for data returned during an API error."""
    code: int
    msg: str


class OrderBookEntry(NamedTuple):
    """Represents a single entry in an order book."""
    price: Decimal
    quantity: Decimal
    timestamp: datetime


class OrderInfo(NamedTuple):
    """Represents information about an order."""
    order_id: str
    symbol: str
    status: str
    side: str
    type: str
    price: Optional[Decimal]
    amount: Decimal
    filled_amount: Decimal
    remaining_amount: Decimal
    timestamp: int


# --- Test Function --- #

def _test_types() -> bool:
    """
    Performs a quick, independent, repeatable self-test of the defined types.

    Returns:
        bool: True if basic instantiation and access work, False otherwise.
    """
    print("Running type self-test...")
    try:
        # Test primitive aliases (static checking helps more here)
        symbol: Symbol = "BTCUSDT"
        order_id: OrderID = "12345"
        ts: Timestamp = int(time.time() * 1000)
        price: Price = 50000.1
        qty: Quantity = 0.001

        # Test Literal types
        side: OrderSide = "BUY"
        order_type: OrderType = "LIMIT"
        status: OrderStatus = "NEW"

        # Test TickerInfo
        ticker = TickerInfo(symbol="ETHUSDT", price=4000.0)
        assert ticker["symbol"] == "ETHUSDT"
        assert ticker["price"] == 4000.0
        print(f"TickerInfo test passed: {ticker}")

        # Test Order
        order = Order(
            symbol=symbol,
            orderId=order_id,
            clientOrderId="my_order_1",
            price=price,
            origQty=qty,
            executedQty=0.0,
            cummulativeQuoteQty=0.0,
            status=status,
            timeInForce="GTC",
            type=order_type,
            side=side,
            stopPrice=None,
            icebergQty=None,
            time=ts,
            updateTime=ts,
            isWorking=True,
            origQuoteOrderQty=None,
        )
        assert order.symbol == symbol
        assert order.side == "BUY"
        assert order.status == "NEW"
        print(f"Order test passed: {order}")

        # Test AccountBalance
        balance = AccountBalance(asset="BTC", free=1.5, locked=0.2)
        assert balance.asset == "BTC"
        assert balance.free == 1.5
        assert balance.locked == 0.2
        print(f"AccountBalance test passed: {balance}")

        # Test ApiErrorData
        error_data = ApiErrorData(code=-1021, msg="Timestamp for this request was 1000ms ahead of the server time.")
        assert error_data['code'] == -1021
        assert "Timestamp" in error_data['msg']
        print(f"ApiErrorData test passed: {error_data}")


        # Example of how these types prevent *some* errors (caught by static analysis)
        # ticker_invalid: TickerInfo = TickerInfo(symbol="SOLUSDT", price="invalid_price") # Type checker error
        # order_invalid_side: Order = Order(..., side="INVALID_SIDE", ...) # Type checker error

        print("Type self-test completed successfully.")
        return True

    except Exception as e:
        print(f"Type self-test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_result = _test_types()
    print(f"Self-test result: {test_result}")
    # Exit with non-zero code if test failed, useful for CI/CD
    exit(0 if test_result else 1)

class BinanceOrderResponse(TypedDict):
    """Response from Binance order endpoints."""
    symbol: str
    orderId: str
    clientOrderId: str
    price: str
    origQty: str
    executedQty: str
    cummulativeQuoteQty: str
    status: str
    timeInForce: str
    type: str
    side: str
    stopPrice: Optional[str]
    icebergQty: Optional[str]
    time: int
    updateTime: int
    isWorking: bool
    origQuoteOrderQty: Optional[str]

class BinanceOrderBookResponse(TypedDict):
    """Response from Binance order book endpoint."""
    lastUpdateId: int
    bids: List[List[str]]
    asks: List[List[str]]

class BinanceTradeResponse(TypedDict):
    """Response from Binance trade endpoints."""
    id: int
    price: str
    qty: str
    time: int
    isBuyerMaker: bool
    isBestMatch: bool

class BinanceBalanceResponse(TypedDict):
    """Response from Binance balance endpoint."""
    asset: str
    free: str
    locked: str

class BinanceTickerResponse(TypedDict):
    """Response from Binance ticker endpoint."""
    symbol: str
    price: str
    priceChange: str
    priceChangePercent: str
    weightedAvgPrice: str
    prevClosePrice: str
    lastQty: str
    bidPrice: str
    bidQty: str
    askPrice: str
    askQty: str
    openPrice: str
    highPrice: str
    lowPrice: str
    volume: str
    quoteVolume: str
    openTime: int
    closeTime: int
    firstId: int
    lastId: int
    count: int

class BinanceWebsocketMessage(TypedDict):
    """Base type for Binance websocket messages."""
    stream: str
    data: dict
