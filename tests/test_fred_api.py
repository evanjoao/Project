"""
Tests for the FRED API client implementation.

This module contains tests for the FredAPI class, which provides a client for interacting
with the Federal Reserve Economic Data (FRED) API. The tests cover initialization,
authentication, rate limiting, and various API endpoints.
"""

import pytest
import json
import time
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock
from ..fred_api import FredAPI
from ..exceptions import APIError, AuthenticationError, RateLimitError, NetworkError, InvalidResponseError

# Sample test data
SAMPLE_SERIES_RESPONSE = {
    "realtime_start": "2023-01-01",
    "realtime_end": "2023-12-31",
    "observation_start": "2023-01-01",
    "observation_end": "2023-12-31",
    "units": "Billions of Dollars",
    "output_type": 4,
    "file_type": "json",
    "order_by": "observation_date",
    "sort_order": "asc",
    "count": 12,
    "offset": 0,
    "limit": 12,
    "observations": [
        {"realtime_start": "2023-01-01", "realtime_end": "2023-12-31", "date": "2023-01-01", "value": "25.0"},
        {"realtime_start": "2023-01-01", "realtime_end": "2023-12-31", "date": "2023-02-01", "value": "25.5"},
        {"realtime_start": "2023-01-01", "realtime_end": "2023-12-31", "date": "2023-03-01", "value": "26.0"}
    ]
}

SAMPLE_SEARCH_RESPONSE = {
    "seriess": [
        {
            "id": "GDP",
            "title": "Gross Domestic Product",
            "observation_start": "1947-01-01",
            "observation_end": "2023-01-01",
            "frequency": "Quarterly",
            "frequency_short": "Q",
            "units": "Billions of Dollars",
            "units_short": "Bil. of $",
            "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
            "seasonal_adjustment_short": "SAAR",
            "last_updated": "2023-04-27 07:45:00-05",
            "notes": "BEA Account Code: A191RC"
        }
    ]
}

SAMPLE_CATEGORIES_RESPONSE = {
    "categories": [
        {
            "id": 1,
            "name": "Money, Banking, & Finance",
            "parent_id": None
        }
    ]
}

SAMPLE_TAGS_RESPONSE = {
    "tags": [
        {
            "name": "gdp",
            "group_id": "macro",
            "notes": "Gross Domestic Product",
            "created": "2012-02-27 10:10:50-06",
            "popularity": 100,
            "series_count": 1000
        }
    ]
}

SAMPLE_SERIES_INFO_RESPONSE = {
    "seriess": [
        {
            "id": "GDP",
            "title": "Gross Domestic Product",
            "observation_start": "1947-01-01",
            "observation_end": "2023-01-01",
            "frequency": "Quarterly",
            "frequency_short": "Q",
            "units": "Billions of Dollars",
            "units_short": "Bil. of $",
            "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
            "seasonal_adjustment_short": "SAAR",
            "last_updated": "2023-04-27 07:45:00-05",
            "notes": "BEA Account Code: A191RC"
        }
    ]
}

@pytest.fixture
def mock_config():
    """Fixture providing a mocked config object."""
    with patch('src.api.fred_api.config') as mock:
        mock.settings.fred.api_key = "test_key"
        mock.settings.fred.base_url = "https://api.stlouisfed.org/fred"
        mock.settings.fred.version = "v1"
        mock.settings.fred.file_type = "json"
        mock.settings.request.timeout = 30
        yield mock

@pytest.fixture
def mock_session():
    """Fixture providing a mocked requests.Session object."""
    with patch('src.api.fred_api.requests.Session') as mock:
        session = MagicMock()
        mock.return_value = session
        yield session

@pytest.fixture
def fred_api(mock_config, mock_session):
    """Fixture providing a FredAPI instance with mocked dependencies."""
    api = FredAPI(api_key="test_key")
    return api

def test_initialization_with_api_key(mock_config, mock_session):
    """Test initialization with an API key."""
    api = FredAPI(api_key="test_key")
    assert api.api_key == "test_key"
    assert api._request_count == 0
    assert api._last_request_time == 0
    assert api._rate_limit_window == 60
    assert api._max_requests_per_window == 120

def test_initialization_without_api_key(mock_config, mock_session):
    """Test initialization without an API key (should use config)."""
    mock_config.settings.fred.api_key = "config_key"
    api = FredAPI()
    assert api.api_key == "config_key"

def test_initialization_without_api_key_failure(mock_config, mock_session):
    """Test initialization without an API key when config has none (should fail)."""
    mock_config.settings.fred.api_key = ""
    with pytest.raises(ValueError, match="FRED API key is required"):
        FredAPI()

def test_build_url(fred_api):
    """Test building the URL for an API endpoint."""
    url = fred_api._build_url("series/observations")
    assert url == "https://api.stlouisfed.org/fred/api/v1/series/observations"

def test_check_rate_limit_no_wait(fred_api):
    """Test rate limit check when under the limit."""
    # Set up a scenario where we're under the rate limit
    fred_api._request_count = 50
    fred_api._last_request_time = time.time() - 30  # 30 seconds ago
    
    # This should not raise an exception
    fred_api._check_rate_limit()
    
    # Counter should not be reset
    assert fred_api._request_count == 50

def test_check_rate_limit_reset_counter(fred_api):
    """Test rate limit check when outside the window (should reset counter)."""
    # Set up a scenario where we're outside the rate limit window
    fred_api._request_count = 100
    fred_api._last_request_time = time.time() - 70  # 70 seconds ago
    
    # This should reset the counter
    fred_api._check_rate_limit()
    
    # Counter should be reset
    assert fred_api._request_count == 0

def test_check_rate_limit_wait(fred_api):
    """Test rate limit check when at the limit (should wait)."""
    # Set up a scenario where we're at the rate limit
    fred_api._request_count = 120
    fred_api._last_request_time = time.time() - 30  # 30 seconds ago
    
    # Mock time.sleep to avoid actually waiting
    with patch('time.sleep') as mock_sleep:
        fred_api._check_rate_limit()
        
        # Should have slept for approximately 30 seconds
        mock_sleep.assert_called_once()
        assert 29 <= mock_sleep.call_args[0][0] <= 31
        
        # Counter should be reset
        assert fred_api._request_count == 0

def test_request_success(mock_session, fred_api):
    """Test successful API request."""
    # Set up mock response
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_SERIES_RESPONSE
    mock_response.status_code = 200
    mock_session.request.return_value = mock_response

    response = fred_api._request("GET", "series/observations", {"series_id": "GDP"})

    assert response == SAMPLE_SERIES_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/observations",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_request_authentication_error(fred_api, mock_session):
    """Test API request with authentication error."""
    # Set up mock response with 401 status
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=401)
    )
    mock_session.request.return_value = mock_response
    
    # Make the request and check for the expected exception
    with pytest.raises(AuthenticationError, match="Invalid API key"):
        fred_api._request("GET", "series/observations", {"series_id": "GDP"})

def test_request_rate_limit_error(fred_api, mock_session):
    """Test API request with rate limit error."""
    # Set up mock response with 429 status
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=429)
    )
    mock_session.request.return_value = mock_response
    
    # Make the request and check for the expected exception
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        fred_api._request("GET", "series/observations", {"series_id": "GDP"})

def test_request_network_error(fred_api, mock_session):
    """Test API request with network error."""
    # Set up mock response with connection error
    mock_session.request.side_effect = requests.exceptions.ConnectionError()
    
    # Make the request and check for the expected exception
    with pytest.raises(NetworkError, match="Connection error while requesting series/observations"):
        fred_api._request("GET", "series/observations", {"series_id": "GDP"})

def test_request_timeout_error(fred_api, mock_session):
    """Test API request with timeout error."""
    # Set up mock response with timeout error
    mock_session.request.side_effect = requests.exceptions.Timeout()
    
    # Make the request and check for the expected exception
    with pytest.raises(NetworkError, match="Request to series/observations timed out"):
        fred_api._request("GET", "series/observations", {"series_id": "GDP"})

def test_request_invalid_json(fred_api, mock_session):
    """Test API request with invalid JSON response."""
    # Set up mock response with invalid JSON
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_session.request.return_value = mock_response
    
    # Make the request and check for the expected exception
    with pytest.raises(InvalidResponseError, match="Invalid JSON response"):
        fred_api._request("GET", "series/observations", {"series_id": "GDP"})

def test_get_series(mock_session, fred_api):
    """Test getting a series."""
    mock_session.request.return_value.json.return_value = SAMPLE_SERIES_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series("GDP")

    assert response == SAMPLE_SERIES_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/observations",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP",
            "sort_order": "asc",
            "output_type": 4
        },
        timeout=30
    )

def test_get_series_with_optional_params(mock_session, fred_api):
    """Test getting a series with optional parameters."""
    mock_session.request.return_value.json.return_value = SAMPLE_SERIES_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series(
        "GDP",
        observation_start="2020-01-01",
        observation_end="2020-12-31",
        frequency="monthly",
        aggregation_method="avg"
    )

    assert response == SAMPLE_SERIES_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/observations",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP",
            "observation_start": "2020-01-01",
            "observation_end": "2020-12-31",
            "frequency": "monthly",
            "aggregation_method": "avg",
            "sort_order": "asc",
            "output_type": 4
        },
        timeout=30
    )

def test_search_series(mock_session, fred_api):
    """Test searching for series."""
    mock_session.request.return_value.json.return_value = SAMPLE_SEARCH_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.search_series("gdp")

    assert response == SAMPLE_SEARCH_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/search",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "search_text": "gdp",
            "order_by": "search_rank",
            "sort_order": "desc"
        },
        timeout=30
    )

def test_search_series_with_optional_params(mock_session, fred_api):
    """Test searching for series with optional parameters."""
    mock_session.request.return_value.json.return_value = SAMPLE_SEARCH_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.search_series(
        "GDP",
        limit=10,
        order_by="popularity",
        sort_order="desc",
        filter_variable="frequency",
        filter_value="Monthly"
    )

    assert response == SAMPLE_SEARCH_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/search",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "search_text": "GDP",
            "limit": "10",
            "order_by": "popularity",
            "sort_order": "desc",
            "filter_variable": "frequency",
            "filter_value": "Monthly"
        },
        timeout=30
    )

def test_get_series_categories(mock_session, fred_api):
    """Test getting series categories."""
    mock_session.request.return_value.json.return_value = SAMPLE_CATEGORIES_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_categories("GDP")

    assert response == SAMPLE_CATEGORIES_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/categories",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_tags(mock_session, fred_api):
    """Test getting series tags."""
    mock_session.request.return_value.json.return_value = SAMPLE_TAGS_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_tags("GDP")

    assert response == SAMPLE_TAGS_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/tags",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP",
            "order_by": "series_count",
            "sort_order": "desc"
        },
        timeout=30
    )

def test_get_series_tags_with_optional_params(mock_session, fred_api):
    """Test getting series tags with optional parameters."""
    mock_session.request.return_value.json.return_value = SAMPLE_TAGS_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_tags(
        "GDP",
        order_by="popularity",
        sort_order="desc"
    )

    assert response == SAMPLE_TAGS_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/tags",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP",
            "order_by": "popularity",
            "sort_order": "desc"
        },
        timeout=30
    )

def test_get_series_info(mock_session, fred_api):
    """Test getting series info."""
    mock_session.request.return_value.json.return_value = SAMPLE_SERIES_INFO_RESPONSE
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_info("GDP")

    assert response == SAMPLE_SERIES_INFO_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_vintagedates(mock_session, fred_api):
    """Test getting series vintage dates."""
    mock_session.request.return_value.json.return_value = {"vintage_dates": ["2020-01-01"]}
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_vintagedates("GDP")

    assert response == {"vintage_dates": ["2020-01-01"]}
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/vintagedates",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_releases(mock_session, fred_api):
    """Test getting series releases."""
    mock_session.request.return_value.json.return_value = {"releases": []}
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_releases("GDP")

    assert response == {"releases": []}
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/releases",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_sources(mock_session, fred_api):
    """Test getting series sources."""
    mock_session.request.return_value.json.return_value = {"sources": []}
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_sources("GDP")

    assert response == {"sources": []}
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/sources",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_updates(mock_session, fred_api):
    """Test getting series updates."""
    mock_session.request.return_value.json.return_value = {"updates": []}
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_updates("GDP")

    assert response == {"updates": []}
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/updates",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP"
        },
        timeout=30
    )

def test_get_series_updates_with_optional_params(mock_session, fred_api):
    """Test getting series updates with optional parameters."""
    mock_session.request.return_value.json.return_value = {"updates": []}
    mock_session.request.return_value.status_code = 200

    response = fred_api.get_series_updates(
        "GDP",
        realtime_start="2020-01-01",
        realtime_end="2020-12-31"
    )

    assert response == {"updates": []}
    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://api.stlouisfed.org/fred/api/v1/series/updates",
        params={
            "api_key": "test_key",
            "file_type": "json",
            "series_id": "GDP",
            "realtime_start": "2020-01-01",
            "realtime_end": "2020-12-31"
        },
        timeout=30
    ) 