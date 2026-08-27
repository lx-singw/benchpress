"""
Custom Exceptions for benchpress-python.
"""

from typing import Optional, Any, List


class BenchpressError(Exception):
    """Base exception for Benchpress SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class AuthenticationError(BenchpressError):
    """Raised when API key is missing or invalid."""

    def __init__(self, message: str = "Invalid or missing Benchpress API Key"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class RateLimitError(BenchpressError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Benchpress rate limit exceeded (429)"):
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")


class ValidationError(BenchpressError):
    """Raised when request parameters fail schema validation."""

    def __init__(self, message: str = "Validation error", errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")
        self.errors = errors or []


class APIError(BenchpressError):
    """Raised on 5xx server errors from Benchpress API."""

    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        super().__init__(message, status_code=status_code, error_code=error_code)
