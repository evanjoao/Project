"""
Tests for the validators module.

This module contains tests to verify that all validation functions work correctly
and handle edge cases appropriately.
"""

import pytest
from src.common.validators import (
    validate_symbol,
    validate_price,
    validate_amount,
    validate_timeframe,
    validate_order_type,
    validate_order_side,
)
from src.common.exceptions import ValidationError

class TestValidateTimeframe:
    """Tests for the validate_timeframe function."""
    
    def test_valid_timeframes(self):
        """Test that valid timeframes pass validation."""
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        for timeframe in valid_timeframes:
            assert validate_timeframe(timeframe) is True
    
    def test_non_standard_timeframes(self):
        """Test that non-standard but valid timeframes pass validation with a warning."""
        non_standard = ['2m', '10m', '2h', '2d']
        for timeframe in non_standard:
            assert validate_timeframe(timeframe) is True
    
    def test_invalid_unit(self):
        """Test that timeframes with invalid units raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe('1x')
        assert "Invalid timeframe unit" in str(excinfo.value)
    
    def test_invalid_value(self):
        """Test that timeframes with invalid values raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe('0m')
        assert "Timeframe value must be positive" in str(excinfo.value)
    
    def test_non_numeric_value(self):
        """Test that timeframes with non-numeric values raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe('am')
        assert "Timeframe must start with a number" in str(excinfo.value)
    
    def test_empty_string(self):
        """Test that empty strings raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe('')
        assert "Timeframe must be at least 2 characters" in str(excinfo.value)
    
    def test_single_character(self):
        """Test that single character strings raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe('m')
        assert "Timeframe must be at least 2 characters" in str(excinfo.value)
    
    def test_non_string_input(self):
        """Test that non-string inputs raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            validate_timeframe(1)  # Using integer instead of string
        assert "Timeframe must be a string" in str(excinfo.value)

# Additional test classes for other validator functions would go here 