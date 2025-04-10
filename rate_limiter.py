"""
Rate limiter implementation for API request throttling using the token bucket algorithm.
This module provides thread-safe rate limiting functionality for API requests.
"""

import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass
import logging
from decimal import Decimal, ROUND_DOWN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting parameters."""
    requests_per_second: float
    burst_size: int
    name: str

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if self.burst_size <= 0:
            raise ValueError("burst_size must be positive")
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.burst_size < self.requests_per_second:
            raise ValueError("burst_size must be greater than or equal to requests_per_second")

class RateLimiterError(Exception):
    """Base exception for rate limiter errors."""
    pass

class RateLimitExceededError(RateLimiterError):
    """Exception raised when rate limit is exceeded."""
    pass

class TokenBucket:
    """
    Thread-safe implementation of the token bucket algorithm for rate limiting.
    Uses Decimal for precise token calculations.
    """
    def __init__(self, rate: float, capacity: int):
        """
        Initialize the token bucket.
        
        Args:
            rate (float): Tokens added per second
            capacity (int): Maximum number of tokens the bucket can hold
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        if capacity < rate:
            raise ValueError("Capacity must be greater than or equal to rate")
            
        self.rate = Decimal(str(rate))
        self.capacity = Decimal(str(capacity))
        self.tokens = self.capacity  # Start with full capacity for burst
        self.last_update = Decimal(str(time.time()))
        self._lock = threading.Lock()

    def _add_tokens(self) -> None:
        """
        Add tokens based on elapsed time since last update.
        This method must be called with the lock held.
        """
        now = Decimal(str(time.time()))
        elapsed = now - self.last_update
        new_tokens = (elapsed * self.rate).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
        
        # Update tokens while respecting capacity limit
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens (int): Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed, False otherwise
        """
        if tokens <= 0:
            raise ValueError("Token count must be positive")
            
        with self._lock:
            # Update available tokens
            self._add_tokens()
            
            # Check if we have enough tokens
            token_count = Decimal(str(tokens))
            if token_count > self.tokens:
                return False
                
            # Consume tokens and update last update time
            self.tokens = (self.tokens - token_count).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
            return True

class RateLimiter:
    """
    Manages multiple rate limiters for different API endpoints or clients.
    Provides thread-safe operations for rate limit management.
    """
    def __init__(self):
        """Initialize the rate limiter with an empty dictionary of buckets."""
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        logger.info("Rate limiter initialized")

    def add_limiter(self, name: str, config: RateLimitConfig) -> None:
        """
        Add a new rate limiter configuration.
        
        Args:
            name (str): Identifier for the rate limiter
            config (RateLimitConfig): Rate limiting configuration
            
        Raises:
            RateLimiterError: If the limiter already exists
            ValueError: If the configuration is invalid
        """
        with self._lock:
            if name in self._buckets:
                raise RateLimiterError(f"Rate limiter '{name}' already exists")
            try:
                self._buckets[name] = TokenBucket(
                    rate=config.requests_per_second,
                    capacity=config.burst_size
                )
                logger.info(f"Added rate limiter '{name}' with {config.requests_per_second} req/s")
            except Exception as e:
                logger.error(f"Failed to add rate limiter '{name}': {str(e)}")
                raise

    def remove_limiter(self, name: str) -> None:
        """
        Remove a rate limiter configuration.
        
        Args:
            name (str): Identifier for the rate limiter to remove
            
        Raises:
            RateLimiterError: If the limiter doesn't exist
        """
        with self._lock:
            if name not in self._buckets:
                raise RateLimiterError(f"Rate limiter '{name}' does not exist")
            del self._buckets[name]
            logger.info(f"Removed rate limiter '{name}'")

    def acquire(self, name: str, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens from a specific rate limiter.
        
        Args:
            name (str): Identifier for the rate limiter
            tokens (int): Number of tokens to consume
            
        Returns:
            bool: True if tokens were acquired, False otherwise
            
        Raises:
            RateLimiterError: If the specified rate limiter doesn't exist
            ValueError: If tokens is not positive
        """
        if tokens <= 0:
            raise ValueError("Tokens must be positive")
            
        with self._lock:
            if name not in self._buckets:
                raise RateLimiterError(f"Rate limiter '{name}' does not exist")
            result = self._buckets[name].consume(tokens)
            if not result:
                logger.debug(f"Rate limit exceeded for '{name}'")
            return result

def test_rate_limiter() -> bool:
    """
    Test the rate limiter functionality.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Create rate limiter instance
        limiter = RateLimiter()
        
        # Test configuration validation
        try:
            RateLimitConfig(requests_per_second=0, burst_size=5, name="test")
            return False
        except ValueError:
            pass
            
        # Add test configuration
        config = RateLimitConfig(
            requests_per_second=2.0,
            burst_size=5,
            name="test"
        )
        limiter.add_limiter("test", config)
        
        # Test basic rate limiting
        assert limiter.acquire("test"), "Should allow first request"
        assert limiter.acquire("test"), "Should allow second request"
        
        # Test burst capacity
        for _ in range(3):
            assert limiter.acquire("test"), "Should allow burst requests"
            
        # Test rate limit exceeded
        assert not limiter.acquire("test"), "Should deny request when rate limit exceeded"
        
        # Test invalid limiter
        try:
            limiter.acquire("nonexistent")
            return False
        except RateLimiterError:
            pass
            
        # Test removing limiter
        limiter.remove_limiter("test")
        try:
            limiter.acquire("test")
            return False
        except RateLimiterError:
            pass
            
        # Test invalid token count
        try:
            limiter.acquire("test", tokens=0)
            return False
        except ValueError:
            pass
            
        return True
        
    except Exception as e:
        logger.error(f"Rate limiter test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests
    test_result = test_rate_limiter()
    print(f"Rate limiter tests {'passed' if test_result else 'failed'}") 