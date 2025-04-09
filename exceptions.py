"""
Custom exception classes for API interactions.

This module defines specific exceptions that can be raised during interactions
with the exchange API, allowing for more granular error handling.
"""

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    def __init__(self, message="API authentication failed"):
        super().__init__(message)

class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message="API rate limit exceeded"):
        super().__init__(message)

class InvalidResponseError(APIError):
    """Raised when the API returns an unexpected or invalid response."""
    def __init__(self, message="Received an invalid response from the API"):
        super().__init__(message)

class InvalidRequestError(APIError):
    """Exception raised for invalid requests."""
    def __init__(self, message="Invalid request parameters or format"):
        super().__init__(message)

class ExchangeError(APIError):
    """Base exception for exchange-related errors."""
    
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}
        self.code = "EXCHANGE_ERROR"

class ValidationError(ExchangeError):
    """Exception for validation errors."""
    
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.code = "VALIDATION_ERROR"

class ConfigurationError(ExchangeError):
    """Exception for configuration errors."""
    
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.code = "CONFIGURATION_ERROR"

class NetworkError(ExchangeError):
    """Exception raised for network-related errors."""
    def __init__(self, message="A network error occurred while communicating with the API", details=None):
        super().__init__(message, details)
        self.code = "NETWORK_ERROR"

class OrderError(ExchangeError):
    """Exception raised for order-related errors."""
    def __init__(self, message, details=None):
        super().__init__(message, details)
        self.code = "ORDER_ERROR"
        self.details = details or {}

class InsufficientFundsError(OrderError):
    """Exception raised when there are insufficient funds for an order."""
    def __init__(self, message="Insufficient funds for the operation", status_code=None, data=None):
        details = {"status_code": status_code, "data": data}
        super().__init__(message, details)
        self.code = "INSUFFICIENT_FUNDS"

# --- Self-Testing ---

def _simulate_api_call(scenario: str):
    """Simulates an API call that might raise a custom exception."""
    if scenario == "auth_fail":
        raise AuthenticationError("Invalid API key provided.")
    elif scenario == "rate_limit":
        raise RateLimitError("Too many requests. Please wait.")
    elif scenario == "no_funds":
        raise InsufficientFundsError("Balance too low to place order.")
    elif scenario == "network_issue":
        raise NetworkError("Could not connect to the exchange endpoint.")
    elif scenario == "bad_response":
        raise InvalidResponseError("API returned malformed JSON data.")
    elif scenario == "generic_error":
        raise APIError("An unknown API issue occurred.")
    elif scenario == "success":
        return {"status": "success", "data": "some data"}
    else:
        raise ValueError("Unknown test scenario")

def run_tests() -> bool:
    """
    Runs a suite of fast, independent tests to verify exception handling.

    Returns:
        bool: True if all tests pass, False otherwise.
    """
    test_scenarios = [
        ("auth_fail", AuthenticationError),
        ("rate_limit", RateLimitError),
        ("no_funds", InsufficientFundsError),
        ("network_issue", NetworkError),
        ("bad_response", InvalidResponseError),
        ("generic_error", APIError),
        ("success", None) # Expect no exception for success scenario
    ]
    all_passed = True

    print("--- Running Exception Tests ---")
    for scenario, expected_exception in test_scenarios:
        try:
            print(f"Testing scenario: {scenario}...")
            _simulate_api_call(scenario)
            if expected_exception is not None:
                print(f"  [FAIL] Expected {expected_exception.__name__}, but no exception was raised.")
                all_passed = False
            else:
                print("  [PASS] No exception raised as expected.")
        except APIError as e:
            if expected_exception is None:
                print(f"  [FAIL] Expected no exception, but got {type(e).__name__}: {e}")
                all_passed = False
            elif isinstance(e, expected_exception):
                print(f"  [PASS] Correctly caught {type(e).__name__}: {e}")
            else:
                print(f"  [FAIL] Expected {expected_exception.__name__}, but caught {type(e).__name__}: {e}")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] Caught unexpected non-API exception {type(e).__name__}: {e}")
            all_passed = False

    print("--- Test Summary ---")
    if all_passed:
        print("All exception tests passed.")
    else:
        print("Some exception tests failed.")

    return all_passed

if __name__ == "__main__":
    test_result = run_tests()
    # In a real application, you might exit with a non-zero code on failure
    # import sys
    # sys.exit(0 if test_result else 1)
