from typing import Any, Dict, List, Union
from .exceptions import ValidationError

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")
    if not symbol.isupper():
        raise ValidationError("Symbol must be uppercase")
    if len(symbol) < 2:
        raise ValidationError("Symbol must be at least 2 characters")
    return True

def validate_price(price: float) -> bool:
    """Validate price value"""
    if not isinstance(price, (int, float)):
        raise ValidationError("Price must be a number")
    if price <= 0:
        raise ValidationError("Price must be positive")
    return True

def validate_amount(amount: float) -> bool:
    """Validate amount value"""
    if not isinstance(amount, (int, float)):
        raise ValidationError("Amount must be a number")
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    return True

def validate_timeframe(timeframe: str) -> bool:
    """
    Validate timeframe format.
    
    This function validates that the timeframe string is in the correct format.
    A valid timeframe consists of a number followed by a unit (m, h, d, w).
    For example: '1m', '5m', '15m', '1h', '4h', '1d', '1w'.
    
    Args:
        timeframe: Timeframe string to validate
        
    Returns:
        True if the timeframe is valid
        
    Raises:
        ValidationError: If the timeframe is invalid
    """
    if not isinstance(timeframe, str):
        raise ValidationError("Timeframe must be a string")
        
    if not timeframe or len(timeframe) < 2:
        raise ValidationError("Timeframe must be at least 2 characters")
    
    valid_units = ['m', 'h', 'd', 'w']
    unit = timeframe[-1]
    
    if unit not in valid_units:
        raise ValidationError(f"Invalid timeframe unit. Must be one of {valid_units}")
    
    try:
        value = int(timeframe[:-1])
        if value <= 0:
            raise ValidationError("Timeframe value must be positive")
    except ValueError:
        raise ValidationError("Timeframe must start with a number")
    
    # Check against predefined list for backward compatibility
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    if timeframe not in valid_timeframes:
        # Log a warning but don't raise an error for backward compatibility
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Timeframe '{timeframe}' is not in the standard list: {valid_timeframes}")
    
    return True

def validate_order_type(order_type: str) -> bool:
    """Validate order type"""
    valid_types = ['MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT']
    if order_type not in valid_types:
        raise ValidationError(f"Invalid order type. Must be one of {valid_types}")
    return True

def validate_order_side(side: str) -> bool:
    """Validate order side"""
    valid_sides = ['BUY', 'SELL']
    if side not in valid_sides:
        raise ValidationError(f"Invalid order side. Must be one of {valid_sides}")
    return True 