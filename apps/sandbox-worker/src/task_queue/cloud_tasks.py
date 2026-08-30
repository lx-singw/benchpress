"""Deterministic Cloud Tasks dispatcher with exact OIDC configuration."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from config import settings
from contracts.hashing import compute_canonical_hash
from contracts.models import RunManifest
from telemetry.events import workflow_events


logger = logging.getLogger("benchpress.task_queue.cloud_tasks")


def deterministic_task_id(kind: str, logical_id: str) -> str:
    """Build a valid, stable task ID without leaking an arbitrarily long input."""
    digest = hashlib.sha256(f"{kind}:{logical_id}".encode()).hexdigest()[:32]
    return f"{kind}-{digest}"


class CloudTasksDispatcher:
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        queue_name: Optional[str] = None,
        client=None,
        event_emitter=None,
    ):
        self.project_id = project_id or settings.google_cloud_project
        self.location = location or settings.tasks_location
        self.queue_name = queue_name or settings.tasks_queue_name
        self.client = client
        self.event_emitter = event_emitter or workflow_events
        self.dispatched_tasks: List[Dict[str, Any]] = []

    @property
    def queue_path(self) -> str:
        return f"projects/{self.project_id}/locations/{self.location}/queues/{self.queue_name}"

    def _target_url(self, endpoint: str) -> str:
        return f"{settings.worker_base_url.rstrip('/')}{endpoint}"

    def _record_dispatch(
        self,
        *,
        kind: str,
        logical_id: str,
        task_name: str,
        target_url: str,
        payload: Dict[str, Any],
        correlation_id: str,
        replayed: bool,
    ) -> None:
        self.event_emitter.emit(
            correlation_id=correlation_id,
            object_id=task_name,
            event_type="CLOUD_TASK_DISPATCH_REPLAYED" if replayed else "CLOUD_TASK_DISPATCHED",
            service="sandbox-worker",
            details={
                "kind": kind,
                "logical_id": logical_id,
                "target_url": target_url,
                "payload_sha256": compute_canonical_hash(payload),
                "queue_path": self.queue_path,
            },
        )

    def _dispatch(self, kind: str, logical_id: str, endpoint: str, payload: Dict[str, Any], correlation_id: str) -> str:
        task_id = deterministic_task_id(kind, logical_id)
        task_name = f"{self.queue_path}/tasks/{task_id}"
        target_url = self._target_url(endpoint)
        record = {
            "task_name": task_name,
            "target_url": target_url,
            "payload": payload,
            "correlation_id": correlation_id,
        }

        if settings.use_local_mock:
            self.dispatched_tasks.append(record)
            logger.info("[MockCloudTasks] Recorded deterministic task %s", task_name)
            self._record_dispatch(
                kind=kind,
                logical_id=logical_id,
                task_name=task_name,
                target_url=target_url,
                payload=payload,
                correlation_id=correlation_id,
                replayed=False,
            )
            return task_name

        if self.client is None:
            from google.cloud import tasks_v2

            client = tasks_v2.CloudTasksClient()
            http_method = tasks_v2.HttpMethod.POST
        else:
            client = self.client
            http_method = "POST"
        http_request = {
            "http_method": http_method,
            "url": target_url,
            "headers": {
                "Content-Type": "application/json",
                "X-Benchpress-Correlation-ID": correlation_id,
            },
            "body": json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            "oidc_token": {
                "service_account_email": settings.tasks_invoker_service_account,
                "audience": settings.tasks_oidc_audience,
            },
        }
        task = {"name": task_name, "http_request": http_request}
        try:
            response = client.create_task(request={"parent": self.queue_path, "task": task})
            self._record_dispatch(
                kind=kind,
                logical_id=logical_id,
                task_name=response.name,
                target_url=target_url,
                payload=payload,
                correlation_id=correlation_id,
                replayed=False,
            )
            return response.name
        except Exception as exc:
            if getattr(exc, "code", None) in {6, "ALREADY_EXISTS"} or type(exc).__name__ == "AlreadyExists":
                logger.info("Cloud Task already exists; treating deterministic dispatch as idempotent: %s", task_name)
                self._record_dispatch(
                    kind=kind,
                    logical_id=logical_id,
                    task_name=task_name,
                    target_url=target_url,
                    payload=payload,
                    correlation_id=correlation_id,
                    replayed=True,
                )
                return task_name
            raise

    def dispatch_run_tasks(self, manifests: List[RunManifest], worker_base_url: Optional[str] = None) -> List[str]:
        if worker_base_url and worker_base_url.rstrip("/") != settings.worker_base_url.rstrip("/"):
            raise ValueError("Per-call worker URL overrides are prohibited")
        return [
            self._dispatch(
                "run",
                manifest.logical_run_key,
                settings.endpoint_execute_run,
                manifest.model_dump(mode="json"),
                manifest.correlation_id,
            )
            for manifest in manifests
        ]

    def dispatch_orchestrate_task(self, event_id: str, correlation_id: str, worker_base_url: Optional[str] = None) -> str:
        if worker_base_url and worker_base_url.rstrip("/") != settings.worker_base_url.rstrip("/"):
            raise ValueError("Per-call worker URL overrides are prohibited")
        return self._dispatch(
            "orchestrate",
            event_id,
            settings.endpoint_orchestrate,
            {"event_id": event_id, "correlation_id": correlation_id},
            correlation_id,
        )

    def dispatch_aggregate_task(self, experiment_id: str, correlation_id: str, payload: Dict[str, Any]) -> str:
        return self._dispatch("aggregate", experiment_id, settings.endpoint_aggregate, payload, correlation_id)

    def dispatch_canary_task(self, canary_id: str, correlation_id: str, payload: Dict[str, Any]) -> str:
        return self._dispatch("canary", canary_id, settings.endpoint_canary, payload, correlation_id)

    def dispatch_publish_task(self, decision_id: str, correlation_id: str, payload: Dict[str, Any]) -> str:
        return self._dispatch("publish", decision_id, settings.endpoint_publish, payload, correlation_id)

    def cancel_run_task(self, logical_run_key: str) -> bool:
        """Delete a not-yet-delivered run task; never cancels a claimed run."""
        task_id = deterministic_task_id("run", logical_run_key)
        task_name = f"{self.queue_path}/tasks/{task_id}"
        if settings.use_local_mock:
            for record in self.dispatched_tasks:
                if record["task_name"] == task_name and not record.get("cancelled"):
                    record["cancelled"] = True
                    return True
            return False
        client = self.client
        if client is None:
            from google.cloud import tasks_v2
            client = tasks_v2.CloudTasksClient()
        try:
            client.delete_task(request={"name": task_name})
            return True
        except Exception as exc:
            if getattr(exc, "code", None) in {5, "NOT_FOUND"} or type(exc).__name__ == "NotFound":
                return False
            raise
