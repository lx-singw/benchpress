"""
Task Authentication and Authorization Security Tests (IMP-03).
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from security.task_auth import verify_task_request, compute_hmac_signature
from config import settings

app = FastAPI()

@app.post("/test-protected")
async def protected_endpoint(authenticated: bool = Depends(verify_task_request)):
    return {"status": "AUTHENTICATED"}

client = TestClient(app)


def test_missing_auth_header_fails_in_production():
    """Verify that unauthenticated requests fail with 401 when mock mode is disabled."""
    with patch.object(settings, "use_local_mock", False):
        response = client.post("/test-protected", json={"test": "payload"})
        assert response.status_code == 401
        assert "Missing Cloud Tasks authentication credentials" in response.json()["detail"]


def test_valid_hmac_signature():
    """Verify valid HMAC signature succeeds even when mock mode is disabled."""
    with patch.object(settings, "use_local_mock", False):
        now_ts = str(int(time.time()))
        body_bytes = b'{"test":"payload"}'
        secret = settings.benchpress_hmac_secret
        sig = compute_hmac_signature("POST", "/test-protected", now_ts, body_bytes, secret)

        response = client.post(
            "/test-protected",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Benchpress-Signature": sig,
                "X-Benchpress-Timestamp": now_ts,
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "AUTHENTICATED"


def test_expired_hmac_timestamp_fails():
    """Verify expired HMAC timestamp (> 300s) fails with 401."""
    with patch.object(settings, "use_local_mock", False):
        expired_ts = str(int(time.time()) - 400) # 400s old
        body_bytes = b'{"test":"payload"}'
        secret = settings.benchpress_hmac_secret
        sig = compute_hmac_signature("POST", "/test-protected", expired_ts, body_bytes, secret)

        response = client.post(
            "/test-protected",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Benchpress-Signature": sig,
                "X-Benchpress-Timestamp": expired_ts,
            }
        )
        assert response.status_code == 401
        assert "Expired HMAC timestamp" in response.json()["detail"]


def test_invalid_hmac_signature_fails():
    """Verify corrupted HMAC signature fails with 401."""
    with patch.object(settings, "use_local_mock", False):
        now_ts = str(int(time.time()))
        body_bytes = b'{"test":"payload"}'

        response = client.post(
            "/test-protected",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Benchpress-Signature": "invalid_sha256_hex_digest_0000",
                "X-Benchpress-Timestamp": now_ts,
            }
        )
        assert response.status_code == 401
        assert "Invalid HMAC signature" in response.json()["detail"]
