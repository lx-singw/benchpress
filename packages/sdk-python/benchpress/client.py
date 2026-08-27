"""
Async and Sync Clients for Benchpress Developer Platform.
"""

import os
from typing import Optional, Dict, Any, List
import httpx
from .models import (
    RoutingRecommendationRequest,
    RoutingRecommendationResponse,
    RoutingRecommendation,
    BenchmarkListResponse,
    BenchmarkRow,
    DispatchTrajectoryRequest,
    DispatchTrajectoryResponse,
    TrajectoryStatusResponse,
    TaskType,
    CodebaseLanguage,
)
from .exceptions import (
    BenchpressError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError,
)

# Type aliases for backward compatibility
BenchmarkEntry = BenchmarkRow
TrajectorySubmissionResponse = DispatchTrajectoryResponse


class BaseBenchpressClient:
    """Base client sharing authentication and URL routing configuration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key or os.getenv("BENCHPRESS_API_KEY")
        self.base_url = (base_url or os.getenv("BENCHPRESS_BASE_URL") or "http://localhost:3000").rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "benchpress-python/1.0.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_response_error(self, response: httpx.Response):
        try:
            body = response.json()
        except Exception:
            body = {}

        msg = body.get("message") or f"HTTP {response.status_code} Error"
        code = body.get("code")

        if response.status_code == 401:
            raise AuthenticationError(msg)
        elif response.status_code == 429:
            raise RateLimitError(msg)
        elif response.status_code == 400:
            raise ValidationError(msg, errors=body.get("errors"))
        elif response.status_code >= 500:
            raise APIError(msg, status_code=response.status_code, error_code=code)
        else:
            raise BenchpressError(msg, status_code=response.status_code, error_code=code)


class AsyncBenchpressClient(BaseBenchpressClient):
    """Asynchronous HTTP Client using httpx.AsyncClient."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._client

    async def get_routing_recommendation(
        self,
        task_type: str = "code_bug_fix",
        codebase_language: str = "python",
        current_model: str = "claude-3-7-sonnet",
        max_budget_per_task_usd: float = 0.50,
        estimated_prompt_tokens: int = 15000,
        estimated_completion_tokens: int = 2500,
        pareto_weights: Optional[Dict[str, float]] = None,
        budget_limit_usd: Optional[float] = None,
        latency_target_ms: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """Query real-time dynamic model routing recommendation."""
        client = self._ensure_client()
        budget = budget_limit_usd if budget_limit_usd is not None else max_budget_per_task_usd
        # Map task_type alias
        norm_task = "code_bug_fix" if task_type in ["bug_fix", "code_bug_fix"] else task_type

        payload = {
            "task_type": norm_task,
            "codebase_language": codebase_language,
            "current_model": current_model,
            "max_budget_per_task_usd": budget,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "estimated_completion_tokens": estimated_completion_tokens,
            "pareto_weights": pareto_weights,
        }
        res = await client.post("/api/v1/routing-recommendation", json=payload)
        if not res.is_success:
            self._handle_response_error(res)

        data = res.json()
        if "recommendation" in data:
            return RoutingRecommendationResponse.model_validate(data)
        # Direct structure fallback
        return RoutingRecommendation.model_validate(data)

    async def list_benchmarks(
        self,
        suite: Optional[str] = None,
        provider: Optional[str] = None,
        pareto_only: bool = False,
        max_cpr: Optional[float] = None,
    ) -> BenchmarkListResponse:
        """Query continuous economic leaderboard."""
        client = self._ensure_client()
        params: Dict[str, Any] = {}
        if suite:
            params["suite"] = suite
        if provider:
            params["provider"] = provider
        if pareto_only:
            params["paretoOnly"] = "true"
        if max_cpr is not None:
            params["maxCpr"] = str(max_cpr)

        res = await client.get("/api/v1/benchmarks", params=params)
        if not res.is_success:
            self._handle_response_error(res)
        return BenchmarkListResponse.model_validate(res.json())

    async def get_benchmarks(self, suite: Optional[str] = None) -> List[BenchmarkEntry]:
        """Backward-compatible helper returning list of benchmark entries."""
        resp = await self.list_benchmarks(suite=suite)
        return resp.data

    async def dispatch_trajectory(
        self,
        task_suite: str,
        task_id: str,
        model_id: str,
        budget_limit_usd: float = 2.00,
        max_turns: int = 20,
    ) -> DispatchTrajectoryResponse:
        """Dispatch evaluation trajectory run."""
        client = self._ensure_client()
        payload = {
            "taskSuite": task_suite,
            "task_suite": task_suite,
            "taskId": task_id,
            "task_id": task_id,
            "modelId": model_id,
            "model_id": model_id,
            "budgetLimitUsd": budget_limit_usd,
            "budget_limit_usd": budget_limit_usd,
            "maxTurns": max_turns,
            "max_turns": max_turns,
        }
        res = await client.post("/api/v1/trajectory-run", json=payload)
        if not res.is_success:
            self._handle_response_error(res)
        return DispatchTrajectoryResponse.model_validate(res.json())

    async def submit_trajectory(
        self,
        task_suite: str,
        task_id: str,
        model_id: str,
        budget_limit_usd: float = 2.00,
        max_turns: int = 20,
    ) -> DispatchTrajectoryResponse:
        """Backward-compatible alias for dispatch_trajectory."""
        return await self.dispatch_trajectory(
            task_suite=task_suite,
            task_id=task_id,
            model_id=model_id,
            budget_limit_usd=budget_limit_usd,
            max_turns=max_turns,
        )

    async def get_trajectory_status(self, trajectory_id: str) -> TrajectoryStatusResponse:
        """Retrieve live execution trace for trajectory."""
        client = self._ensure_client()
        res = await client.get(f"/api/v1/trajectories/{trajectory_id}")
        if not res.is_success:
            self._handle_response_error(res)
        return TrajectoryStatusResponse.model_validate(res.json())


class SyncBenchpressClient(BaseBenchpressClient):
    """Synchronous HTTP Client using httpx.Client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        self._client: Optional[httpx.Client] = None

    def __enter__(self):
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()
            self._client = None

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def _ensure_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._client

    def get_routing_recommendation(
        self,
        task_type: str = "code_bug_fix",
        codebase_language: str = "python",
        current_model: str = "claude-3-7-sonnet",
        max_budget_per_task_usd: float = 0.50,
        estimated_prompt_tokens: int = 15000,
        estimated_completion_tokens: int = 2500,
        pareto_weights: Optional[Dict[str, float]] = None,
        budget_limit_usd: Optional[float] = None,
        **kwargs,
    ) -> Any:
        client = self._ensure_client()
        budget = budget_limit_usd if budget_limit_usd is not None else max_budget_per_task_usd
        norm_task = "code_bug_fix" if task_type in ["bug_fix", "code_bug_fix"] else task_type

        payload = {
            "task_type": norm_task,
            "codebase_language": codebase_language,
            "current_model": current_model,
            "max_budget_per_task_usd": budget,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "estimated_completion_tokens": estimated_completion_tokens,
            "pareto_weights": pareto_weights,
        }
        res = client.post("/api/v1/routing-recommendation", json=payload)
        if not res.is_success:
            self._handle_response_error(res)

        data = res.json()
        if "recommendation" in data:
            return RoutingRecommendationResponse.model_validate(data)
        return RoutingRecommendation.model_validate(data)

    def list_benchmarks(
        self,
        suite: Optional[str] = None,
        provider: Optional[str] = None,
        pareto_only: bool = False,
        max_cpr: Optional[float] = None,
    ) -> BenchmarkListResponse:
        client = self._ensure_client()
        params: Dict[str, Any] = {}
        if suite:
            params["suite"] = suite
        if provider:
            params["provider"] = provider
        if pareto_only:
            params["paretoOnly"] = "true"
        if max_cpr is not None:
            params["maxCpr"] = str(max_cpr)

        res = client.get("/api/v1/benchmarks", params=params)
        if not res.is_success:
            self._handle_response_error(res)
        return BenchmarkListResponse.model_validate(res.json())

    def get_benchmarks(self, suite: Optional[str] = None) -> List[BenchmarkEntry]:
        resp = self.list_benchmarks(suite=suite)
        return resp.data

    def dispatch_trajectory(
        self,
        task_suite: str,
        task_id: str,
        model_id: str,
        budget_limit_usd: float = 2.00,
        max_turns: int = 20,
    ) -> DispatchTrajectoryResponse:
        client = self._ensure_client()
        payload = {
            "taskSuite": task_suite,
            "task_suite": task_suite,
            "taskId": task_id,
            "task_id": task_id,
            "modelId": model_id,
            "model_id": model_id,
            "budgetLimitUsd": budget_limit_usd,
            "budget_limit_usd": budget_limit_usd,
            "maxTurns": max_turns,
            "max_turns": max_turns,
        }
        res = client.post("/api/v1/trajectory-run", json=payload)
        if not res.is_success:
            self._handle_response_error(res)
        return DispatchTrajectoryResponse.model_validate(res.json())

    def submit_trajectory(
        self,
        task_suite: str,
        task_id: str,
        model_id: str,
        budget_limit_usd: float = 2.00,
        max_turns: int = 20,
    ) -> DispatchTrajectoryResponse:
        return self.dispatch_trajectory(
            task_suite=task_suite,
            task_id=task_id,
            model_id=model_id,
            budget_limit_usd=budget_limit_usd,
            max_turns=max_turns,
        )

    def get_trajectory_status(self, trajectory_id: str) -> TrajectoryStatusResponse:
        client = self._ensure_client()
        res = client.get(f"/api/v1/trajectories/{trajectory_id}")
        if not res.is_success:
            self._handle_response_error(res)
        return TrajectoryStatusResponse.model_validate(res.json())


# Default export is AsyncBenchpressClient for async parity with TypeScript SDK & Python agent workflows
BenchpressClient = AsyncBenchpressClient
