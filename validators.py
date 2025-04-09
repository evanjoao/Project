"""
Input validation utilities for API requests.

This module provides reusable validation functions for common API input patterns
including trading pairs, numeric ranges, dates, and API keys.
"""

import re
from typing import Optional, Union, Tuple, Any
from datetime import datetime
from dateutil.parser import parse
from pydantic import BaseModel, Field, model_validator, ValidationError

# Regular expression patterns
TRADING_PAIR_PATTERN = r'^[A-Z0-9]+/[A-Z0-9]+$'
API_KEY_PATTERN = r'^[A-Za-z0-9]{32,}$'
API_SECRET_PATTERN = r'^[A-Za-z0-9]{64,}$'

class NumericRange(BaseModel):
    """Validates numeric ranges with optional min/max bounds."""
    value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    @model_validator(mode='after')
    def validate_range(self) -> Any:
        if self.min_value is not None and self.value < self.min_value:
            raise ValueError(f'Value must be greater than or equal to {self.min_value}')
        if self.max_value is not None and self.value > self.max_value:
            raise ValueError(f'Value must be less than or equal to {self.max_value}')
        return self

def validate_trading_pair(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a trading pair symbol (e.g., 'BTC/USDT').
    
    Args:
        symbol: Trading pair symbol to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(TRADING_PAIR_PATTERN, symbol):
        return False, "Invalid trading pair format. Expected format: BASE/QUOTE (e.g., BTC/USDT)"
    return True, None

def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validates an API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(API_KEY_PATTERN, api_key):
        return False, "Invalid API key format"
    return True, None

def validate_api_secret(api_secret: str) -> Tuple[bool, Optional[str]]:
    """
    Validates an API secret format.
    
    Args:
        api_secret: API secret to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not re.match(API_SECRET_PATTERN, api_secret):
        return False, "Invalid API secret format"
    return True, None

def validate_datetime_range(
    start_time: Union[str, datetime],
    end_time: Union[str, datetime]
) -> Tuple[bool, Optional[str]]:
    """
    Validates a datetime range.
    
    Args:
        start_time: Start time (string or datetime)
        end_time: End time (string or datetime)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        start = parse(start_time) if isinstance(start_time, str) else start_time
        end = parse(end_time) if isinstance(end_time, str) else end_time
        
        if end <= start:
            return False, "End time must be after start time"
        return True, None
    except ValueError as e:
        return False, f"Invalid datetime format: {str(e)}"

def validate_numeric_range(
    value: float,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validates a numeric value against optional min/max bounds.
    
    Args:
        value: Value to validate
        min_value: Optional minimum value
        max_value: Optional maximum value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if min_value is not None and value < min_value:
            return False, f"Value must be greater than or equal to {min_value}"
        if max_value is not None and value > max_value:
            return False, f"Value must be less than or equal to {max_value}"
        return True, None
    except ValueError as e:
        return False, str(e) 