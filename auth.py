"""
Authentication and authorization utilities.

This module provides authentication and authorization functionality for the API,
including token generation, password hashing, and user authentication.
"""

import hashlib
import hmac
import time
import base64
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt

# Load environment variables from .env file
load_dotenv()

# Configuration constants
SECRET_KEY = "@Elreyfriki007"  # In production, use environment variable
TOKEN_EXPIRE_MINUTES = 30
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")  # Replace with your actual JWT secret key
JWT_ALGORITHM = "HS256"  # Replace with your actual JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@dataclass
class BinanceCredentials:
    """Binance API credentials model."""
    api_key: str
    api_secret: str

@dataclass
class Token:
    """Token response model."""
    access_token: str
    token_type: str = "bearer"

@dataclass
class TokenData:
    """Token data model."""
    username: Optional[str] = None

def load_binance_credentials() -> BinanceCredentials:
    """Load Binance API credentials from environment variables."""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        raise ValueError("Binance API credentials not found")
        
    return BinanceCredentials(api_key=api_key, api_secret=api_secret)

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    try:
        return hashlib.sha256(password.encode()).hexdigest()
    except Exception as e:
        raise ValueError(f"Error hashing password: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to check against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return hmac.compare_digest(
            hash_password(plain_password),
            hashed_password
        )
    except Exception as e:
        raise ValueError(f"Error verifying password: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify a JWT token and return the token data."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise ValueError("Invalid token payload")
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            raise ValueError("Token has no expiration")
            
        if datetime.utcnow().timestamp() > exp:
            raise ValueError("Token has expired")
            
        return TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

def main() -> bool:
    """
    Test the authentication module functionality.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Test password hashing
        test_password = "test_password123"
        hashed = hash_password(test_password)
        assert verify_password(test_password, hashed), "Password verification failed"
        
        # Test token creation and verification
        test_data = {"sub": "test_user"}
        token = create_access_token(test_data)
        token_data = verify_token(token)
        assert token_data.username == "test_user", "Token verification failed"
        
        # Test Binance credentials loading
        credentials = load_binance_credentials()
        assert credentials.api_key and credentials.api_secret, "Binance credentials loading failed"
        
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Authentication module test {'passed' if success else 'failed'}") 