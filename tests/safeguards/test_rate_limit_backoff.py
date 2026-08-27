"""
Test Suite for Safeguard 2: Vertex AI Rate-Limit Armor & Exponential Jitter Backoff.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from fsm.engine import retry_with_exponential_jitter


class FakeResourceExhaustedError(Exception):
    """Simulates Google Cloud ResourceExhausted HTTP 429 error."""
    pass


@pytest.mark.asyncio
async def test_exponential_jitter_backoff_recovery():
    """Verify that transient HTTP 429 quota exhaustion is retried and recovers cleanly."""
    attempts = 0

    @retry_with_exponential_jitter(max_retries=4, base_delay=0.01, max_delay=0.1, retry_exceptions=(FakeResourceExhaustedError,))
    async def mock_vertex_gemini_call(prompt: str) -> dict:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise FakeResourceExhaustedError("429 ResourceExhausted: Quota exceeded for generate_content_requests_per_minute")
        return {"response": "Success", "text": f"Generated response for {prompt}"}

    res = await mock_vertex_gemini_call("Explain model routing")
    assert attempts == 3
    assert res["response"] == "Success"
    assert "Generated response for Explain model routing" in res["text"]


@pytest.mark.asyncio
async def test_exponential_jitter_backoff_max_retries_exhausted():
    """Verify that when 429 persists past max_retries, exception is raised properly."""
    attempts = 0

    @retry_with_exponential_jitter(max_retries=3, base_delay=0.01, max_delay=0.05, retry_exceptions=(FakeResourceExhaustedError,))
    async def mock_failing_gemini_call() -> dict:
        nonlocal attempts
        attempts += 1
        raise FakeResourceExhaustedError("429 Quota exhausted")

    with pytest.raises(FakeResourceExhaustedError):
        await mock_failing_gemini_call()

    assert attempts == 3
