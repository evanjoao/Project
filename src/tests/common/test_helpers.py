"""
Tests for the helpers module.

This module contains tests to verify that all helper functions work correctly
and handle edge cases appropriately.
"""

import pytest
import json
from datetime import datetime, timezone
from src.common.helpers import (
    safe_json_loads,
    calculate_position_size,
)

class TestSafeJsonLoads:
    """Tests for the safe_json_loads function."""
    
    def test_valid_json(self):
        """Test that valid JSON is parsed correctly."""
        test_data = '{"key": "value", "number": 42}'
        result = safe_json_loads(test_data)
        assert result == {"key": "value", "number": 42}
    
    def test_invalid_json(self):
        """Test that invalid JSON returns an empty dict."""
        test_data = '{"key": "value", "number": 42'  # Missing closing brace
        result = safe_json_loads(test_data)
        assert result == {}
    
    def test_empty_string(self):
        """Test that empty string returns an empty dict."""
        result = safe_json_loads("")
        assert result == {}
    
    def test_non_string_input(self):
        """Test that non-string input returns an empty dict."""
        result = safe_json_loads(123)
        assert result == {}

class TestCalculatePositionSize:
    """Tests for the calculate_position_size function."""
    
    def test_valid_inputs(self):
        """Test that valid inputs produce expected results."""
        portfolio_value = 10000.0
        risk_per_trade = 1.0  # 1%
        stop_loss_percentage = 2.0  # 2%
        
        position_size = calculate_position_size(
            portfolio_value, risk_per_trade, stop_loss_percentage
        )
        
        # Expected: (10000 * 0.01) / 0.02 = 5000
        assert position_size == 5000.0
    
    def test_zero_stop_loss(self):
        """Test that zero stop loss raises ValueError."""
        with pytest.raises(ZeroDivisionError):
            calculate_position_size(10000.0, 1.0, 0.0)
    
    def test_negative_values(self):
        """Test that negative values produce expected results."""
        portfolio_value = 10000.0
        risk_per_trade = 1.0
        stop_loss_percentage = -2.0
        
        position_size = calculate_position_size(
            portfolio_value, risk_per_trade, stop_loss_percentage
        )
        
        # Expected: (10000 * 0.01) / 0.02 = 5000 (absolute value of stop loss is used)
        assert position_size == 5000.0
    
    def test_zero_portfolio(self):
        """Test that zero portfolio value returns zero position size."""
        position_size = calculate_position_size(0.0, 1.0, 2.0)
        assert position_size == 0.0
    
    def test_zero_risk(self):
        """Test that zero risk returns zero position size."""
        position_size = calculate_position_size(10000.0, 0.0, 2.0)
        assert position_size == 0.0 