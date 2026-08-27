"""
Benchpress Async & Sync Python Client for Model Routers & Agents.
"""

from typing import Optional, Dict, Any, List
import os
import httpx
from pydantic import BaseModel, Field, ConfigDict


class RoutingRecommendation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    recommended_strategy: str = Field(alias="recommendedStrategy")
    planner_model: str = Field(alias="plannerModel")
    coder_model: str = Field(alias="coderModel")
    rationale: str
    projected_cpr_usd: float = Field(alias="projectedCprUsd")
    projected_savings_pct: float = Field(alias="projectedSavingsPct")
    confidence_score: float = Field(alias="confidenceScore")
    evaluated_at: Optional[str] = Field(default=None, alias="evaluatedAt")


class TrajectorySubmissionResponse(BaseModel):
    trajectory_id: str
    status: str
    queue_name: str
    enqueued_at: str
    status_url: str


class BenchmarkEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model_id: str = Field(alias="modelId")
    model_name: str = Field(alias="modelName")
    provider: str
    task_suite: str = Field(alias="taskSuite")
    pass_rate_pct: float = Field(alias="passRatePct")
    cpr_usd: float = Field(alias="cprUsd")
    mean_turns: float = Field(alias="meanTurns")
    mean_latency_seconds: float = Field(alias="meanLatencySeconds")
    pareto_frontier: bool = Field(alias="paretoFrontier")


class BenchpressClient:
    """Async Client for Benchpress API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("BENCHPRESS_API_KEY", "")
        self.base_url = (base_url or os.environ.get("BENCHPRESS_BASE_URL", "http://localhost:3000/api/v1")).rstrip("/")
        self.timeout = timeout
        headers = {
            "User-Agent": "benchpress-python/1.0.0",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=self.timeout)

    async def get_routing_recommendation(
        self,
        task_type: str,
        current_model: str,
        budget_limit_usd: Optional[float] = None,
        latency_target_ms: Optional[int] = None,
    ) -> RoutingRecommendation:
        """Fetch model routing recommendation."""
        payload: Dict[str, Any] = {
            "task_type": task_type,
            "current_model": current_model,
        }
        if budget_limit_usd is not None:
            payload["budget_limit_usd"] = budget_limit_usd
        if latency_target_ms is not None:
            payload["latency_target_ms"] = latency_target_ms

        res = await self._client.post("/routing-recommendation", json=payload)
        res.raise_for_status()
        return RoutingRecommendation.model_validate(res.json())

    async def submit_trajectory(
        self,
        task_suite: str,
        task_id: str,
        model_id: str,
        budget_limit_usd: float = 2.0,
        max_turns: int = 20,
    ) -> TrajectorySubmissionResponse:
        """Submit a trajectory execution task."""
        payload = {
            "task_suite": task_suite,
            "task_id": task_id,
            "model_id": model_id,
            "budget_limit_usd": budget_limit_usd,
            "max_turns": max_turns,
        }
        res = await self._client.post("/trajectory-run", json=payload)
        res.raise_for_status()
        return TrajectorySubmissionResponse.model_validate(res.json())

    async def get_benchmarks(self, suite: Optional[str] = None) -> List[BenchmarkEntry]:
        """Fetch latest benchmark leaderboard entries."""
        params = {"suite": suite} if suite else {}
        res = await self._client.get("/benchmarks", params=params)
        res.raise_for_status()
        data = res.json()
        return [BenchmarkEntry.model_validate(item) for item in data.get("benchmarks", [])]

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
