"""
FRED API Client Implementation

This module provides a client for interacting with the Federal Reserve Economic Data (FRED) API.
It handles authentication, rate limiting, and provides methods for accessing economic data.
The client is designed to be used alongside the Binance API client in the same project.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from . import config
from .exceptions import APIError, AuthenticationError, RateLimitError, NetworkError, InvalidResponseError
from .utils import format_number

# Configure logger
logger = logging.getLogger(__name__)

class FredAPI:
    """
    Client for interacting with the FRED API.
    
    This class provides methods to access economic data from the Federal Reserve Economic Data (FRED) API.
    It handles authentication, rate limiting, and provides a clean interface for accessing FRED data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the FRED API client.
        
        Args:
            api_key: Optional API key. If not provided, will use the one from config.
        """
        self.config = config.settings.fred
        self.api_key = api_key or self.config.api_key
        if not self.api_key:
            raise ValueError("FRED API key is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Rate limiting tracking
        self._request_count = 0
        self._last_request_time = 0
        self._rate_limit_window = 60  # 60 seconds window
        self._max_requests_per_window = 120  # FRED's default rate limit
        
        logger.info("FRED API client initialized")
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build the full URL for an API endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL for the API endpoint
        """
        return f"{self.config.base_url}/api/{self.config.version}/{endpoint}"
    
    def _check_rate_limit(self) -> None:
        """
        Check if the rate limit has been reached and wait if necessary.
        
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Reset counter if we're outside the window
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we've hit the rate limit
        if self._request_count >= self._max_requests_per_window:
            # Calculate time to wait
            wait_time = self._rate_limit_window - (current_time - self._last_request_time)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                # Reset counter after waiting
                self._request_count = 0
                self._last_request_time = time.time()
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the FRED API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Optional query parameters
            
        Returns:
            Dict containing the API response
            
        Raises:
            APIError: If the API request fails
            RateLimitError: If rate limit is exceeded
            NetworkError: If there's a network issue
            InvalidResponseError: If the response is invalid
        """
        # Check rate limit before making the request
        self._check_rate_limit()
        
        url = self._build_url(endpoint)
        
        # Add API key to parameters
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        params["file_type"] = self.config.file_type
        
        try:
            logger.debug(f"Making {method} request to {endpoint} with params: {params}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=config.settings.request.timeout
            )
            
            # Update rate limit tracking
            self._request_count += 1
            self._last_request_time = time.time()
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise InvalidResponseError(f"Invalid JSON response: {str(e)}")
                
        except Timeout:
            logger.error(f"Request to {endpoint} timed out")
            raise NetworkError(f"Request to {endpoint} timed out")
        except ConnectionError:
            logger.error(f"Connection error while requesting {endpoint}")
            raise NetworkError(f"Connection error while requesting {endpoint}")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                logger.error("Authentication failed")
                raise AuthenticationError("Invalid API key")
            elif status_code == 429:
                logger.error("Rate limit exceeded")
                raise RateLimitError("Rate limit exceeded")
            else:
                logger.error(f"HTTP error {status_code}: {e}")
                raise APIError(f"HTTP error {status_code}: {str(e)}")
        except RequestException as e:
            logger.error(f"Request error: {e}")
            raise APIError(f"Request error: {str(e)}")
    
    def get_series(self, series_id: str, 
                  realtime_start: Optional[Union[str, datetime]] = None,
                  realtime_end: Optional[Union[str, datetime]] = None,
                  limit: Optional[int] = None,
                  offset: Optional[int] = None,
                  sort_order: str = "asc",
                  observation_start: Optional[Union[str, datetime]] = None,
                  observation_end: Optional[Union[str, datetime]] = None,
                  units: Optional[str] = None,
                  frequency: Optional[str] = None,
                  aggregation_method: Optional[str] = None,
                  output_type: int = 4) -> Dict[str, Any]:
        """
        Get observations for a series.
        
        Args:
            series_id: The ID for a series
            realtime_start: Start date for real-time period
            realtime_end: End date for real-time period
            limit: Maximum number of results to return
            offset: Result offset
            sort_order: Sort order of results ('asc' or 'desc')
            observation_start: Start date for observations
            observation_end: End date for observations
            units: Units of measurement
            frequency: Frequency of aggregation
            aggregation_method: Method of aggregation
            output_type: Type of output (1=observations by real-time period, 2=observations by observation period, 3=observations by real-time period, 4=observations by observation period)
            
        Returns:
            Dict containing the series data
        """
        params = {
            "series_id": series_id,
            "sort_order": sort_order,
            "output_type": output_type
        }
        
        # Add optional parameters if provided
        if realtime_start:
            params["realtime_start"] = str(realtime_start)
        if realtime_end:
            params["realtime_end"] = str(realtime_end)
        if limit:
            params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        if units:
            params["units"] = units
        if frequency:
            params["frequency"] = frequency
        if aggregation_method:
            params["aggregation_method"] = aggregation_method
        
        return self._request("GET", "series/observations", params)
    
    def search_series(self, search_text: str,
                     limit: Optional[int] = None,
                     offset: Optional[int] = None,
                     order_by: str = "search_rank",
                     sort_order: str = "desc",
                     filter_value: Optional[str] = None,
                     filter_variable: Optional[str] = None,
                     tag_names: Optional[List[str]] = None,
                     exclude_tag_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for FRED series.
        
        Args:
            search_text: The words to match against economic data series
            limit: Maximum number of results to return
            offset: Result offset
            order_by: Order results by field
            sort_order: Sort order of results ('asc' or 'desc')
            filter_value: Filter results by value
            filter_variable: Filter results by variable
            tag_names: List of tag names to filter by
            exclude_tag_names: List of tag names to exclude
            
        Returns:
            Dict containing the search results
        """
        params = {
            "search_text": search_text,
            "order_by": order_by,
            "sort_order": sort_order
        }
        
        # Add optional parameters if provided
        if limit:
            params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)
        if filter_value:
            params["filter_value"] = filter_value
        if filter_variable:
            params["filter_variable"] = filter_variable
        if tag_names:
            params["tag_names"] = ",".join(tag_names)
        if exclude_tag_names:
            params["exclude_tag_names"] = ",".join(exclude_tag_names)
        
        return self._request("GET", "series/search", params)
    
    def get_series_categories(self, series_id: str) -> Dict[str, Any]:
        """
        Get the categories for a series.
        
        Args:
            series_id: The ID for a series
            
        Returns:
            Dict containing the categories
        """
        params = {"series_id": series_id}
        return self._request("GET", "series/categories", params)
    
    def get_series_tags(self, series_id: str,
                       limit: Optional[int] = None,
                       offset: Optional[int] = None,
                       order_by: str = "series_count",
                       sort_order: str = "desc") -> Dict[str, Any]:
        """
        Get the tags for a series.
        
        Args:
            series_id: The ID for a series
            limit: Maximum number of results to return
            offset: Result offset
            order_by: Order results by field
            sort_order: Sort order of results ('asc' or 'desc')
            
        Returns:
            Dict containing the tags
        """
        params = {
            "series_id": series_id,
            "order_by": order_by,
            "sort_order": sort_order
        }
        
        if limit:
            params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)
        
        return self._request("GET", "series/tags", params)
    
    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a series.
        
        Args:
            series_id: The ID for a series
            
        Returns:
            Dict containing the series information
        """
        params = {"series_id": series_id}
        return self._request("GET", "series", params)
    
    def get_series_vintagedates(self, series_id: str) -> Dict[str, Any]:
        """
        Get the vintage dates for a series.
        
        Args:
            series_id: The ID for a series
            
        Returns:
            Dict containing the vintage dates
        """
        params = {"series_id": series_id}
        return self._request("GET", "series/vintagedates", params)
    
    def get_series_releases(self, series_id: str) -> Dict[str, Any]:
        """
        Get the releases for a series.
        
        Args:
            series_id: The ID for a series
            
        Returns:
            Dict containing the releases
        """
        params = {"series_id": series_id}
        return self._request("GET", "series/releases", params)
    
    def get_series_sources(self, series_id: str) -> Dict[str, Any]:
        """
        Get the sources for a series.
        
        Args:
            series_id: The ID for a series
            
        Returns:
            Dict containing the sources
        """
        params = {"series_id": series_id}
        return self._request("GET", "series/sources", params)
    
    def get_series_updates(self, series_id: str,
                          realtime_start: Optional[Union[str, datetime]] = None,
                          realtime_end: Optional[Union[str, datetime]] = None) -> Dict[str, Any]:
        """
        Get the updates for a series.
        
        Args:
            series_id: The ID for a series
            realtime_start: Start date for real-time period
            realtime_end: End date for real-time period
            
        Returns:
            Dict containing the updates
        """
        params = {"series_id": series_id}
        
        if realtime_start:
            params["realtime_start"] = str(realtime_start)
        if realtime_end:
            params["realtime_end"] = str(realtime_end)
        
        return self._request("GET", "series/updates", params)


def run_tests() -> bool:
    """
    Run a suite of tests to verify the FRED API client functionality.
    
    This function performs a series of tests to ensure that the FRED API client
    works correctly. It tests initialization, error handling, and basic API calls.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    logger.info("Starting FRED API tests")
    all_tests_passed = True
    
    try:
        # Test 1: Initialization with API key
        try:
            fred = FredAPI(api_key="test_key")
            logger.info("Test 1 PASSED: Initialization with API key")
        except Exception as e:
            logger.error(f"Test 1 FAILED: Initialization with API key - {e}")
            all_tests_passed = False
        
        # Test 2: Initialization without API key (should fail)
        try:
            # Temporarily save the original API key
            original_api_key = config.settings.fred.api_key
            # Set API key to empty string
            config.settings.fred.api_key = ""
            
            fred = FredAPI()
            logger.error("Test 2 FAILED: Initialization without API key should have failed")
            all_tests_passed = False
        except ValueError:
            logger.info("Test 2 PASSED: Initialization without API key correctly failed")
        finally:
            # Restore the original API key
            config.settings.fred.api_key = original_api_key
        
        # Test 3: Mock API request
        try:
            # Create a mock response
            mock_response = {
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
            
            # Mock the _request method
            original_request = FredAPI._request
            
            def mock_request(self, method, endpoint, params=None):
                if endpoint == "series/observations" and params and params.get("series_id") == "GDP":
                    return mock_response
                raise APIError("Mock error for non-GDP series")
            
            FredAPI._request = mock_request
            
            # Test with a valid series ID
            fred = FredAPI(api_key="test_key")
            result = fred.get_series("GDP")
            
            if result == mock_response:
                logger.info("Test 3 PASSED: Mock API request")
            else:
                logger.error("Test 3 FAILED: Mock API request returned unexpected result")
                all_tests_passed = False
            
            # Test with an invalid series ID
            try:
                fred.get_series("INVALID")
                logger.error("Test 3 FAILED: Request with invalid series ID should have failed")
                all_tests_passed = False
            except APIError:
                logger.info("Test 3 PASSED: Request with invalid series ID correctly failed")
            
            # Restore the original _request method
            FredAPI._request = original_request
            
        except Exception as e:
            logger.error(f"Test 3 FAILED: Mock API request - {e}")
            all_tests_passed = False
    
    except Exception as e:
        logger.error(f"Test suite failed with unexpected error: {e}")
        all_tests_passed = False
    
    logger.info(f"FRED API tests completed. All tests passed: {all_tests_passed}")
    return all_tests_passed


if __name__ == "__main__":
    # Configure logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the tests
    test_result = run_tests()
    
    # Exit with appropriate status code
    import sys
    sys.exit(0 if test_result else 1) 