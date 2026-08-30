"""Versioned, retry-safe workflow telemetry without sensitive payload content."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from config import settings
from contracts.hashing import compute_canonical_hash, utc_now_rfc3339


logger = logging.getLogger("benchpress.telemetry.events")
SENSITIVE_DETAIL_KEYS = {
    "authorization", "credential", "credentials", "password", "prompt",
    "raw_output", "secret", "source_content",
}


class WorkflowEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    event_id: str = Field(pattern=r"^tel_[a-f0-9]{32}$")
    correlation_id: str
    causation_id: Optional[str] = None
    object_id: str
    event_type: str
    transition: Optional[str] = None
    attempt: int = Field(default=1, ge=1)
    service: str
    release_sha: str
    severity: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


def _sanitize(details: Dict[str, Any]) -> Dict[str, Any]:
    forbidden = sorted(key for key in details if key.lower() in SENSITIVE_DETAIL_KEYS)
    if forbidden:
        raise ValueError(f"Sensitive telemetry detail keys are prohibited: {', '.join(forbidden)}")
    return details


class WorkflowEventEmitter:
    def __init__(self, bigquery_client=None):
        self._lock = threading.RLock()
        self.events: Dict[str, Dict[str, Any]] = {}
        self.client = bigquery_client

    def emit(
        self,
        *,
        correlation_id: str,
        object_id: str,
        event_type: str,
        service: str,
        causation_id: Optional[str] = None,
        transition: Optional[str] = None,
        attempt: int = 1,
        severity: str = "INFO",
        details: Optional[Dict[str, Any]] = None,
    ) -> WorkflowEvent:
        safe_details = _sanitize(details or {})
        identity = {
            "correlation_id": correlation_id,
            "object_id": object_id,
            "event_type": event_type,
            "service": service,
            "causation_id": causation_id,
            "transition": transition,
            "attempt": attempt,
            "details": safe_details,
        }
        event_id = f"tel_{compute_canonical_hash(identity)[:32]}"
        with self._lock:
            existing = self.events.get(event_id)
            if existing:
                return WorkflowEvent.model_validate(existing)
            event = WorkflowEvent(
                event_id=event_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                object_id=object_id,
                event_type=event_type,
                transition=transition,
                attempt=attempt,
                service=service,
                release_sha=settings.release_sha,
                severity=severity,
                timestamp=utc_now_rfc3339(),
                details=safe_details,
            )
            payload = event.model_dump(mode="json")
            self.events[event_id] = payload

        logger.log(getattr(logging, severity, logging.INFO), "%s", payload)
        if not settings.use_local_mock:
            try:
                if self.client is None:
                    from google.cloud import bigquery
                    self.client = bigquery.Client(project=settings.google_cloud_project)
                table = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.workflow_events"
                bigquery_payload = {
                    **payload,
                    # BigQuery's insertAll representation for a native JSON
                    # column is a serialized JSON value, not a nested record.
                    "details": json.dumps(
                        payload["details"],
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
                errors = self.client.insert_rows_json(
                    table,
                    [bigquery_payload],
                    row_ids=[event_id],
                )
                if errors:
                    logger.error("BigQuery workflow event insert failed: %s", errors)
            except Exception as exc:
                logger.error("Workflow telemetry unavailable for %s: %s", event_id, exc)
        return event


workflow_events = WorkflowEventEmitter()
