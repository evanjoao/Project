"""
Utility functions for API operations.
Contains helper functions for formatting, validation, and data conversion.
"""

from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime

def format_binance_order_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Format Binance order response to internal format.
    
    Args:
        response: Raw response from Binance API
        
    Returns:
        Formatted order information
    """
    return {
        'order_id': response['orderId'],
        'symbol': response['symbol'],
        'price': Decimal(response['price']),
        'quantity': Decimal(response['origQty']),
        'status': response['status'].lower(),
        'side': response['side'].lower(),
        'type': response['type'].lower(),
        'timestamp': datetime.fromtimestamp(response['time'] / 1000)
    }

def convert_binance_timeframe(timeframe: str) -> str:
    """Convert internal timeframe format to Binance format.
    
    Args:
        timeframe: Internal timeframe format (e.g., '1h', '4h', '1d')
        
    Returns:
        Binance timeframe format
    """
    timeframe_map = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1w'
    }
    return timeframe_map.get(timeframe, '1h')

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(symbol, str):
        return False
    return len(symbol) >= 6 and symbol.isupper()

def format_number(number: float, decimals: int = 8) -> str:
    """Format number to string with specified decimals.
    
    Args:
        number: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    return f"{number:.{decimals}f}".rstrip('0').rstrip('.') 