"""
Base API Client Module

This module provides a base class for API clients with common functionality
such as request handling, rate limiting, and error handling.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Tuple

import aiohttp
import requests
from pydantic import BaseModel

from src.core.config.api_config import APIConfigManager, ExchangeConfig

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """
    Base class for API clients.
    
    This class provides common functionality for API clients such as:
    - Request handling with retries
    - Rate limiting
    - Error handling
    - Authentication
    """
    
    def __init__(self, config_manager: APIConfigManager, exchange: str):
        """
        Initialize the API client.
        
        Args:
            config_manager: The API configuration manager
            exchange: The exchange name (e.g., 'binance', 'fred')
        """
        self.config_manager = config_manager
        self.exchange = exchange
        self.config = config_manager.get_exchange_config(exchange)
        self.auth = config_manager.get_auth_template(exchange)
        self.global_config = config_manager.config.global_settings
        self.error_config = config_manager.config.error_handling
        
        # Initialize session
        self.session = None
        self.aio_session = None
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_reset_time = 0
        
        logger.info(f"Initialized {exchange} API client")
    
    def _get_session(self) -> requests.Session:
        """
        Get or create a requests session.
        
        Returns:
            requests.Session: The session
        """
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update(self._get_headers())
        return self.session
    
    async def _get_aio_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp session.
        
        Returns:
            aiohttp.ClientSession: The session
        """
        if self.aio_session is None:
            self.aio_session = aiohttp.ClientSession(headers=self._get_headers())
        return self.aio_session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests.
        
        Returns:
            Dict[str, str]: The headers
        """
        return {
            "User-Agent": "Crypto-Trading-Bot/1.0",
            "Accept": "application/json",
        }
    
    def _handle_rate_limit(self):
        """
        Handle rate limiting by waiting if necessary.
        """
        current_time = time.time()
        
        # Check if we need to reset the request count
        if current_time >= self.request_reset_time:
            self.request_count = 0
            self.request_reset_time = current_time + 60  # Reset every minute
        
        # Check if we've exceeded the rate limit
        if self.request_count >= self.config.rate_limits.requests_per_minute:
            wait_time = self.request_reset_time - current_time
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                self.request_count = 0
                self.request_reset_time = time.time() + 60
        
        # Ensure we're not making requests too quickly
        min_request_interval = 60 / self.config.rate_limits.requests_per_minute
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < min_request_interval:
            time.sleep(min_request_interval - time_since_last_request)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def _handle_rate_limit_async(self):
        """
        Handle rate limiting for async requests.
        """
        current_time = time.time()
        
        # Check if we need to reset the request count
        if current_time >= self.request_reset_time:
            self.request_count = 0
            self.request_reset_time = current_time + 60  # Reset every minute
        
        # Check if we've exceeded the rate limit
        if self.request_count >= self.config.rate_limits.requests_per_minute:
            wait_time = self.request_reset_time - current_time
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.request_reset_time = time.time() + 60
        
        # Ensure we're not making requests too quickly
        min_request_interval = 60 / self.config.rate_limits.requests_per_minute
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < min_request_interval:
            await asyncio.sleep(min_request_interval - time_since_last_request)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle the API response.
        
        Args:
            response: The response from the API
            
        Returns:
            Dict[str, Any]: The parsed response
            
        Raises:
            Exception: If the response indicates an error
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in self.error_config.retry_on_status:
                logger.warning(f"HTTP error {status_code}, will retry: {e}")
                raise  # Let the retry mechanism handle it
            else:
                logger.error(f"HTTP error {status_code}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            raise
    
    async def _handle_response_async(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Handle the async API response.
        
        Args:
            response: The response from the API
            
        Returns:
            Dict[str, Any]: The parsed response
            
        Raises:
            Exception: If the response indicates an error
        """
        try:
            response.raise_for_status()
            return await response.json()
        except aiohttp.ClientError as e:
            status_code = getattr(e, 'status', None)
            if status_code in self.error_config.retry_on_status:
                logger.warning(f"HTTP error {status_code}, will retry: {e}")
                raise  # Let the retry mechanism handle it
            else:
                logger.error(f"HTTP error {status_code}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            raise
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            method: The HTTP method (GET, POST, etc.)
            endpoint: The API endpoint
            params: Query parameters
            data: Request body data
            headers: Additional headers
            retries: Number of retries (defaults to config value)
            
        Returns:
            Dict[str, Any]: The API response
            
        Raises:
            Exception: If the request fails after all retries
        """
        if retries is None:
            retries = self.error_config.max_retries
        
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                self._handle_rate_limit()
                
                session = self._get_session()
                request_headers = self._get_headers()
                if headers:
                    request_headers.update(headers)
                
                # Convert timeout to tuple format (connect timeout, read timeout)
                timeout_tuple: Tuple[float, float] = (self.global_config.timeout, self.global_config.timeout)
                
                response = session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=timeout_tuple
                )
                
                return self._handle_response(response)
            
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Request failed after {retries} retries: {e}")
                    raise
                
                backoff_time = self.error_config.backoff_factor ** attempt
                logger.warning(f"Request failed, retrying in {backoff_time} seconds: {e}")
                time.sleep(backoff_time)
        
        # This should never be reached due to the raise in the loop,
        # but we need it to satisfy the type checker
        raise Exception("Request failed after all retries")
    
    async def _make_request_async(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an asynchronous request to the API.
        
        Args:
            method: The HTTP method (GET, POST, etc.)
            endpoint: The API endpoint
            params: Query parameters
            data: Request body data
            headers: Additional headers
            retries: Number of retries (defaults to config value)
            
        Returns:
            Dict[str, Any]: The API response
            
        Raises:
            Exception: If the request fails after all retries
        """
        if retries is None:
            retries = self.error_config.max_retries
        
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                await self._handle_rate_limit_async()
                
                session = await self._get_aio_session()
                request_headers = self._get_headers()
                if headers:
                    request_headers.update(headers)
                
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=float(self.global_config.timeout))
                ) as response:
                    return await self._handle_response_async(response)
            
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Request failed after {retries} retries: {e}")
                    raise
                
                backoff_time = self.error_config.backoff_factor ** attempt
                logger.warning(f"Request failed, retrying in {backoff_time} seconds: {e}")
                await asyncio.sleep(backoff_time)
        
        # This should never be reached due to the raise in the loop,
        # but we need it to satisfy the type checker
        raise Exception("Request failed after all retries")
    
    async def close(self):
        """Close any open sessions."""
        if self.session:
            self.session.close()
            self.session = None
        
        if self.aio_session:
            await self.aio_session.close()
            self.aio_session = None
    
    def __enter__(self):
        """Enter the context manager."""
        self.session = self._get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self.session:
            self.session.close()
            self.session = None
    
    async def __aenter__(self):
        """Enter the async context manager."""
        self.aio_session = await self._get_aio_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if self.aio_session:
            await self.aio_session.close()
            self.aio_session = None
    
    @abstractmethod
    def get_market_data(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: The market data
        """
        pass
    
    @abstractmethod
    async def get_market_data_async(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market data for a symbol asynchronously.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: The market data
        """
        pass 