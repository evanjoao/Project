"""
Tests for the metrics module.

This module contains tests to verify that all financial metric calculation functions
work correctly and handle edge cases appropriately.
"""

import pytest
import numpy as np
from src.common.metrics import (
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_volatility,
)

# Define a small epsilon value for floating-point comparisons
EPSILON = 1e-10

class TestCalculateReturns:
    """Tests for the calculate_returns function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected returns."""
        prices = [100.0, 105.0, 103.0, 107.0]
        expected = [0.05, -0.01904761904761905, 0.03883495145631068]
        result = calculate_returns(prices)
        
        # Check that results are close (floating point comparison)
        assert len(result) == len(expected)
        for i in range(len(result)):
            assert abs(result[i] - expected[i]) < EPSILON
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert calculate_returns([]) == []
    
    def test_single_price(self):
        """Test that single price returns empty list."""
        assert calculate_returns([100.0]) == []
    
    def test_two_prices(self):
        """Test that two prices produce one return."""
        prices = [100.0, 105.0]
        expected = [0.05]
        result = calculate_returns(prices)
        assert abs(result[0] - expected[0]) < EPSILON
    
    def test_zero_price(self):
        """Test that zero price is handled correctly."""
        prices = [100.0, 0.0, 50.0]
        result = calculate_returns(prices)
        assert result[0] == -1.0  # (0 - 100) / 100 = -1
        assert result[1] == float('inf')  # (50 - 0) / 0 = inf

class TestCalculateSharpeRatio:
    """Tests for the calculate_sharpe_ratio function."""
    
    def test_valid_returns(self):
        """Test that valid returns produce expected Sharpe ratio."""
        # Create a series with known characteristics
        returns = [0.01, 0.02, -0.01, 0.03]
        result = calculate_sharpe_ratio(returns)
        
        # Sharpe ratio should be positive for this series
        assert result > 0
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_sharpe_ratio([]) == 0.0
    
    def test_single_return(self):
        """Test that single return returns 0.0."""
        assert calculate_sharpe_ratio([0.01]) == 0.0
    
    def test_custom_risk_free_rate(self):
        """Test that custom risk-free rate is used correctly."""
        returns = [0.01, 0.02, -0.01, 0.03]
        result1 = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        result2 = calculate_sharpe_ratio(returns, risk_free_rate=0.04)
        
        # Higher risk-free rate should result in lower Sharpe ratio
        assert result1 > result2

class TestCalculateMaxDrawdown:
    """Tests for the calculate_max_drawdown function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected maximum drawdown."""
        prices = [100.0, 90.0, 80.0, 95.0, 85.0, 70.0]
        result = calculate_max_drawdown(prices)
        
        # Maximum drawdown should be 0.3 (from 100 to 70)
        assert abs(result - 0.3) < EPSILON
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_max_drawdown([]) == 0.0
    
    def test_single_price(self):
        """Test that single price returns 0.0."""
        assert calculate_max_drawdown([100.0]) == 0.0
    
    def test_constant_prices(self):
        """Test that constant prices return 0.0 drawdown."""
        prices = [100.0] * 10
        assert abs(calculate_max_drawdown(prices)) < EPSILON
    
    def test_monotonically_increasing_prices(self):
        """Test that monotonically increasing prices return 0.0 drawdown."""
        prices = [100.0, 110.0, 120.0, 130.0, 140.0]
        assert abs(calculate_max_drawdown(prices)) < EPSILON

class TestCalculateWinRate:
    """Tests for the calculate_win_rate function."""
    
    def test_valid_trades(self):
        """Test that valid trades produce expected win rate."""
        trades = [
            {'profit': 10.0},
            {'profit': -5.0},
            {'profit': 15.0},
            {'profit': -8.0}
        ]
        result = calculate_win_rate(trades)
        
        # Win rate should be 0.5 (2 winning trades out of 4)
        assert result == 0.5
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_win_rate([]) == 0.0
    
    def test_all_winning_trades(self):
        """Test that all winning trades return 1.0."""
        trades = [
            {'profit': 10.0},
            {'profit': 5.0},
            {'profit': 15.0}
        ]
        assert calculate_win_rate(trades) == 1.0
    
    def test_all_losing_trades(self):
        """Test that all losing trades return 0.0."""
        trades = [
            {'profit': -10.0},
            {'profit': -5.0},
            {'profit': -15.0}
        ]
        assert calculate_win_rate(trades) == 0.0

class TestCalculateProfitFactor:
    """Tests for the calculate_profit_factor function."""
    
    def test_valid_trades(self):
        """Test that valid trades produce expected profit factor."""
        trades = [
            {'profit': 10.0},
            {'profit': -5.0},
            {'profit': 15.0},
            {'profit': -8.0}
        ]
        result = calculate_profit_factor(trades)
        
        # Profit factor should be 25/13 ≈ 1.923
        assert abs(result - 1.9230769230769231) < EPSILON
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_profit_factor([]) == 0.0
    
    def test_all_winning_trades(self):
        """Test that all winning trades return infinity."""
        trades = [
            {'profit': 10.0},
            {'profit': 5.0},
            {'profit': 15.0}
        ]
        assert calculate_profit_factor(trades) == float('inf')
    
    def test_all_losing_trades(self):
        """Test that all losing trades return 0.0."""
        trades = [
            {'profit': -10.0},
            {'profit': -5.0},
            {'profit': -15.0}
        ]
        assert calculate_profit_factor(trades) == 0.0

class TestCalculateVolatility:
    """Tests for the calculate_volatility function."""
    
    def test_valid_returns(self):
        """Test that valid returns produce expected volatility."""
        # Create a series with known volatility
        np.random.seed(42)
        returns = [0.01 + np.random.normal(0, 0.01) for _ in range(30)]
        
        # Calculate volatility with default annualization
        volatility = calculate_volatility(returns)
        
        # Volatility should be positive
        assert volatility > 0
        
        # Calculate without annualization
        volatility_daily = calculate_volatility(returns, annualize=False)
        
        # Daily volatility should be less than annualized volatility
        assert volatility_daily < volatility
        
        # Annualized volatility should be approximately daily volatility * sqrt(252)
        assert abs(volatility - volatility_daily * np.sqrt(252)) < EPSILON
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_volatility([]) == 0.0
    
    def test_single_return(self):
        """Test that single return returns 0.0."""
        assert calculate_volatility([0.01]) == 0.0
    
    def test_constant_returns(self):
        """Test that constant returns return 0.0 volatility."""
        returns = [0.01] * 30
        assert abs(calculate_volatility(returns)) < EPSILON 