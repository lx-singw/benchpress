"""
SyncBenchpressClient Pytest Suite.
"""

import pytest
import httpx
from benchpress import SyncBenchpressClient
from benchpress.exceptions import ValidationError, RateLimitError


def test_sync_get_routing_recommendation():
    """Test SyncBenchpressClient.get_routing_recommendation with mock response."""

    def mock_handler(request: httpx.Request):
        assert request.url.path == "/api/v1/routing-recommendation"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "latency_ms": 3.8,
                "timestamp": "2026-08-27T08:00:00Z",
                "recommendation": {
                    "recommendedStrategy": "FAST_CODER",
                    "plannerModel": "gemini-2.5-flash",
                    "coderModel": "gemini-2.5-flash",
                    "projectedCprUsd": 0.048,
                    "currentModelCprUsd": 1.32,
                    "projectedSavingsPct": 96.3,
                    "passAt1EstimatePct": 58.4,
                    "estimatedTurns": 6,
                    "rationale": "Quick edits execute on Gemini 2.5 Flash saving 96.3%.",
                    "proxyConfig": {
                        "baseUrl": "http://localhost:3000/api/v1/proxy",
                        "modelHeader": "x-benchpress-route",
                    },
                },
            },
        )

    transport = httpx.MockTransport(mock_handler)
    with SyncBenchpressClient(base_url="http://mock-benchpress.local") as client:
        client._client = httpx.Client(
            transport=transport,
            base_url="http://mock-benchpress.local",
            headers=client._get_headers(),
        )

        res = client.get_routing_recommendation(
            task_type="quick_edit",
            codebase_language="typescript",
            current_model="gpt-4o",
        )

        assert res.status == "success"
        assert res.recommendation.recommendedStrategy == "FAST_CODER"
        assert res.recommendation.projectedSavingsPct == 96.3


def test_sync_client_error_handling():
    """Test error handling on 429 rate limit."""

    def mock_handler(request: httpx.Request):
        return httpx.Response(429, json={"message": "Too many requests to Benchpress API"})

    transport = httpx.MockTransport(mock_handler)
    with SyncBenchpressClient(base_url="http://mock-benchpress.local") as client:
        client._client = httpx.Client(
            transport=transport,
            base_url="http://mock-benchpress.local",
            headers=client._get_headers(),
        )

        with pytest.raises(RateLimitError):
            client.list_benchmarks()
