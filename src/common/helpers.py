"""
Common helper functions used throughout the project.

This module provides general-purpose helper functions that don't fit into
other specialized modules. It focuses on data handling, JSON operations,
and risk management calculations.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def format_timestamp(timestamp: Union[int, float, str, datetime]) -> str:
    """
    Format timestamp to ISO format string.
    
    Args:
        timestamp: Timestamp to format
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")
    
    return dt.isoformat()

def calculate_returns(prices: List[float]) -> List[float]:
    """
    Calculate percentage returns from a list of prices.
    
    Args:
        prices: List of prices
        
    Returns:
        List of percentage returns
    """
    if not prices or len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        returns.append((prices[i] - prices[i-1]) / prices[i-1] * 100)
    return returns

def safe_json_loads(data: str) -> Dict[str, Any]:
    """
    Safely load JSON data with error handling.
    
    This function attempts to parse a JSON string and returns the resulting
    dictionary. If parsing fails, it logs the error and returns an empty
    dictionary.
    
    Args:
        data: JSON string to parse
        
    Returns:
        Parsed JSON data as a dictionary or empty dict if parsing fails
        
    Examples:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json_loads('invalid json')
        {}
    """
    if not isinstance(data, str):
        logger.warning(f"Expected string input, got {type(data)}")
        return {}
        
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return {}

def calculate_position_size(
    portfolio_value: float,
    risk_per_trade: float,
    stop_loss_percentage: float
) -> float:
    """
    Calculate position size based on risk parameters.
    
    This function calculates the appropriate position size based on the
    portfolio value, maximum risk per trade, and stop loss percentage.
    The calculation follows the formula:
    
    position_size = (portfolio_value * risk_per_trade) / stop_loss_percentage
    
    Args:
        portfolio_value: Total portfolio value
        risk_per_trade: Maximum risk per trade as percentage (e.g., 1.0 for 1%)
        stop_loss_percentage: Stop loss percentage (e.g., 2.0 for 2%)
        
    Returns:
        Position size in base currency
        
    Raises:
        ZeroDivisionError: If stop_loss_percentage is zero
        
    Examples:
        >>> calculate_position_size(10000, 1.0, 2.0)
        5000.0
    """
    if stop_loss_percentage == 0:
        raise ZeroDivisionError("Stop loss percentage cannot be zero")
        
    # Use absolute value of stop loss to handle negative values
    abs_stop_loss = abs(stop_loss_percentage)
    
    # Calculate risk amount in base currency
    risk_amount = portfolio_value * (risk_per_trade / 100)
    
    # Calculate position size
    position_size = risk_amount / (abs_stop_loss / 100)
    
    return position_size

def validate_timeframe(timeframe: str) -> bool:
    """
    Validate if the timeframe string is in correct format.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d')
        
    Returns:
        True if valid, False otherwise
    """
    valid_units = ['m', 'h', 'd']
    if not timeframe or len(timeframe) < 2:
        return False
    
    unit = timeframe[-1]
    if unit not in valid_units:
        return False
    
    try:
        value = int(timeframe[:-1])
        return value > 0
    except ValueError:
        return False

def calculate_volatility(prices: List[float], window: int = 20) -> float:
    """
    Calculate price volatility using standard deviation of returns.
    
    Args:
        prices: List of prices
        window: Rolling window size
        
    Returns:
        Volatility value
    """
    if len(prices) < window:
        return 0.0
    
    returns = pd.Series(prices).pct_change().dropna()
    return returns.rolling(window=window).std().iloc[-1] * 100
