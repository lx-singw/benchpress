"""
Google Cloud Tasks Dispatcher Tier.
Dispatches immutable run execution, aggregation, and canary tasks with deterministic names and OIDC tokens.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from contracts.models import RunManifest
from config import settings

logger = logging.getLogger("benchpress.task_queue.cloud_tasks")


class CloudTasksDispatcher:
    """Dispatches asynchronous idempotent tasks to Google Cloud Tasks."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        queue_name: Optional[str] = None,
    ):
        self.project_id = project_id or settings.google_cloud_project
        self.location = location or settings.google_cloud_region
        self.queue_name = queue_name or "trajectory-execution-queue"
        self.dispatched_tasks: List[Dict[str, Any]] = []

    def dispatch_run_tasks(
        self,
        manifests: List[RunManifest],
        worker_base_url: Optional[str] = None,
    ) -> List[str]:
        """Fan out immutable run manifests as Cloud Tasks."""
        base_url = (worker_base_url or f"http://{settings.host}:{settings.port}").rstrip("/")
        target_url = f"{base_url}{settings.endpoint_execute_run}"
        task_names: List[str] = []

        for manifest in manifests:
            # Deterministic task name for exactly-once Cloud Tasks queue deduplication
            task_name = f"projects/{self.project_id}/locations/{self.location}/queues/{self.queue_name}/tasks/{manifest.logical_run_key}"
            payload = manifest.model_dump(mode="json")

            if settings.use_local_mock:
                logger.info(f"[MockCloudTasks] Enqueued deterministic task '{manifest.logical_run_key}' to {target_url}")
                self.dispatched_tasks.append({
                    "task_name": task_name,
                    "target_url": target_url,
                    "payload": payload,
                })
                task_names.append(task_name)
            else:
                try:
                    from google.cloud import tasks_v2
                    client = tasks_v2.CloudTasksClient()
                    parent = client.queue_path(self.project_id, self.location, self.queue_name)

                    http_request = {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": target_url,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(payload).encode("utf-8"),
                    }

                    # Attach OIDC service account token
                    if hasattr(settings, "tasks_invoker_service_account"):
                        http_request["oidc_token"] = {
                            "service_account_email": settings.tasks_invoker_service_account,
                            "audience": base_url,
                        }

                    task = {
                        "name": task_name,
                        "http_request": http_request,
                    }

                    response = client.create_task(request={"parent": parent, "task": task})
                    task_names.append(response.name)
                except Exception as e:
                    logger.error(f"Failed to enqueue task '{task_name}': {e}")
                    raise

        return task_names

    def dispatch_orchestrate_task(
        self,
        event_id: str,
        correlation_id: str,
        worker_base_url: Optional[str] = None,
    ) -> str:
        """Enqueue single evaluation orchestrator task for a received ChangeEvent."""
        base_url = (worker_base_url or f"http://{settings.host}:{settings.port}").rstrip("/")
        target_url = f"{base_url}{settings.endpoint_orchestrate}"
        task_name = f"projects/{self.project_id}/locations/{self.location}/queues/{self.queue_name}/tasks/orch_{event_id}"

        payload = {
            "event_id": event_id,
            "correlation_id": correlation_id,
        }

        if settings.use_local_mock:
            logger.info(f"[MockCloudTasks] Enqueued orchestration task 'orch_{event_id}' to {target_url}")
            self.dispatched_tasks.append({
                "task_name": task_name,
                "target_url": target_url,
                "payload": payload,
            })
            return task_name
        else:
            try:
                from google.cloud import tasks_v2
                client = tasks_v2.CloudTasksClient()
                parent = client.queue_path(self.project_id, self.location, self.queue_name)

                http_request = {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": target_url,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(payload).encode("utf-8"),
                }

                task = {"name": task_name, "http_request": http_request}
                response = client.create_task(request={"parent": parent, "task": task})
                return response.name
            except Exception as e:
                logger.error(f"Failed to enqueue orchestration task '{task_name}': {e}")
                raise
