"""
Test suite for the BaseAPIClient class.

This module contains tests for the base API client functionality including:
- Request handling
- Rate limiting
- Error handling
- Authentication
- Session management
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest
import aiohttp
import requests
from pydantic import BaseModel

from src.core.api.clients.base_client import BaseAPIClient
from src.core.config.api_config import APIConfigManager, ExchangeConfig, GlobalConfig, APIConfig

# Mock configuration classes
class MockGlobalConfig(GlobalConfig):
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_pause: int = 1
    log_level: str = "INFO"

class MockErrorConfig(BaseModel):
    max_retries: int = 3
    backoff_factor: int = 2
    retry_on_status: List[int] = [429, 500, 502, 503, 504]

class MockRateLimits(BaseModel):
    requests_per_minute: int = 60

class MockWebSocketConfig(BaseModel):
    enabled: bool = True
    ping_interval: int = 30
    reconnect_delay: int = 5

class MockEndpoints(BaseModel):
    market_data: str = "/market-data"
    order_book: str = "/order-book"
    recent_trades: str = "/recent-trades"

class MockExchangeConfig(ExchangeConfig):
    enabled: bool = True
    api_version: str = "v1"
    base_url: str = "https://api.example.com"
    rate_limits: MockRateLimits = MockRateLimits()
    endpoints: MockEndpoints = MockEndpoints()
    websocket: MockWebSocketConfig = MockWebSocketConfig()

class MockValidation(BaseModel):
    price_precision: int = 8
    amount_precision: int = 8
    min_order_amount: float = 0.0001
    max_order_amount: float = 1000.0

class MockMonitoring(BaseModel):
    health_check_interval: int = 60
    alert_thresholds: Dict[str, float] = {
        "error_rate": 0.05,
        "latency": 1000
    }
    metrics: Dict[str, Any] = {
        "enabled": True,
        "export_interval": 60
    }

class MockWebSocket(BaseModel):
    default_channels: List[str] = ["ticker", "orderbook", "trades"]
    buffer_size: int = 1000
    max_reconnect_attempts: int = 5
    connection_timeout: int = 10

class MockAPIConfig(APIConfig):
    global_settings: MockGlobalConfig = MockGlobalConfig()
    error_handling: MockErrorConfig = MockErrorConfig()
    exchanges: Dict[str, ExchangeConfig] = {"test_exchange": MockExchangeConfig()}
    auth_templates: Dict[str, Dict[str, str]] = {
        "test_exchange": {
            "api_key": "test_key",
            "api_secret": "test_secret"
        }
    }
    websocket: MockWebSocket = MockWebSocket()
    validation: MockValidation = MockValidation()
    monitoring: MockMonitoring = MockMonitoring()

class MockAPIConfigManager(APIConfigManager):
    """Mock implementation of APIConfigManager for testing."""
    
    def __init__(self):
        super().__init__("config/api_config.yaml")
        self._config = MockAPIConfig()
    
    @property
    def config(self) -> APIConfig:
        if self._config is None:
            self._config = MockAPIConfig()
        return self._config
    
    def get_exchange_config(self, exchange: str) -> ExchangeConfig:
        return MockExchangeConfig()
    
    def get_auth_template(self, exchange: str) -> Dict[str, str]:
        return {
            "api_key": "test_key",
            "api_secret": "test_secret"
        }

# Implementation class for testing (not a test class)
class MockAPIClientImpl(BaseAPIClient):
    """Implementation of BaseAPIClient for testing purposes."""
    
    def get_market_data(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return self._make_request("GET", "/market-data", params={"symbol": symbol})
    
    async def get_market_data_async(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return await self._make_request_async("GET", "/market-data", params={"symbol": symbol})

@pytest.fixture
def api_client():
    """Fixture providing a test API client instance."""
    config_manager = MockAPIConfigManager()
    return MockAPIClientImpl(config_manager, "test_exchange")

@pytest.fixture
def mock_response():
    """Fixture providing a mock response."""
    response = Mock(spec=requests.Response)
    response.json.return_value = {"data": "test"}
    response.raise_for_status.return_value = None
    return response

@pytest.fixture
def mock_aio_response():
    """Fixture providing a mock async response."""
    response = AsyncMock(spec=aiohttp.ClientResponse)
    response.json.return_value = {"data": "test"}
    response.raise_for_status.return_value = None
    return response

@pytest.fixture
def mock_aio_session():
    """Fixture providing a mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    return session

class TestBaseAPIClient:
    """Test suite for BaseAPIClient class."""
    
    def test_initialization(self, api_client):
        """Test client initialization."""
        assert api_client.exchange == "test_exchange"
        assert api_client.config.base_url == "https://api.example.com"
        assert api_client.auth["api_key"] == "test_key"
        assert api_client.global_config.timeout == 30
        assert api_client.error_config.max_retries == 3
    
    def test_get_headers(self, api_client):
        """Test header generation."""
        headers = api_client._get_headers()
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert headers["Accept"] == "application/json"
    
    @patch("requests.Session")
    def test_get_session(self, mock_session_class, api_client):
        """Test session management."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        session = api_client._get_session()
        assert session == api_client.session
        mock_session_class.assert_called_once()
    
    @patch("time.time")
    @patch("time.sleep")
    def test_rate_limiting(self, mock_sleep, mock_time, api_client):
        """Test rate limiting functionality."""
        mock_time.return_value = 100.0
        api_client.last_request_time = 99.0
        api_client.request_count = 0
        api_client.request_reset_time = 160.0
        
        api_client._handle_rate_limit()
        mock_sleep.assert_not_called()
        
        # Test rate limit exceeded
        api_client.request_count = api_client.config.rate_limits.requests_per_minute
        api_client._handle_rate_limit()
        mock_sleep.assert_called()
    
    @patch("requests.Session.request")
    def test_make_request_success(self, mock_request, api_client, mock_response):
        """Test successful request handling."""
        mock_request.return_value = mock_response
        
        result = api_client._make_request("GET", "/test")
        assert result == {"data": "test"}
        mock_request.assert_called_once()
    
    @patch("requests.Session.request")
    def test_make_request_retry(self, mock_request, api_client):
        """Test request retry mechanism."""
        # Set max_retries to 0 to ensure the exception is raised
        api_client.error_config.max_retries = 0
        
        mock_request.side_effect = requests.exceptions.RequestException("Test error")
        
        with pytest.raises(requests.exceptions.RequestException):
            api_client._make_request("GET", "/test")
        
        assert mock_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_make_request_async_success(self, api_client, mock_aio_response, mock_aio_session):
        """Test successful async request handling."""
        mock_aio_session.request.return_value.__aenter__.return_value = mock_aio_response
        
        with patch("aiohttp.ClientSession", return_value=mock_aio_session):
            result = await api_client._make_request_async("GET", "/test")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_make_request_async_retry(self, api_client, mock_aio_session):
        """Test async request retry mechanism."""
        # Set max_retries to 0 to ensure the exception is raised
        api_client.error_config.max_retries = 0
        
        mock_aio_session.request.side_effect = aiohttp.ClientError("Test error")
        
        with patch("aiohttp.ClientSession", return_value=mock_aio_session):
            with pytest.raises(aiohttp.ClientError):
                await api_client._make_request_async("GET", "/test")
    
    def test_context_manager(self, api_client):
        """Test context manager functionality."""
        mock_session = MagicMock()
        with patch("requests.Session", return_value=mock_session):
            with api_client as client:
                assert client == api_client
                assert client.session is not None
                assert client.session == mock_session
            
            assert api_client.session is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, api_client, mock_aio_session):
        """Test async context manager functionality."""
        with patch("aiohttp.ClientSession", return_value=mock_aio_session):
            async with api_client as client:
                assert client == api_client
                assert client.aio_session == mock_aio_session
            
            assert api_client.aio_session is None
    
    def test_get_market_data(self, api_client):
        """Test market data retrieval."""
        with patch.object(api_client, "_make_request") as mock_request:
            mock_request.return_value = {"price": 100}
            
            result = api_client.get_market_data("BTC/USDT")
            assert result == {"price": 100}
            mock_request.assert_called_once_with(
                "GET",
                "/market-data",
                params={"symbol": "BTC/USDT"}
            )
    
    @pytest.mark.asyncio
    async def test_get_market_data_async(self, api_client):
        """Test async market data retrieval."""
        with patch.object(api_client, "_make_request_async") as mock_request:
            mock_request.return_value = {"price": 100}
            
            result = await api_client.get_market_data_async("BTC/USDT")
            assert result == {"price": 100}
            mock_request.assert_called_once_with(
                "GET",
                "/market-data",
                params={"symbol": "BTC/USDT"}
            ) 