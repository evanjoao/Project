"""
Tests for the rate limiter implementation.
"""

import pytest
import time
from typing import Any, cast
from ..rate_limiter import RateLimiter, RateLimitConfig, RateLimiterError

# Define the API limiter name as a constant
API_LIMITER_NAME = "api"

@pytest.fixture
def rate_limiter() -> Any:  # type: ignore[type-arg, type-var, specialization, misc]
    """Fixture providing a rate limiter instance for API request throttling.
    
    Returns:
        RateLimiter: A configured rate limiter instance with:
        - 10 requests per second (standard API rate limit)
        - Burst capacity of 20 requests (2x standard rate)
        - Named "api" limiter
    """
    limiter = RateLimiter()
    config = RateLimitConfig(
        requests_per_second=10.0,  # Standard API rate limit
        burst_size=20,            # Allow 2x burst for high-priority requests
        name=API_LIMITER_NAME     # Generic name for API rate limiting
    )
    limiter.add_limiter(API_LIMITER_NAME, config)
    return limiter

def test_rate_limiter_initialization(rate_limiter):
    """Test rate limiter initialization and configuration validation."""
    # Verify limiter instance and bucket existence
    limiter = cast(RateLimiter, rate_limiter)
    assert limiter is not None
    assert API_LIMITER_NAME in limiter._buckets
    
    # Validate bucket configuration
    api_bucket = limiter._buckets[API_LIMITER_NAME]
    expected_config = {
        "rate": 10.0,
        "capacity": 20,
        "tokens": 20
    }
    
    assert api_bucket.rate == expected_config["rate"]
    assert api_bucket.capacity == expected_config["capacity"] 
    assert api_bucket.tokens == expected_config["tokens"]

def test_rate_limiter_basic_operation(rate_limiter):
    """Test basic rate limiter operation with precise timing."""
    limiter = cast(RateLimiter, rate_limiter)
    # Test initial burst capacity
    assert limiter.acquire(API_LIMITER_NAME), "First request should be allowed"
    assert limiter.acquire(API_LIMITER_NAME), "Second request should be allowed"
    assert limiter.acquire(API_LIMITER_NAME), "Third request should be allowed"
    
    # Test token refill
    time.sleep(0.2)  # Wait for tokens to refill
    assert limiter.acquire(API_LIMITER_NAME), "Request after token refill should be allowed"
    assert limiter.acquire(API_LIMITER_NAME), "Second request after refill should be allowed"

def test_rate_limiter_burst_capacity(rate_limiter):
    """Test burst capacity handling with precise timing and token management."""
    limiter = cast(RateLimiter, rate_limiter)
    # Test initial burst capacity (20 tokens)
    for i in range(20):
        assert limiter.acquire(API_LIMITER_NAME), f"Request {i+1} should be allowed within burst capacity"
    
    # At this point we've consumed all tokens
    assert not limiter.acquire(API_LIMITER_NAME), "Request should be denied when burst capacity is exceeded"
    
    # Wait for tokens to refill (10 tokens/sec for 0.5 seconds = 5 tokens)
    time.sleep(0.5)
    
    # Should be able to consume the refilled tokens
    for i in range(5):
        assert limiter.acquire(API_LIMITER_NAME), f"Request {i+1} should be allowed after refill"
    
    # Should deny when tokens are exhausted again
    assert not limiter.acquire(API_LIMITER_NAME), "Request should be denied when tokens are exhausted"

def test_rate_limiter_invalid_limiter(rate_limiter):
    """Test handling of invalid limiter names."""
    limiter = cast(RateLimiter, rate_limiter)
    with pytest.raises(RateLimiterError) as exc_info:
        limiter.acquire("nonexistent")
        assert str(exc_info.value) == "Rate limiter 'nonexistent' does not exist"

def test_rate_limiter_removal(rate_limiter):
    """Test removing a rate limiter and verifying proper cleanup."""
    limiter = cast(RateLimiter, rate_limiter)
    # Verify limiter exists before removal
    assert API_LIMITER_NAME in limiter._buckets, "Rate limiter should exist before removal"
    
    # Remove the limiter
    limiter.remove_limiter(API_LIMITER_NAME)
    
    # Verify limiter was removed
    assert API_LIMITER_NAME not in limiter._buckets, "Rate limiter should be removed"
    
    # Verify attempts to use removed limiter raise appropriate error
    with pytest.raises(RateLimiterError) as exc_info:
        limiter.acquire(API_LIMITER_NAME)
    assert str(exc_info.value) == "Rate limiter 'api' does not exist"

def test_rate_limiter_duplicate_addition(rate_limiter):
    """Test that attempting to add a duplicate rate limiter raises an error."""
    limiter = cast(RateLimiter, rate_limiter)
    # Create initial rate limiter config
    initial_config = RateLimitConfig(
        requests_per_second=1.0,
        burst_size=3,
        name="test"
    )
    limiter.add_limiter("test", initial_config)

    # Attempt to add duplicate config with different parameters
    duplicate_config = RateLimitConfig(
        requests_per_second=2.0,  # Different rate
        burst_size=5,  # Different burst size
        name="test"  # Same name
    )
    
    with pytest.raises(RateLimiterError) as exc_info:
        limiter.add_limiter("test", duplicate_config)
    assert "already exists" in str(exc_info.value)

def test_rate_limiter_token_consumption(rate_limiter):
    """Test token consumption behavior with multiple tokens."""
    limiter = cast(RateLimiter, rate_limiter)
    # Initial state should allow consuming burst size tokens
    assert limiter.acquire(API_LIMITER_NAME, tokens=10), "Should allow consuming initial tokens"
    
    # Should have 10 tokens remaining (from 20 initial)
    assert limiter.acquire(API_LIMITER_NAME, tokens=5), "Should allow consuming more tokens"
    
    # Should have 5 tokens remaining, not enough for 10
    assert not limiter.acquire(API_LIMITER_NAME, tokens=10), "Should deny when insufficient tokens remain"
    
    # Wait for tokens to refill (10 tokens/sec for 0.3 seconds = 3 tokens)
    time.sleep(0.3)
    
    # Should now have 8 tokens (5 remaining + 3 refilled)
    assert limiter.acquire(API_LIMITER_NAME, tokens=5), "Should allow consuming partially refilled tokens"
    assert not limiter.acquire(API_LIMITER_NAME, tokens=5), "Should deny when remaining tokens are insufficient"
