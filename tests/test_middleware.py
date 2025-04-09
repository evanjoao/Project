"""
Tests for the API middleware components.
"""

import pytest
import time
from typing import Tuple, Dict, Any, Optional, Generator, cast
from unittest.mock import patch, MagicMock
from ..middleware import APIMiddleware, AuthenticationError, RateLimitError

@pytest.fixture
def middleware() -> Generator[APIMiddleware, None, None]:
    """Fixture providing an APIMiddleware instance."""
    yield APIMiddleware()

def test_authenticate_no_token(middleware: APIMiddleware) -> None:
    """Test authentication with no token."""
    with pytest.raises(AuthenticationError, match="No authentication token provided"):
        middleware.authenticate()

def test_authenticate_invalid_token_format(middleware):
    """Test authentication with invalid token format."""
    with pytest.raises(AuthenticationError, match="Invalid token format"):
        middleware.authenticate("invalid_token")

def test_authenticate_valid_token(middleware):
    """Test authentication with valid token."""
    result = middleware.authenticate("Bearer test_token")
    assert result == {"username": "test_user"}

def test_rate_limit_basic(middleware):
    """Test basic rate limiting functionality."""
    key = "test_key"
    max_requests = 3
    window_seconds = 1
    
    # Make requests up to the limit
    for _ in range(max_requests):
        middleware.rate_limit(key, max_requests=max_requests, window_seconds=window_seconds)
    
    # Next request should fail
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        middleware.rate_limit(key, max_requests=max_requests, window_seconds=window_seconds)

def test_rate_limit_window_reset(middleware):
    """Test rate limit window reset."""
    key = "test_key"
    max_requests = 2
    window_seconds = 1
    
    # Make requests up to the limit
    for _ in range(max_requests):
        middleware.rate_limit(key, max_requests=max_requests, window_seconds=window_seconds)
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Should be able to make more requests
    middleware.rate_limit(key, max_requests=max_requests, window_seconds=window_seconds)

def test_log_request_decorator(middleware):
    """Test the log_request decorator."""
    @middleware.log_request
    def test_function() -> str:
        return "success"
    
    result = test_function()
    assert result == "success"

def test_log_request_decorator_with_error(middleware):
    """Test the log_request decorator with an error."""
    @middleware.log_request
    def test_function() -> None:
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        test_function()

def test_handle_errors_decorator_authentication_error(middleware):
    """Test the handle_errors decorator with AuthenticationError."""
    @middleware.handle_errors
    def test_function() -> Tuple[Dict[str, Any], int]:
        raise AuthenticationError("Auth failed")
    
    response, status_code = test_function()
    assert status_code == 401
    assert response["error"] == "Authentication failed"
    assert "Auth failed" in response["message"]

def test_handle_errors_decorator_rate_limit_error(middleware):
    """Test the handle_errors decorator with RateLimitError."""
    @middleware.handle_errors
    def test_function() -> Tuple[Dict[str, Any], int]:
        raise RateLimitError("Rate limit exceeded")
    
    response, status_code = test_function()
    assert status_code == 429
    assert response["error"] == "Rate limit exceeded"
    assert "Rate limit exceeded" in response["message"]

def test_handle_errors_decorator_general_error(middleware):
    """Test the handle_errors decorator with a general error."""
    @middleware.handle_errors
    def test_function() -> Tuple[Dict[str, Any], int]:
        raise ValueError("Test error")
    
    response, status_code = test_function()
    assert status_code == 500
    assert response["error"] == "Internal server error"
    assert "Test error" in response["message"]

def test_handle_errors_decorator_success(middleware):
    """Test the handle_errors decorator with successful execution."""
    @middleware.handle_errors
    def test_function() -> str:
        return "success"
    
    result = test_function()
    assert result == "success"

@pytest.mark.asyncio
async def test_middleware_combined_usage() -> None:
    """Test combined usage of middleware decorators."""
    middleware = APIMiddleware()
    
    @middleware.handle_errors
    @middleware.log_request
    def decorated_func() -> Any:
        middleware.rate_limit('test_key', max_requests=1, window_seconds=60)
        return "success"
    
    # First call should succeed
    result = decorated_func()
    assert result == "success"
    
    # Second call should return rate limit error response
    response, status_code = decorated_func()
    assert status_code == 429
    assert cast(Dict[str, str], response)["error"] == "Rate limit exceeded"
    assert "Rate limit exceeded for key: test_key" in cast(Dict[str, str], response)["message"] 