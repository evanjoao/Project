"""
Financial metrics calculation module.

This module provides functions for calculating various financial metrics
such as returns, Sharpe ratio, maximum drawdown, win rate, profit factor,
and volatility. These metrics are commonly used in financial analysis
and trading strategy evaluation.
"""

from typing import List, Dict, Union, TypeVar, cast, Any
import numpy as np
from .types import Price, Amount

# Define type aliases for better readability
PriceList = List[Price]
ReturnList = List[float]
TradeList = List[Dict[str, Union[Price, Amount]]]

def calculate_returns(prices: PriceList) -> ReturnList:
    """
    Calculate percentage returns from a list of prices.
    
    This function calculates the percentage change between consecutive prices
    in the list. The formula used is:
    
    return[i] = (price[i] - price[i-1]) / price[i-1]
    
    Args:
        prices: List of prices
        
    Returns:
        List of percentage returns. The length of the returned list is one less
        than the input list since the first price has no previous price to
        calculate a return from.
        
    Examples:
        >>> calculate_returns([100, 105, 103, 107])
        [0.05, -0.01904761904761905, 0.03883495145631068]
    """
    if not prices or len(prices) < 2:
        return []
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    
    # Calculate returns with handling for division by zero
    returns = []
    for i in range(1, len(prices_array)):
        if prices_array[i-1] == 0:
            # If previous price is zero, return infinity for positive current price
            # or negative infinity for negative current price
            if prices_array[i] > 0:
                returns.append(float('inf'))
            elif prices_array[i] < 0:
                returns.append(float('-inf'))
            else:
                returns.append(0.0)  # Both prices are zero
        else:
            returns.append((prices_array[i] - prices_array[i-1]) / prices_array[i-1])
    
    return cast(ReturnList, returns)

def calculate_sharpe_ratio(returns: ReturnList, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio.
    
    The Sharpe ratio is a measure of risk-adjusted return. It is calculated as:
    
    Sharpe Ratio = (R_p - R_f) / σ_p
    
    where:
    - R_p is the return of the portfolio
    - R_f is the risk-free rate
    - σ_p is the standard deviation of the portfolio's excess return
    
    Args:
        returns: List of returns
        risk_free_rate: Annual risk-free rate (default: 0.02 or 2%)
        
    Returns:
        Sharpe ratio. Returns 0.0 if there are fewer than 2 returns.
        
    Examples:
        >>> calculate_sharpe_ratio([0.01, 0.02, -0.01, 0.03])
        1.2345678901234567
    """
    if len(returns) < 2:
        return 0.0
    
    # Convert to numpy array for efficient calculation
    returns_array = np.array(returns, dtype=float)
    
    # Calculate daily risk-free rate (assuming 252 trading days per year)
    daily_rf = risk_free_rate / 252
    
    # Calculate excess returns
    excess_returns = returns_array - daily_rf
    
    # Calculate Sharpe ratio (annualized)
    return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))

def calculate_max_drawdown(prices: PriceList) -> float:
    """
    Calculate maximum drawdown.
    
    Maximum drawdown is the maximum observed loss from a peak to a trough
    of a portfolio, before a new peak is attained. It is expressed as a
    percentage of the peak value.
    
    Args:
        prices: List of prices
        
    Returns:
        Maximum drawdown as a decimal (e.g., 0.25 for 25% drawdown)
        
    Examples:
        >>> calculate_max_drawdown([100, 90, 80, 95, 85, 70])
        0.3
    """
    if not prices or len(prices) < 2:
        return 0.0
    
    # Convert to numpy array for efficient calculation
    prices_array = np.array(prices, dtype=float)
    
    # Calculate running maximum
    peak = np.maximum.accumulate(prices_array)
    
    # Calculate drawdown
    drawdown = (prices_array - peak) / peak
    
    # Return absolute value of maximum drawdown
    return float(abs(np.min(drawdown)))

def calculate_win_rate(trades: TradeList) -> float:
    """
    Calculate win rate from a list of trades.
    
    Win rate is the percentage of trades that result in a profit.
    
    Args:
        trades: List of trade dictionaries, each containing at least a 'profit' key
        
    Returns:
        Win rate as a decimal between 0 and 1 (e.g., 0.65 for 65% win rate)
        
    Examples:
        >>> trades = [{'profit': 10}, {'profit': -5}, {'profit': 15}, {'profit': -8}]
        >>> calculate_win_rate(trades)
        0.5
    """
    if not trades:
        return 0.0
    
    winning_trades = sum(1 for trade in trades if trade['profit'] > 0)
    return winning_trades / len(trades)

def calculate_profit_factor(trades: TradeList) -> float:
    """
    Calculate profit factor.
    
    Profit factor is the ratio of gross profit to gross loss. It is a measure
    of the strategy's profitability relative to its losses.
    
    Args:
        trades: List of trade dictionaries, each containing at least a 'profit' key
        
    Returns:
        Profit factor. Returns infinity if there are no losses.
        
    Examples:
        >>> trades = [{'profit': 10}, {'profit': -5}, {'profit': 15}, {'profit': -8}]
        >>> calculate_profit_factor(trades)
        2.5
    """
    if not trades:
        return 0.0
    
    gross_profit = sum(trade['profit'] for trade in trades if trade['profit'] > 0)
    gross_loss = abs(sum(trade['profit'] for trade in trades if trade['profit'] < 0))
    
    return gross_profit / gross_loss if gross_loss != 0 else float('inf')

def calculate_volatility(returns: ReturnList, annualize: bool = True) -> float:
    """
    Calculate volatility of returns.
    
    Volatility is a measure of the dispersion of returns. It is calculated as
    the standard deviation of returns.
    
    Args:
        returns: List of returns
        annualize: Whether to annualize the volatility (default: True)
                  Assumes 252 trading days per year if True
        
    Returns:
        Volatility. If annualize is True, returns annualized volatility.
        
    Examples:
        >>> calculate_volatility([0.01, 0.02, -0.01, 0.03])
        0.12345678901234567
    """
    if len(returns) < 2:
        return 0.0
    
    # Convert to numpy array for efficient calculation
    returns_array = np.array(returns, dtype=float)
    
    # Calculate volatility
    vol = float(np.std(returns_array))
    
    # Annualize if requested (assuming 252 trading days per year)
    return vol * np.sqrt(252) if annualize else vol 