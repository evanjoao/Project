"""
Tests for the math_utils module.

This module contains tests to verify that all mathematical utility functions
work correctly and handle edge cases appropriately.
"""

import pytest
import numpy as np
from src.common.math_utils import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_returns,
    calculate_volatility,
)

class TestCalculateReturns:
    """Tests for the calculate_returns function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected returns."""
        prices = [100.0, 105.0, 103.0, 107.0]
        expected = [5.0, -1.9047619047619047, 3.883495145631068]
        result = calculate_returns(prices)
        
        # Check that results are close (floating point comparison)
        assert len(result) == len(expected)
        for i in range(len(result)):
            assert abs(result[i] - expected[i]) < 1e-10
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert calculate_returns([]) == []
    
    def test_single_price(self):
        """Test that single price returns empty list."""
        assert calculate_returns([100.0]) == []
    
    def test_two_prices(self):
        """Test that two prices produce one return."""
        prices = [100.0, 105.0]
        expected = [5.0]
        result = calculate_returns(prices)
        assert result == expected
    
    def test_zero_price(self):
        """Test that zero price is handled correctly."""
        prices = [100.0, 0.0, 50.0]
        result = calculate_returns(prices)
        assert result[0] == -100.0  # (0 - 100) / 100 * 100 = -100
        assert result[1] == float('inf')  # (50 - 0) / 0 * 100 = inf

class TestCalculateVolatility:
    """Tests for the calculate_volatility function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected volatility."""
        # Create a series with known volatility
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 1) for _ in range(30)]
        
        # Calculate volatility with default window
        volatility = calculate_volatility(prices)
        
        # Volatility should be positive
        assert volatility > 0
        
        # Calculate with custom window
        volatility_custom = calculate_volatility(prices, window=10)
        assert volatility_custom > 0
        assert volatility_custom != volatility  # Different windows should give different results
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return 0.0."""
        prices = [100.0, 105.0, 103.0, 107.0]
        assert calculate_volatility(prices, window=5) == 0.0
    
    def test_empty_list(self):
        """Test that empty list returns 0.0."""
        assert calculate_volatility([]) == 0.0
    
    def test_single_price(self):
        """Test that single price returns 0.0."""
        assert calculate_volatility([100.0]) == 0.0
    
    def test_constant_prices(self):
        """Test that constant prices return 0.0 volatility."""
        prices = [100.0] * 30
        assert calculate_volatility(prices) == 0.0

# Additional test classes for other math utility functions would go here 