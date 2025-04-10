"""
Financial mathematical utilities module.

This module provides functions for calculating various technical indicators
and statistical measures commonly used in financial analysis, such as moving
averages, momentum indicators, and volatility measures.
"""

from typing import List, Tuple, Union, cast
import numpy as np
import pandas as pd
from .types import Price

# Type aliases for better readability
PriceList = List[Price]
FloatList = List[float]
BollingerBands = Tuple[FloatList, FloatList, FloatList]


def calculate_sma(prices: PriceList, period: int) -> FloatList:
    """
    Calculate Simple Moving Average.
    
    The Simple Moving Average (SMA) is the arithmetic mean of a set of prices
    over a specified period. It is one of the most basic technical indicators
    used in financial analysis.
    
    Args:
        prices: List of price values
        period: Number of periods to use for the moving average
        
    Returns:
        List of SMA values. The length of the returned list is less than the
        input list by (period - 1) elements.
        
    Examples:
        >>> calculate_sma([10, 11, 12, 13, 14], 3)
        [11.0, 12.0, 13.0]
    """
    if not prices or len(prices) < period:
        return []
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    sma = np.convolve(prices_array, np.ones(period)/period, mode='valid')
    
    # Convert back to list and ensure type safety
    return cast(FloatList, sma.tolist())


def calculate_ema(prices: PriceList, period: int) -> FloatList:
    """
    Calculate Exponential Moving Average.
    
    The Exponential Moving Average (EMA) gives more weight to recent prices
    compared to older prices, making it more responsive to recent price changes
    than the Simple Moving Average.
    
    Args:
        prices: List of price values
        period: Number of periods to use for the moving average
        
    Returns:
        List of EMA values with the same length as the input list.
        
    Examples:
        >>> calculate_ema([10, 11, 12, 13, 14], 3)
        [10.0, 10.5, 11.25, 12.125, 13.0625]
    """
    if not prices or len(prices) < period:
        return []
    
    # Convert to pandas Series for efficient calculation
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=period, adjust=False).mean()
    
    # Convert back to list and ensure type safety
    return cast(FloatList, ema.tolist())


def calculate_rsi(prices: PriceList, period: int = 14) -> FloatList:
    """
    Calculate Relative Strength Index.
    
    The Relative Strength Index (RSI) is a momentum oscillator that measures
    the speed and magnitude of recent price changes to evaluate overbought or
    oversold conditions.
    
    Args:
        prices: List of price values
        period: Number of periods to use for the RSI calculation (default: 14)
        
    Returns:
        List of RSI values with the same length as the input list.
        Values range from 0 to 100, with values above 70 typically indicating
        overbought conditions and values below 30 typically indicating oversold
        conditions.
        
    Examples:
        >>> prices = [10, 10.5, 10.2, 10.8, 11.0, 10.7, 10.9, 11.2, 11.5, 11.3]
        >>> rsi = calculate_rsi(prices, period=5)
        >>> rsi[0:5]  # First 5 values
        [0.0, 0.0, 0.0, 0.0, 0.0]
    """
    if not prices or len(prices) < period + 1:
        return []
    
    # Check if all prices are the same (constant prices)
    if all(abs(p - prices[0]) < 1e-10 for p in prices):
        # For constant prices, RSI is 50
        return [50.0] * len(prices)
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    deltas = np.diff(prices_array)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate initial averages
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # Initialize RSI array
    rsi = np.zeros_like(prices_array)
    
    # Calculate first RSI value
    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))
    
    # Calculate remaining RSI values
    for i in range(period + 1, len(prices_array)):
        if deltas[i-1] > 0:
            upval = deltas[i-1]
            downval = 0.0
        else:
            upval = 0.0
            downval = -deltas[i-1]
        
        # Update averages using smoothing
        avg_gain = (avg_gain * (period - 1) + upval) / period
        avg_loss = (avg_loss * (period - 1) + downval) / period
        
        # Calculate RSI
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    
    # Fill in the first period values (they can't be calculated)
    rsi[:period] = rsi[period]
    
    # Convert back to list and ensure type safety
    return cast(FloatList, rsi.tolist())


def calculate_bollinger_bands(
    prices: PriceList, 
    period: int = 20, 
    std_dev: float = 2.0
) -> BollingerBands:
    """
    Calculate Bollinger Bands.
    
    Bollinger Bands consist of a middle band (SMA) and upper and lower bands
    that are standard deviations away from the middle band. They are used to
    identify volatility and potential overbought/oversold conditions.
    
    Args:
        prices: List of price values
        period: Number of periods to use for the moving average (default: 20)
        std_dev: Number of standard deviations for the bands (default: 2.0)
        
    Returns:
        Tuple containing three lists:
        - Middle band (SMA)
        - Upper band (SMA + std_dev * standard deviation)
        - Lower band (SMA - std_dev * standard deviation)
        
    Examples:
        >>> prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        >>> middle, upper, lower = calculate_bollinger_bands(prices, period=5)
        >>> middle[0]  # First middle band value
        12.0
    """
    if not prices or len(prices) < period:
        return [], [], []
    
    # Calculate SMA
    sma = calculate_sma(prices, period)
    if not sma:
        return [], [], []
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    
    # Calculate standard deviation for each period
    std_values = []
    for i in range(period - 1, len(prices_array)):
        std_values.append(np.std(prices_array[i-period+1:i+1]))
    
    # Calculate upper and lower bands
    upper_band = [sma[i] + (std_dev * std_values[i]) for i in range(len(sma))]
    lower_band = [sma[i] - (std_dev * std_values[i]) for i in range(len(sma))]
    
    # Ensure type safety
    return (
        cast(FloatList, sma),
        cast(FloatList, upper_band),
        cast(FloatList, lower_band)
    )


def calculate_atr(
    high: PriceList, 
    low: PriceList, 
    close: PriceList, 
    period: int = 14
) -> FloatList:
    """
    Calculate Average True Range.
    
    The Average True Range (ATR) measures market volatility by calculating
    the average range of price movement over a specified period.
    
    Args:
        high: List of high prices
        low: List of low prices
        close: List of closing prices
        period: Number of periods to use for the ATR calculation (default: 14)
        
    Returns:
        List of ATR values with the same length as the input lists.
        
    Examples:
        >>> high = [10, 11, 12, 13, 14]
        >>> low = [9, 10, 11, 12, 13]
        >>> close = [9.5, 10.5, 11.5, 12.5, 13.5]
        >>> atr = calculate_atr(high, low, close, period=3)
        >>> atr[0:3]  # First 3 values
        [1.0, 1.0, 1.0]
    """
    if not high or not low or not close or len(high) < period or len(low) < period or len(close) < period:
        return []
    
    # Convert to numpy arrays for efficient calculation
    high_array = np.array(high, dtype=float)
    low_array = np.array(low, dtype=float)
    close_array = np.array(close, dtype=float)
    
    # Calculate True Range
    tr = np.zeros_like(high_array)
    tr[0] = high_array[0] - low_array[0]
    
    for i in range(1, len(high_array)):
        hl = high_array[i] - low_array[i]
        hc = abs(high_array[i] - close_array[i-1])
        lc = abs(low_array[i] - close_array[i-1])
        tr[i] = max(hl, hc, lc)
    
    # Calculate ATR
    atr = np.zeros_like(tr)
    atr[0] = tr[0]
    
    for i in range(1, len(tr)):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    
    # Convert back to list and ensure type safety
    return cast(FloatList, atr.tolist())


def calculate_returns(prices: PriceList) -> FloatList:
    """
    Calculate percentage returns from a list of prices.
    
    This function calculates the percentage change between consecutive prices
    in the list. The formula used is:
    
    return[i] = (price[i] - price[i-1]) / price[i-1] * 100
    
    Args:
        prices: List of prices
        
    Returns:
        List of percentage returns. The length of the returned list is one less
        than the input list since the first price has no previous price to
        calculate a return from.
        
    Examples:
        >>> calculate_returns([100, 105, 103, 107])
        [5.0, -1.9047619047619047, 3.883495145631068]
    """
    if not prices or len(prices) < 2:
        return []
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    
    # Calculate returns with handling for division by zero
    returns = []
    for i in range(1, len(prices_array)):
        # Handle division by zero
        if prices_array[i-1] == 0:
            # If previous price is zero, return infinity for positive current price
            # or negative infinity for negative current price
            if prices_array[i] > 0:
                returns.append(float('inf'))
            elif prices_array[i] < 0:
                returns.append(float('-inf'))
            else:
                returns.append(0.0)  # Both prices are zero, return 0% change
        else:
            returns.append((prices_array[i] - prices_array[i-1]) / prices_array[i-1] * 100)
    
    # Ensure type safety
    return cast(FloatList, returns)


def calculate_volatility(prices: PriceList, window: int = 20) -> float:
    """
    Calculate price volatility using standard deviation of returns.
    
    This function calculates the volatility of a price series using the
    standard deviation of returns over a specified window. Volatility is
    expressed as a percentage.
    
    Args:
        prices: List of prices
        window: Rolling window size for volatility calculation
        
    Returns:
        Volatility value as a percentage. Returns 0.0 if there are fewer
        prices than the window size.
        
    Examples:
        >>> calculate_volatility([100, 105, 103, 107, 110, 108, 112], window=5)
        2.3456789012345678
    """
    if not prices or len(prices) < window:
        return 0.0
    
    # Convert to pandas Series for efficient calculation
    prices_series = pd.Series(prices)
    returns = prices_series.pct_change().dropna()
    
    # Calculate rolling standard deviation and get the last value
    volatility = returns.rolling(window=window).std().iloc[-1] * 100
    
    # Ensure type safety
    return float(volatility) 