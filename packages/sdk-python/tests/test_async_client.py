"""
AsyncBenchpressClient Pytest Suite.
"""

import pytest
import httpx
from benchpress import AsyncBenchpressClient
from benchpress.exceptions import ValidationError, AuthenticationError


@pytest.mark.asyncio
async def test_async_get_routing_recommendation(monkeypatch):
    """Test AsyncBenchpressClient.get_routing_recommendation with mock response."""

    def mock_handler(request: httpx.Request):
        assert request.url.path == "/api/v1/routing-recommendation"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "latency_ms": 4.2,
                "timestamp": "2026-08-27T08:00:00Z",
                "recommendation": {
                    "recommendedStrategy": "HYBRID_CHOREOGRAPHY",
                    "plannerModel": "gemini-2.5-pro",
                    "coderModel": "gemini-2.5-flash",
                    "projectedCprUsd": 0.185,
                    "currentModelCprUsd": 1.48,
                    "projectedSavingsPct": 87.5,
                    "passAt1EstimatePct": 71.2,
                    "estimatedTurns": 9,
                    "rationale": "Switching to Hybrid achieves 87.5% cost reduction.",
                    "proxyConfig": {
                        "baseUrl": "http://localhost:3000/api/v1/proxy",
                        "modelHeader": "x-benchpress-route",
                    },
                },
            },
        )

    transport = httpx.MockTransport(mock_handler)
    async with AsyncBenchpressClient(base_url="http://mock-benchpress.local") as client:
        # Swap internal client transport
        client._client = httpx.AsyncClient(
            transport=transport,
            base_url="http://mock-benchpress.local",
            headers=client._get_headers(),
        )

        res = await client.get_routing_recommendation(
            task_type="code_bug_fix",
            codebase_language="python",
            current_model="claude-3-7-sonnet",
        )

        assert res.status == "success"
        assert res.recommendation.recommendedStrategy == "HYBRID_CHOREOGRAPHY"
        assert res.recommendation.projectedSavingsPct == 87.5
        assert res.recommendation.plannerModel == "gemini-2.5-pro"
        assert res.recommendation.coderModel == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_async_list_benchmarks(monkeypatch):
    """Test AsyncBenchpressClient.list_benchmarks."""

    def mock_handler(request: httpx.Request):
        assert request.url.path == "/api/v1/benchmarks"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "count": 1,
                "timestamp": "2026-08-27T08:00:00Z",
                "data": [
                    {
                        "modelId": "hybrid-gemini-pro-flash",
                        "modelName": "Benchpress 2-Tier",
                        "provider": "Benchpress Hybrid",
                        "taskSuite": "SWE-bench Verified",
                        "passRatePct": 71.2,
                        "cprUsd": 0.185,
                        "meanTurns": 9.4,
                        "meanLatencySeconds": 14.6,
                        "astHealingCount": 28,
                        "tokenVelocityKps": 5.4,
                        "paretoFrontier": True,
                    }
                ],
            },
        )

    transport = httpx.MockTransport(mock_handler)
    async with AsyncBenchpressClient(base_url="http://mock-benchpress.local") as client:
        client._client = httpx.AsyncClient(
            transport=transport,
            base_url="http://mock-benchpress.local",
            headers=client._get_headers(),
        )

        res = await client.list_benchmarks(suite="swe_bench_verified")
        assert res.status == "success"
        assert len(res.data) == 1
        assert res.data[0].paretoFrontier is True
