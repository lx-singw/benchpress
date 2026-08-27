"""
Pytest Test Suite for Benchpress Python SDK Client.
"""

import pytest
import json
import httpx
from benchpress.client import (
    BenchpressClient,
    RoutingRecommendation,
    TrajectorySubmissionResponse,
    BenchmarkEntry,
)


@pytest.fixture
def mock_transport():
    """Custom MockTransport handler for Benchpress API endpoints."""
    def handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path

        if url_path.endswith("/routing-recommendation"):
            payload = json.loads(request.content.decode())
            assert "task_type" in payload
            assert "current_model" in payload

            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "recommendedStrategy": "HYBRID_CHOREOGRAPHY",
                    "plannerModel": "gemini-2.5-pro",
                    "coderModel": "gemini-2.5-flash",
                    "rationale": "Routing to Gemini 2.5 Pro + Flash reduces cost by 68.2%",
                    "projectedCprUsd": 0.28,
                    "projectedSavingsPct": 68.2,
                    "confidenceScore": 0.94,
                    "evaluatedAt": "2026-08-27T07:00:00Z",
                },
            )

        elif url_path.endswith("/trajectory-run"):
            payload = json.loads(request.content.decode())
            assert payload["task_suite"] == "SWE_BENCH_VERIFIED"
            assert payload["task_id"] == "django-12858"

            return httpx.Response(
                202,
                json={
                    "trajectory_id": "traj-test-99",
                    "status": "QUEUED",
                    "queue_name": "trajectory-execution-queue",
                    "enqueued_at": "2026-08-27T07:00:00Z",
                    "status_url": "/api/v1/trajectories/traj-test-99",
                },
            )

        elif url_path.endswith("/benchmarks"):
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "benchmarks": [
                        {
                            "modelId": "gemini-2.5-pro",
                            "modelName": "Gemini 2.5 Pro",
                            "provider": "Google",
                            "taskSuite": "SWE-bench Verified",
                            "passRatePct": 63.8,
                            "cprUsd": 0.42,
                            "meanTurns": 11.2,
                            "meanLatencySeconds": 18.4,
                            "astHealingCount": 14,
                            "tokenVelocityKps": 4.8,
                            "paretoFrontier": True,
                        },
                        {
                            "modelId": "gemini-2.5-flash",
                            "modelName": "Gemini 2.5 Flash",
                            "provider": "Google",
                            "taskSuite": "SWE-bench Verified",
                            "passRatePct": 41.5,
                            "cprUsd": 0.12,
                            "meanTurns": 8.5,
                            "meanLatencySeconds": 6.8,
                            "astHealingCount": 19,
                            "tokenVelocityKps": 7.2,
                            "paretoFrontier": True,
                        },
                    ],
                    "totalCount": 2,
                    "generatedAt": "2026-08-27T07:00:00Z",
                },
            )

        elif url_path.endswith("/error-endpoint"):
            return httpx.Response(500, json={"error": "Internal Server Error"})

        return httpx.Response(404, json={"error": "Not Found"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_get_routing_recommendation(mock_transport):
    client = BenchpressClient(api_key="test-key-123", base_url="http://mock-benchpress.local/api/v1")
    client._client = httpx.AsyncClient(
        base_url="http://mock-benchpress.local/api/v1",
        transport=mock_transport,
    )

    rec = await client.get_routing_recommendation(
        task_type="bug_fix",
        current_model="gpt-4o",
        budget_limit_usd=1.50,
        latency_target_ms=2000,
    )

    assert isinstance(rec, RoutingRecommendation)
    assert rec.recommended_strategy == "HYBRID_CHOREOGRAPHY"
    assert rec.planner_model == "gemini-2.5-pro"
    assert rec.coder_model == "gemini-2.5-flash"
    assert rec.projected_cpr_usd == 0.28
    assert rec.projected_savings_pct == 68.2
    assert rec.confidence_score == 0.94

    await client.close()


@pytest.mark.asyncio
async def test_submit_trajectory(mock_transport):
    client = BenchpressClient(base_url="http://mock-benchpress.local/api/v1")
    client._client = httpx.AsyncClient(
        base_url="http://mock-benchpress.local/api/v1",
        transport=mock_transport,
    )

    sub = await client.submit_trajectory(
        task_suite="SWE_BENCH_VERIFIED",
        task_id="django-12858",
        model_id="gemini-2.5-pro",
        budget_limit_usd=2.00,
        max_turns=15,
    )

    assert isinstance(sub, TrajectorySubmissionResponse)
    assert sub.trajectory_id == "traj-test-99"
    assert sub.status == "QUEUED"
    assert sub.queue_name == "trajectory-execution-queue"
    assert "traj-test-99" in sub.status_url

    await client.close()


@pytest.mark.asyncio
async def test_get_benchmarks(mock_transport):
    client = BenchpressClient(base_url="http://mock-benchpress.local/api/v1")
    client._client = httpx.AsyncClient(
        base_url="http://mock-benchpress.local/api/v1",
        transport=mock_transport,
    )

    benchmarks = await client.get_benchmarks(suite="SWE-bench Verified")

    assert len(benchmarks) == 2
    assert isinstance(benchmarks[0], BenchmarkEntry)
    assert benchmarks[0].model_id == "gemini-2.5-pro"
    assert benchmarks[0].pass_rate_pct == 63.8
    assert benchmarks[0].cpr_usd == 0.42
    assert benchmarks[0].pareto_frontier is True

    await client.close()


@pytest.mark.asyncio
async def test_client_context_manager():
    async with BenchpressClient(api_key="secret-api-key", base_url="http://mock-benchpress.local") as client:
        assert client.api_key == "secret-api-key"
        assert client.base_url == "http://mock-benchpress.local"
        assert client._client.headers["authorization"] == "Bearer secret-api-key"
        assert "benchpress-python" in client._client.headers["user-agent"]


@pytest.mark.asyncio
async def test_client_error_handling(mock_transport):
    client = BenchpressClient(base_url="http://mock-benchpress.local/api/v1")
    client._client = httpx.AsyncClient(
        base_url="http://mock-benchpress.local/api/v1",
        transport=mock_transport,
    )

    with pytest.raises(httpx.HTTPStatusError):
        res = await client._client.get("/error-endpoint")
        res.raise_for_status()

    await client.close()
