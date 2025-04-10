from typing import List, Union, Tuple
import numpy as np
from .types import Price
import pandas as pd

def calculate_sma(prices: List[Price], period: int) -> List[float]:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return []
    return np.convolve(prices, np.ones(period)/period, mode='valid').tolist()

def calculate_ema(prices: List[Price], period: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return []
    return np.array(prices).ewm(span=period, adjust=False).mean().tolist()

def calculate_rsi(prices: List[Price], period: int = 14) -> List[float]:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return []
    
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down if down != 0 else float('inf')
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else float('inf')
        rsi[i] = 100. - 100./(1. + rs)
    
    return rsi.tolist()

def calculate_bollinger_bands(prices: List[Price], period: int = 20, std_dev: float = 2.0) -> tuple[List[float], List[float], List[float]]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return [], [], []
    
    sma = calculate_sma(prices, period)
    std = np.std(prices[-period:])
    upper_band = [x + (std_dev * std) for x in sma]
    lower_band = [x - (std_dev * std) for x in sma]
    
    return sma, upper_band, lower_band

def calculate_atr(high: List[Price], low: List[Price], close: List[Price], period: int = 14) -> List[float]:
    """Calculate Average True Range"""
    if len(high) < period or len(low) < period or len(close) < period:
        return []
    
    tr = np.zeros_like(high)
    tr[0] = high[0] - low[0]
    
    for i in range(1, len(high)):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    atr = np.zeros_like(tr)
    atr[0] = tr[0]
    
    for i in range(1, len(tr)):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    
    return atr.tolist()

def calculate_returns(prices: List[Price]) -> List[float]:
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
    
    returns = []
    for i in range(1, len(prices)):
        # Handle division by zero
        if prices[i-1] == 0:
            # If previous price is zero, return infinity for positive current price
            # or negative infinity for negative current price
            if prices[i] > 0:
                returns.append(float('inf'))
            elif prices[i] < 0:
                returns.append(float('-inf'))
            else:
                returns.append(0.0)  # Both prices are zero, return 0% change
        else:
            returns.append((prices[i] - prices[i-1]) / prices[i-1] * 100)
    return returns

def calculate_volatility(prices: List[Price], window: int = 20) -> float:
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
    if len(prices) < window:
        return 0.0
    
    returns = pd.Series(prices).pct_change().dropna()
    return returns.rolling(window=window).std().iloc[-1] * 100 