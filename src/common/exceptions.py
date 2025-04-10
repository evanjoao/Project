"""
Custom exceptions for the trading application.

This module defines a hierarchy of custom exceptions used throughout the trading application
for error handling. The exceptions are organized into categories based on their purpose:

- Trading exceptions: Related to trading operations, orders, and positions
- API exceptions: Related to external API interactions and authentication
- Data exceptions: Related to data fetching, processing, and storage
- Validation exceptions: Related to input validation and data integrity
- Configuration exceptions: Related to application configuration and setup

Each exception class includes a descriptive docstring explaining when it should be raised.
"""

from typing import Optional, Any


# Base exception classes for different error categories
class TradingError(Exception):
    """Base exception for trading related errors.
    
    This exception should be raised when there is an error related to trading operations,
    such as order execution, position management, or risk management.
    """
    pass


class APIError(Exception):
    """Base exception for API related errors.
    
    This exception should be raised when there is an error related to external API
    interactions, such as network issues, rate limiting, or authentication problems.
    """
    pass


class DataError(Exception):
    """Base exception for data related errors.
    
    This exception should be raised when there is an error related to data operations,
    such as fetching, processing, or storing market data or trading information.
    """
    pass


class ValidationError(Exception):
    """Base exception for validation errors.
    
    This exception should be raised when there is an error related to input validation
    or data integrity checks, such as invalid parameters or malformed data.
    """
    pass


class ConfigurationError(Exception):
    """Base exception for configuration errors.
    
    This exception should be raised when there is an error related to application
    configuration, such as missing or invalid settings, environment variables, or
    configuration files.
    """
    pass


# Trading related exceptions
class InsufficientFundsError(TradingError):
    """Raised when there are insufficient funds for a trade.
    
    This exception should be raised when attempting to execute a trade with
    insufficient funds in the account or when the position size exceeds
    available margin.
    """
    pass


class OrderError(TradingError):
    """Raised when there is an error with order execution.
    
    This exception should be raised when there is a problem with order placement,
    modification, or cancellation, such as invalid order parameters or
    exchange-specific errors.
    """
    pass


class PositionError(TradingError):
    """Raised when there is an error with position management.
    
    This exception should be raised when there is a problem with position
    operations, such as opening, closing, or modifying positions.
    """
    pass


class RiskLimitError(TradingError):
    """Raised when a risk limit is exceeded.
    
    This exception should be raised when a trading operation would exceed
    predefined risk limits, such as maximum position size, leverage, or drawdown.
    """
    pass


# API related exceptions
class RateLimitError(APIError):
    """Raised when API rate limit is exceeded.
    
    This exception should be raised when the number of API requests exceeds
    the allowed rate limit for a given time period.
    """
    pass


class AuthenticationError(APIError):
    """Raised when there are authentication issues.
    
    This exception should be raised when there are problems with API authentication,
    such as invalid API keys, expired tokens, or insufficient permissions.
    """
    pass


class ConnectionError(APIError):
    """Raised when there are connection issues with an external API.
    
    This exception should be raised when there are network-related problems
    connecting to an external API, such as timeouts, connection resets, or
    DNS resolution failures.
    """
    pass


class APIResponseError(APIError):
    """Raised when there is an error in the API response.
    
    This exception should be raised when the API returns an error response
    or unexpected data format that cannot be processed.
    """
    pass


# Data related exceptions
class DataFetchError(DataError):
    """Raised when there is an error fetching data.
    
    This exception should be raised when there is a problem retrieving data
    from a data source, such as a database, file, or external API.
    """
    pass


class DataProcessingError(DataError):
    """Raised when there is an error processing data.
    
    This exception should be raised when there is a problem processing or
    transforming data, such as parsing errors, calculation errors, or
    data format issues.
    """
    pass


class DataStorageError(DataError):
    """Raised when there is an error storing data.
    
    This exception should be raised when there is a problem saving or
    persisting data, such as database errors, file I/O errors, or
    storage quota exceeded.
    """
    pass


class DataNotFoundError(DataError):
    """Raised when requested data is not found.
    
    This exception should be raised when attempting to access data that
    does not exist or cannot be found in the expected location.
    """
    pass


# Validation related exceptions
class ParameterValidationError(ValidationError):
    """Raised when a parameter fails validation.
    
    This exception should be raised when a function or method parameter
    fails validation checks, such as type checking, range validation, or
    format validation.
    """
    pass


class DataValidationError(ValidationError):
    """Raised when data fails validation.
    
    This exception should be raised when data fails validation checks,
    such as schema validation, data integrity checks, or business rule
    validation.
    """
    pass


# Configuration related exceptions
class MissingConfigError(ConfigurationError):
    """Raised when a required configuration is missing.
    
    This exception should be raised when a required configuration setting,
    environment variable, or configuration file is missing.
    """
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when a configuration is invalid.
    
    This exception should be raised when a configuration setting,
    environment variable, or configuration file contains invalid values
    or is in an incorrect format.
    """
    pass 