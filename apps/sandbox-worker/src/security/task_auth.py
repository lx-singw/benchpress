"""Fail-closed Cloud Tasks OIDC authentication."""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping

from fastapi import HTTPException, Request

from config import settings


logger = logging.getLogger("benchpress.security.task_auth")
ALLOWED_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


def validate_oidc_claims(claims: Mapping[str, Any], now: int | None = None) -> None:
    """Bind a verified Google ID token to the configured worker and invoker."""
    current_time = int(time.time()) if now is None else now
    if claims.get("iss") not in ALLOWED_ISSUERS:
        raise ValueError("unexpected issuer")
    if claims.get("aud") != settings.tasks_oidc_audience:
        raise ValueError("unexpected audience")
    if claims.get("email") != settings.tasks_invoker_service_account:
        raise ValueError("unexpected invoker identity")
    if claims.get("email_verified") is not True:
        raise ValueError("invoker email is not verified")
    if not claims.get("sub"):
        raise ValueError("missing subject")
    if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] <= current_time:
        raise ValueError("token expired")
    if not isinstance(claims.get("iat"), (int, float)) or claims["iat"] > current_time + 30:
        raise ValueError("invalid issued-at time")


def _verify_google_token(token: str) -> Mapping[str, Any]:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    return id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        audience=settings.tasks_oidc_audience,
    )


async def verify_task_request(request: Request) -> bool:
    """Require exact Cloud Tasks workload identity outside local mock mode."""
    authorization = request.headers.get("Authorization", "")

    if settings.use_local_mock and not authorization:
        logger.debug("Local mock request accepted without Cloud Tasks identity")
        return True

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        logger.warning("Rejecting request without a Bearer identity token: %s", request.url.path)
        raise HTTPException(status_code=401, detail="Unauthorized: missing Bearer identity token")

    try:
        claims = _verify_google_token(token.strip())
        validate_oidc_claims(claims)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Cloud Tasks OIDC validation failed for %s: %s", request.url.path, type(exc).__name__)
        raise HTTPException(status_code=403, detail="Forbidden: invalid Cloud Tasks identity") from exc

    logger.info(
        "Cloud Tasks identity accepted for %s (subject=%s)",
        request.url.path,
        claims.get("sub"),
    )
    return True
