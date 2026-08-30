"""Cloud Tasks workload-identity authentication tests."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from config import settings
from security.task_auth import validate_oidc_claims, verify_task_request


app = FastAPI()


@app.post("/test-protected")
async def protected_endpoint(authenticated: bool = Depends(verify_task_request)):
    return {"status": "AUTHENTICATED"}


client = TestClient(app)


def valid_claims(**overrides):
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": settings.tasks_oidc_audience,
        "email": settings.tasks_invoker_service_account,
        "email_verified": True,
        "sub": "1234567890",
        "iat": now - 10,
        "exp": now + 300,
    }
    claims.update(overrides)
    return claims


def test_local_mock_allows_only_absent_auth():
    assert client.post("/test-protected", json={}).status_code == 200
    with patch("security.task_auth._verify_google_token", side_effect=ValueError("bad")):
        response = client.post("/test-protected", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 403


def test_missing_auth_fails_outside_local_mock(monkeypatch):
    monkeypatch.setattr(type(settings), "use_local_mock", property(lambda self: False))
    response = client.post("/test-protected", json={})
    assert response.status_code == 401


def test_valid_bound_oidc_token_succeeds(monkeypatch):
    monkeypatch.setattr(type(settings), "use_local_mock", property(lambda self: False))
    with patch("security.task_auth._verify_google_token", return_value=valid_claims()):
        response = client.post("/test-protected", headers={"Authorization": "Bearer signed-token"})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://issuer.example"},
        {"aud": "https://other.example"},
        {"email": "other@example.iam.gserviceaccount.com"},
        {"email_verified": False},
        {"sub": ""},
        {"exp": 1},
        {"iat": int(time.time()) + 120},
    ],
)
def test_claim_binding_rejects_wrong_identity_or_lifetime(overrides):
    with pytest.raises(ValueError):
        validate_oidc_claims(valid_claims(**overrides))


def test_invalid_verified_claims_return_forbidden(monkeypatch):
    monkeypatch.setattr(type(settings), "use_local_mock", property(lambda self: False))
    with patch("security.task_auth._verify_google_token", return_value=valid_claims(aud="wrong")):
        response = client.post("/test-protected", headers={"Authorization": "Bearer signed-token"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: invalid Cloud Tasks identity"
