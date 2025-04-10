"""Tests for the logging module."""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
import pytest
from src.common.logging import get_logger, setup_logger, temporary_log_level
from src.common.config import config

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

def test_get_logger_singleton():
    """Test that get_logger returns the same instance for the same name."""
    logger1 = get_logger("test")
    logger2 = get_logger("test")
    assert logger1 is logger2

def test_setup_logger_basic():
    """Test basic logger setup with console handler."""
    logger = setup_logger("test_basic")
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_setup_logger_with_file(temp_log_dir, monkeypatch):
    """Test logger setup with file handler."""
    # Patch the config to use our temp directory
    monkeypatch.setattr(config.logging, "log_dir", temp_log_dir)
    
    log_file = "test.log"
    logger = setup_logger("test_file", log_file=log_file)
    
    assert len(logger.handlers) == 2
    assert any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    assert (temp_log_dir / log_file).exists()

def test_setup_logger_invalid_level():
    """Test that invalid log levels raise ValueError."""
    with pytest.raises(ValueError):
        setup_logger("test_invalid", level=999)

def test_temporary_log_level():
    """Test the temporary log level context manager."""
    root_logger = logging.getLogger()
    original_level = root_logger.level
    
    with temporary_log_level(logging.DEBUG):
        assert root_logger.level == logging.DEBUG
    
    assert root_logger.level == original_level

def test_logger_handlers_clear():
    """Test that handlers are cleared before adding new ones."""
    logger = setup_logger("test_clear")
    initial_handler_count = len(logger.handlers)
    
    # Setup again
    logger = setup_logger("test_clear")
    assert len(logger.handlers) == initial_handler_count

def test_file_handler_error_handling(temp_log_dir, monkeypatch):
    """Test that file handler errors are caught and logged."""
    # Patch the config to use our temp directory
    monkeypatch.setattr(config.logging, "log_dir", temp_log_dir)
    
    # Make the directory read-only to force an error
    os.chmod(temp_log_dir, 0o444)
    
    logger = setup_logger("test_error", log_file="test.log")
    assert len(logger.handlers) == 1  # Only console handler
    assert isinstance(logger.handlers[0], logging.StreamHandler) 