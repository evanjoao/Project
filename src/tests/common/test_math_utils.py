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


class TestCalculateSMA:
    """Tests for the calculate_sma function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected SMA values."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        period = 3
        expected = [11.0, 12.0, 13.0]
        result = calculate_sma(prices, period)
        
        # Check that results are close (floating point comparison)
        assert len(result) == len(expected)
        for i in range(len(result)):
            assert abs(result[i] - expected[i]) < 1e-10
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert calculate_sma([], 3) == []
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return empty list."""
        prices = [10.0, 11.0]
        assert calculate_sma(prices, 3) == []
    
    def test_period_one(self):
        """Test that period of 1 returns the same values."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = calculate_sma(prices, 1)
        assert result == prices


class TestCalculateEMA:
    """Tests for the calculate_ema function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected EMA values."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        period = 3
        result = calculate_ema(prices, period)
        
        # EMA values should be different from SMA values
        sma = calculate_sma(prices, period)
        assert result != sma
        
        # EMA should give more weight to recent prices
        assert result[-1] > sma[-1]  # Last EMA value should be higher than last SMA value
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert calculate_ema([], 3) == []
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return empty list."""
        prices = [10.0, 11.0]
        assert calculate_ema(prices, 3) == []
    
    def test_period_one(self):
        """Test that period of 1 returns the same values."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = calculate_ema(prices, 1)
        assert result == prices


class TestCalculateRSI:
    """Tests for the calculate_rsi function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected RSI values."""
        # Create a series with known trend
        prices = [10.0, 10.5, 11.0, 11.5, 12.0, 11.8, 11.5, 11.2, 11.0, 10.8, 10.5, 10.2, 10.0]
        period = 5
        result = calculate_rsi(prices, period)
        
        # RSI should be between 0 and 100
        assert all(0 <= rsi <= 100 for rsi in result)
        
        # First period values should be the same
        assert all(rsi == result[period] for rsi in result[:period])
        
        # RSI should be higher for uptrend and lower for downtrend
        uptrend_rsi = result[4]  # During uptrend
        downtrend_rsi = result[-1]  # During downtrend
        assert uptrend_rsi > downtrend_rsi
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert calculate_rsi([], 5) == []
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return empty list."""
        prices = [10.0, 11.0, 12.0, 13.0]
        assert calculate_rsi(prices, 5) == []
    
    def test_constant_prices(self):
        """Test that constant prices produce RSI of 50."""
        prices = [10.0] * 20
        result = calculate_rsi(prices, 5)
        assert all(abs(rsi - 50) < 1e-10 for rsi in result)


class TestCalculateBollingerBands:
    """Tests for the calculate_bollinger_bands function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected Bollinger Bands."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]
        period = 5
        std_dev = 2.0
        middle, upper, lower = calculate_bollinger_bands(prices, period, std_dev)
        
        # Check that middle band is the SMA
        sma = calculate_sma(prices, period)
        assert middle == sma
        
        # Check that upper band is above middle band
        assert all(u > m for u, m in zip(upper, middle))
        
        # Check that lower band is below middle band
        assert all(l < m for l, m in zip(lower, middle))
        
        # Check that bands have the same length
        assert len(middle) == len(upper) == len(lower)
    
    def test_empty_list(self):
        """Test that empty list returns empty lists."""
        middle, upper, lower = calculate_bollinger_bands([], 5)
        assert middle == upper == lower == []
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return empty lists."""
        prices = [10.0, 11.0, 12.0]
        middle, upper, lower = calculate_bollinger_bands(prices, 5)
        assert middle == upper == lower == []
    
    def test_different_std_dev(self):
        """Test that different std_dev values produce different bands."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]
        period = 5
        
        # Calculate bands with different std_dev values
        _, upper1, lower1 = calculate_bollinger_bands(prices, period, 1.0)
        _, upper2, lower2 = calculate_bollinger_bands(prices, period, 2.0)
        
        # Wider std_dev should produce wider bands
        assert all(u2 > u1 for u1, u2 in zip(upper1, upper2))
        assert all(l2 < l1 for l1, l2 in zip(lower1, lower2))


class TestCalculateATR:
    """Tests for the calculate_atr function."""
    
    def test_valid_prices(self):
        """Test that valid prices produce expected ATR values."""
        high = [10.0, 11.0, 12.0, 13.0, 14.0]
        low = [9.0, 10.0, 11.0, 12.0, 13.0]
        close = [9.5, 10.5, 11.5, 12.5, 13.5]
        period = 3
        result = calculate_atr(high, low, close, period)
        
        # ATR should be positive
        assert all(atr > 0 for atr in result)
        
        # ATR should have the same length as input
        assert len(result) == len(high)
    
    def test_empty_lists(self):
        """Test that empty lists return empty list."""
        assert calculate_atr([], [], [], 3) == []
    
    def test_insufficient_prices(self):
        """Test that insufficient prices return empty list."""
        high = [10.0, 11.0]
        low = [9.0, 10.0]
        close = [9.5, 10.5]
        assert calculate_atr(high, low, close, 3) == []
    
    def test_constant_prices(self):
        """Test that constant prices produce constant ATR."""
        high = [10.0] * 10
        low = [9.0] * 10
        close = [9.5] * 10
        result = calculate_atr(high, low, close, 3)
        
        # ATR should be constant after the first period
        assert all(abs(atr - result[2]) < 1e-10 for atr in result[2:])


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