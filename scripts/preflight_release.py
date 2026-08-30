#!/usr/bin/env python3
"""Run explicit, spend-producing release preflight checks.

This command is never invoked by the normal unit-test gate. It requires a
validated non-local WorkerSettings environment and performs live reads/writes
against the configured Google Cloud project plus one minimal planner-model call.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
WORKER_SRC = ROOT / "apps" / "sandbox-worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from config import RuntimeMode, is_eligible_planner_model, settings  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_worker_readiness(report: dict) -> None:
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2 import id_token

    token = id_token.fetch_id_token(GoogleAuthRequest(), settings.tasks_oidc_audience)
    request = Request(
        f"{settings.worker_base_url.rstrip('/')}/readyz",
        method="GET",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(request, timeout=15) as response:  # noqa: S310 - validated HTTPS URL
        body = json.loads(response.read().decode("utf-8"))
    if response.status != 200 or body.get("release_sha") != settings.release_sha:
        raise RuntimeError("Worker readiness response does not match configured release SHA")
    report["checks"]["worker_readiness"] = {
        "status": "PASS",
        "url": f"{settings.worker_base_url.rstrip('/')}/readyz",
        "release_sha": body.get("release_sha"),
    }


def check_firestore(report: dict) -> None:
    from google.cloud import firestore

    client = firestore.Client(
        project=settings.google_cloud_project,
        database=settings.firestore_database_id,
    )
    check_id = f"preflight-{uuid.uuid4().hex}"
    document = client.collection(f"{settings.firestore_collection_prefix}_preflight").document(check_id)
    transaction = client.transaction()

    @firestore.transactional
    def create_check(txn):
        txn.create(
            document,
            {
                "release_sha": settings.release_sha,
                "created_at": firestore.SERVER_TIMESTAMP,
                "purpose": "release_preflight",
            },
        )

    create_check(transaction)
    snapshot = document.get()
    try:
        if not snapshot.exists or snapshot.get("release_sha") != settings.release_sha:
            raise RuntimeError("Firestore preflight transaction was not readable")
    finally:
        document.delete()
    report["checks"]["firestore_transaction"] = {
        "status": "PASS",
        "database": settings.firestore_database_id,
        "collection_prefix": settings.firestore_collection_prefix,
    }


def check_cloud_tasks(report: dict) -> None:
    from google.cloud import tasks_v2

    client = tasks_v2.CloudTasksClient()
    queue_name = client.queue_path(
        settings.google_cloud_project,
        settings.tasks_location,
        settings.tasks_queue_name,
    )
    queue = client.get_queue(name=queue_name)
    report["checks"]["cloud_tasks_queue"] = {
        "status": "PASS",
        "name": queue.name,
        "state": str(queue.state),
    }


def check_bigquery(report: dict) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=settings.google_cloud_project)
    dataset = client.get_dataset(f"{settings.google_cloud_project}.{settings.bigquery_dataset}")
    required_tables = ["trajectories", "fsm_turns", "workflow_events"]
    available_tables = {table.table_id for table in client.list_tables(dataset)}
    missing = sorted(set(required_tables) - available_tables)
    if missing:
        raise RuntimeError(f"BigQuery tables missing: {', '.join(missing)}")
    report["checks"]["bigquery_dataset"] = {
        "status": "PASS",
        "dataset_id": dataset.full_dataset_id,
        "location": dataset.location,
        "tables": required_tables,
    }


def check_planner_model(report: dict) -> None:
    from google import genai
    from google.genai import types

    if settings.gemini_api_key:
        client = genai.Client(api_key=settings.gemini_api_key)
        api_surface = "gemini_api"
    else:
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.vertex_ai_location,
        )
        api_surface = "vertex_ai"

    started = time.perf_counter()
    generation_config = {"max_output_tokens": 8}
    if settings.planner_model.startswith("gemini-3.7"):
        generation_config["thinking_config"] = types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.LOW
        )
    else:
        generation_config["temperature"] = 0
    response = client.models.generate_content(
        model=settings.planner_model,
        contents="Return exactly the single word READY.",
        config=types.GenerateContentConfig(**generation_config),
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    usage = getattr(response, "usage_metadata", None)
    response_text = (getattr(response, "text", "") or "").strip()
    if not response_text:
        raise RuntimeError("Eligible-model preflight returned no text")
    response_model = getattr(response, "model_version", None)
    if not response_model or not is_eligible_planner_model(response_model):
        raise RuntimeError(f"Provider response model is not eligible Gemini 3.5+: {response_model}")
    report["checks"]["eligible_planner_model"] = {
        "status": "PASS",
        "requested_model": settings.planner_model,
        "response_model_version": response_model,
        "response_id": getattr(response, "response_id", None),
        "api_surface": api_surface,
        "latency_ms": latency_ms,
        "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_token_count", None),
            "candidate_tokens": getattr(usage, "candidates_token_count", None),
            "reasoning_tokens": getattr(usage, "thoughts_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
        },
        "response_text_sha256": __import__("hashlib").sha256(response_text.encode()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the sanitized JSON report")
    parser.add_argument(
        "--skip-worker",
        action="store_true",
        help="Skip the deployed /readyz check during an initial infrastructure preflight",
    )
    args = parser.parse_args()

    if settings.runtime_mode is RuntimeMode.LOCAL_MOCK:
        raise SystemExit("Release preflight refuses RUNTIME_MODE=local_mock")

    report = {
        "schema_version": "1.0.0",
        "started_at": utc_now(),
        "runtime_mode": settings.runtime_mode.value,
        "release_sha": settings.release_sha,
        "project": settings.google_cloud_project,
        "region": settings.google_cloud_region,
        "checks": {},
        "status": "RUNNING",
    }

    checks = [check_firestore, check_cloud_tasks, check_bigquery, check_planner_model]
    if not args.skip_worker:
        checks.insert(0, check_worker_readiness)

    try:
        for check in checks:
            check(report)
        report["status"] = "PASS"
        return_code = 0
    except Exception as exc:
        report["status"] = "FAIL"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        return_code = 1
    finally:
        report["completed_at"] = utc_now()
        rendered = json.dumps(report, indent=2, sort_keys=True)
        print(rendered)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
