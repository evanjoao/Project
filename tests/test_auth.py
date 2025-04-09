"""
Tests for the authentication module.
"""

import pytest
import os
from datetime import timedelta, datetime
from unittest.mock import patch, mock_open
from ..auth import (
    BinanceCredentials,
    Token,
    TokenData,
    load_binance_credentials,
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_api_key',
        'BINANCE_API_SECRET': 'test_api_secret'
    }):
        yield

def test_load_binance_credentials(mock_env_vars):
    """Test loading Binance credentials from environment variables."""
    credentials = load_binance_credentials()
    assert isinstance(credentials, BinanceCredentials)
    assert credentials.api_key == 'test_api_key'
    assert credentials.api_secret == 'test_api_secret'

def test_load_binance_credentials_missing():
    """Test loading Binance credentials when environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Binance API credentials not found"):
            load_binance_credentials()

def test_hash_password():
    """Test password hashing functionality."""
    password = "test_password123"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 produces 64 character hex string
    assert hashed != password

def test_verify_password():
    """Test password verification functionality."""
    password = "test_password123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_access_token():
    """Test access token creation."""
    data = {"sub": "test_user"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert "." in token  # Token should have two parts separated by a dot
    
    # Test with custom expiration
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)

def test_verify_token():
    """Test token verification."""
    with patch('src.api.auth.jwt.decode') as mock_decode:
        # Mock the JWT decode to return a valid payload
        mock_decode.return_value = {
            "sub": "test_user",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        
        data = {"sub": "test_user"}
        token = create_access_token(
            data=data,
            expires_delta=timedelta(hours=1)
        )
        
        # Verify token immediately
        token_data = verify_token(token)
        assert isinstance(token_data, TokenData)
        assert token_data.username == "test_user"

def test_verify_token_invalid():
    """Test verification of invalid tokens."""
    with pytest.raises(ValueError):
        verify_token("invalid.token.format")
    
    with pytest.raises(ValueError):
        verify_token("invalid.signature")

def test_verify_token_expired():
    """Test verification of expired tokens."""
    data = {"sub": "test_user"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))  # Expired token
    with pytest.raises(ValueError, match="Token has expired"):
        verify_token(token)

def test_token_data_model():
    """Test TokenData model."""
    token_data = TokenData(username="test_user")
    assert token_data.username == "test_user"
    
    token_data = TokenData()  # Test with no username
    assert token_data.username is None

def test_token_model():
    """Test Token model."""
    token = Token(access_token="test_token")
    assert token.access_token == "test_token"
    assert token.token_type == "bearer"
    
    token = Token(access_token="test_token", token_type="custom")
    assert token.token_type == "custom" 