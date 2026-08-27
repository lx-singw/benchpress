"""
Benchpress Python SDK and Dynamic Model Router Package.
"""

from .client import BenchpressClient, AsyncBenchpressClient, SyncBenchpressClient
from .decorator import trace_trajectory
from .exceptions import (
    BenchpressError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError,
)
from .models import (
    RoutingRecommendationRequest,
    RoutingRecommendationResponse,
    BenchmarkListResponse,
    DispatchTrajectoryRequest,
    DispatchTrajectoryResponse,
    TrajectoryStatusResponse,
)

__version__ = "1.0.0"

__all__ = [
    "BenchpressClient",
    "AsyncBenchpressClient",
    "SyncBenchpressClient",
    "trace_trajectory",
    "BenchpressError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "APIError",
    "RoutingRecommendationRequest",
    "RoutingRecommendationResponse",
    "BenchmarkListResponse",
    "DispatchTrajectoryRequest",
    "DispatchTrajectoryResponse",
    "TrajectoryStatusResponse",
]
