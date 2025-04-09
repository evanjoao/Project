"""
Tests for the configuration module.
"""

import pytest
import json
from pathlib import Path
from ..config import Config, load_config, validate_config

@pytest.fixture
def valid_config_data():
    """Fixture providing valid configuration data."""
    return {
        "exchange": {
            "name": "binance",
            "api_key": "test_key",
            "api_secret": "test_secret",
            "testnet": True
        },
        "trading": {
            "base_currency": "USDT",
            "trading_pairs": ["BTC/USDT", "ETH/USDT"],
            "max_open_orders": 5
        },
        "risk_management": {
            "max_position_size": 1.0,
            "stop_loss_percentage": 2.0,
            "take_profit_percentage": 4.0
        }
    }

@pytest.fixture
def invalid_config_data():
    """Fixture providing invalid configuration data."""
    return {
        "exchange": {
            "name": "invalid_exchange",
            "api_key": "",
            "api_secret": ""
        }
    }

def test_load_config_valid_file(tmp_path, valid_config_data):
    """Test loading configuration from a valid file."""
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(valid_config_data, f)
    
    config = load_config(config_file)
    assert config == valid_config_data

def test_load_config_invalid_file(tmp_path):
    """Test loading configuration from an invalid file."""
    config_file = tmp_path / "config.json"
    config_file.write_text("invalid json")
    
    with pytest.raises(ValueError):
        load_config(config_file)

def test_validate_config_valid(valid_config_data):
    """Test validation of valid configuration."""
    result = validate_config(valid_config_data)
    assert result["success"] is True
    assert len(result["errors"]) == 0

def test_validate_config_invalid(invalid_config_data):
    """Test validation of invalid configuration."""
    result = validate_config(invalid_config_data)
    assert result["success"] is False
    assert len(result["errors"]) > 0

def test_config_class_initialization(valid_config_data):
    """Test Config class initialization."""
    config = Config(valid_config_data)
    assert config.exchange_name == "binance"
    assert config.api_key == "test_key"
    assert config.api_secret == "test_secret"
    assert config.testnet is True
    assert config.base_currency == "USDT"
    assert config.trading_pairs == ["BTC/USDT", "ETH/USDT"]
    assert config.max_open_orders == 5
    assert config.max_position_size == 1.0
    assert config.stop_loss_percentage == 2.0
    assert config.take_profit_percentage == 4.0

def test_config_class_validation():
    """Test Config class validation."""
    invalid_configs = [
        {"exchange": {}},  # Missing required fields
        {"exchange": {"name": "binance"}},  # Missing api credentials
        {"exchange": {"name": "invalid_exchange", "api_key": "key", "api_secret": "secret"}},  # Invalid exchange name
        {}  # Empty config
    ]
    
    for invalid_config in invalid_configs:
        with pytest.raises(ValueError):
            Config(invalid_config)
