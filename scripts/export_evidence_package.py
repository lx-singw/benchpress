#!/usr/bin/env python3
"""Export one measured Benchpress workflow from authoritative cloud state."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
SENSITIVE_KEYS = {
    "authorization",
    "credentials",
    "gemini_api_key",
    "password",
    "prompt",
    "raw_output",
    "secret",
    "source_content",
}


class ExportError(RuntimeError):
    pass


def validate_arguments(args: argparse.Namespace) -> None:
    patterns = {
        "correlation_id": r"^corr_[0-9A-HJKMNP-TV-Z]{26}$",
        "project": r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
        "region": r"^[a-z]+-[a-z]+[0-9]$",
        "queue": r"^[A-Za-z0-9_-]{1,100}$",
        "bigquery_dataset": r"^[A-Za-z_][A-Za-z0-9_]{0,1023}$",
        "collection_prefix": r"^[A-Za-z0-9_]{1,100}$",
        "web_service": r"^[a-z][a-z0-9-]{0,62}$",
        "worker_service": r"^[a-z][a-z0-9-]{0,62}$",
    }
    for field, pattern in patterns.items():
        value = str(getattr(args, field))
        if not re.fullmatch(pattern, value):
            raise ExportError(f"Invalid --{field.replace('_', '-')}: {value}")
    if not re.fullmatch(r"^\(default\)$|^[a-z][a-z0-9-]{2,61}$", args.database):
        raise ExportError(f"Invalid --database: {args.database}")
    if not args.public_url.startswith("https://"):
        raise ExportError("--public-url must be HTTPS")


def json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): sanitize(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def write_json(root: Path, relative: str, value: Any) -> str:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(sanitize(value), indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )
    return relative.replace("\\", "/")


def run_json(command: list[str], cwd: Path = REPO_ROOT) -> Any:
    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "")
        raise ExportError(f"Command failed: {' '.join(command)}: {stderr}") from exc
    return json.loads(result.stdout)


def git_state() -> dict[str, Any]:
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
        raise ExportError("Git HEAD is not a full lowercase commit SHA")
    if dirty:
        raise ExportError("Measured evidence export requires a clean release checkout")
    return {"commit_sha": sha, "clean": True}


def export_firestore(args: argparse.Namespace, root: Path) -> tuple[dict[str, list[str]], dict[str, list[dict[str, Any]]]]:
    try:
        from google.cloud import firestore
    except ImportError as exc:
        raise ExportError("google-cloud-firestore is required") from exc

    client = firestore.Client(project=args.project, database=args.database)
    prefix = args.collection_prefix
    categories = [
        "change_events", "experiments", "task_fingerprints", "configurations", "plans",
        "planner_invocations", "run_manifests", "run_results", "aggregates", "policy_versions",
        "canary_results", "decision_receipts", "replay_events", "published_decisions",
    ]
    exported: dict[str, list[str]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    for category in categories:
        collection = client.collection(f"{prefix}_{category}")
        matches = []
        try:
            matches = [snapshot.to_dict() for snapshot in collection.where("correlation_id", "==", args.correlation_id).stream()]
        except Exception:
            matches = []
        records[category] = matches

    experiments = records["experiments"]
    if len(experiments) != 1:
        raise ExportError(f"Expected one experiment for correlation ID; found {len(experiments)}")
    experiment_id = experiments[0]["experiment_id"]

    # Collections whose records are indexed by experiment rather than correlation.
    for category in ["plans", "planner_invocations", "run_manifests", "run_results", "aggregates", "canary_results", "decision_receipts", "replay_events"]:
        if not records[category]:
            records[category] = [
                snapshot.to_dict()
                for snapshot in client.collection(f"{prefix}_{category}")
                .where("experiment_id", "==", experiment_id)
                .stream()
            ]

    publication = client.collection(f"{prefix}_published_decisions").document(experiment_id).get()
    records["published_decisions"] = [publication.to_dict()] if publication.exists else []

    plans = records["plans"]
    receipts = records["decision_receipts"]
    if len(plans) != 1 or len(receipts) != 1 or len(records["published_decisions"]) != 1:
        raise ExportError("Bundle requires exactly one plan, receipt, and publication pointer")
    fingerprint_id = plans[0].get("fingerprint_id")
    if not fingerprint_id:
        raise ExportError("Approved plan does not reference a task fingerprint")
    fingerprint = (
        client.collection(f"{prefix}_task_fingerprints")
        .document(fingerprint_id)
        .get()
    )
    if not fingerprint.exists:
        raise ExportError(f"Missing task fingerprint {fingerprint_id}")
    records["task_fingerprints"] = [fingerprint.to_dict()]
    receipt = receipts[0]
    if receipt.get("truth_class") != "BENCHPRESS_MEASURED":
        raise ExportError("Fixture/non-measured receipt cannot be exported")
    if records["published_decisions"][0].get("publication_status") != "PUBLISHED":
        raise ExportError("Decision is not published")

    referenced_configs = {
        receipts[0].get("baseline_configuration_id"), receipts[0].get("candidate_configuration_id")
    } - {None}
    records["configurations"] = []
    for config_id in sorted(referenced_configs):
        snapshot = client.collection(f"{prefix}_configurations").document(config_id).get()
        if not snapshot.exists:
            raise ExportError(f"Missing referenced configuration {config_id}")
        records["configurations"].append(snapshot.to_dict())

    referenced_policies = {
        receipt.get("baseline_policy_version"),
        receipt.get("candidate_policy_version"),
    }
    for canary in records["canary_results"]:
        referenced_policies.update([canary.get("baseline_policy_version"), canary.get("candidate_policy_version")])
    records["policy_versions"] = []
    for version in sorted(referenced_policies - {None}):
        snapshot = client.collection(f"{prefix}_policy_versions").document(version).get()
        if not snapshot.exists:
            raise ExportError(f"Missing referenced policy {version}")
        records["policy_versions"].append(snapshot.to_dict())

    for category, values in records.items():
        exported[category] = [
            write_json(root, f"firestore/{category}/{index:04d}.json", value)
            for index, value in enumerate(values, 1)
        ]
    return exported, records


def deterministic_task_id(kind: str, logical_id: str) -> str:
    digest = hashlib.sha256(f"{kind}:{logical_id}".encode()).hexdigest()[:32]
    return f"{kind}-{digest}"


def duration_json(value: Any) -> dict[str, int]:
    """Normalize protobuf and proto-plus duration representations."""
    if isinstance(value, timedelta):
        total_microseconds = (
            (value.days * 86_400 + value.seconds) * 1_000_000
            + value.microseconds
        )
        seconds, remaining_microseconds = divmod(total_microseconds, 1_000_000)
        return {
            "seconds": seconds,
            "nanos": remaining_microseconds * 1_000,
        }
    if hasattr(value, "seconds") and hasattr(value, "nanos"):
        return {"seconds": int(value.seconds), "nanos": int(value.nanos)}
    raise ExportError(f"Unsupported Cloud Tasks duration value: {type(value).__name__}")


def export_tasks(
    args: argparse.Namespace,
    root: Path,
    records: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    try:
        from google.cloud import tasks_v2
        from google.cloud import bigquery
    except ImportError as exc:
        raise ExportError("google-cloud-tasks and google-cloud-bigquery are required") from exc

    tasks_client = tasks_v2.CloudTasksClient()
    queue_name = tasks_client.queue_path(args.project, args.region, args.queue)
    queue = tasks_client.get_queue(request={"name": queue_name})
    queue_metadata = {
        "name": queue.name,
        "state": str(queue.state),
        "rate_limits": {
            "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second,
            "max_concurrent_dispatches": queue.rate_limits.max_concurrent_dispatches,
        },
        "retry_config": {
            "max_attempts": queue.retry_config.max_attempts,
            "max_retry_duration": duration_json(queue.retry_config.max_retry_duration),
            "min_backoff": duration_json(queue.retry_config.min_backoff),
            "max_backoff": duration_json(queue.retry_config.max_backoff),
            "max_doublings": queue.retry_config.max_doublings,
        },
    }

    bq_client = bigquery.Client(project=args.project)
    query = f"""
        SELECT TO_JSON_STRING(e) AS payload
        FROM `{args.project}.{args.bigquery_dataset}.workflow_events` AS e
        WHERE correlation_id = @correlation_id
          AND event_type IN ('CLOUD_TASK_DISPATCHED', 'CLOUD_TASK_DISPATCH_REPLAYED')
        ORDER BY timestamp, event_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("correlation_id", "STRING", args.correlation_id),
        ]
    )
    observations = [json.loads(row["payload"]) for row in bq_client.query(query, job_config=job_config).result()]
    if not observations:
        raise ExportError("No durable Cloud Tasks dispatch observations matched the correlation ID")

    observed_names = {event.get("object_id") for event in observations}
    expected_run_names = {
        f"{queue_name}/tasks/{deterministic_task_id('run', manifest['logical_run_key'])}"
        for manifest in records["run_manifests"]
    }
    missing_run_names = sorted(expected_run_names - observed_names)
    if missing_run_names:
        raise ExportError(f"Missing durable dispatch observations for {len(missing_run_names)} run tasks")
    if not any(event.get("details", {}).get("kind") == "aggregate" for event in observations):
        raise ExportError("Aggregate task dispatch observation is missing")
    if records["canary_results"] and not any(
        event.get("details", {}).get("kind") == "canary" for event in observations
    ):
        raise ExportError("Canary task dispatch observation is missing")

    evidence = {
        "queue": queue_metadata,
        "expected_run_task_names": sorted(expected_run_names),
        "dispatch_observations": observations,
    }
    return {"tasks": [write_json(root, "cloud-tasks/tasks.json", evidence)]}


def export_cloud_run(args: argparse.Namespace, root: Path) -> dict[str, list[str]]:
    files = []
    for service in [args.web_service, args.worker_service]:
        data = run_json([
            "gcloud", "run", "services", "describe", service, "--project", args.project,
            "--region", args.region, "--format=json",
        ])
        files.append(write_json(root, f"cloud-run/{service}.json", data))
    return {"services": files}


def export_logs(
    args: argparse.Namespace,
    root: Path,
    records: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    try:
        from google.cloud import logging_v2
    except ImportError as exc:
        raise ExportError("google-cloud-logging is required") from exc
    client = logging_v2.Client(project=args.project)
    query = f'jsonPayload.correlation_id="{args.correlation_id}"'
    entries = []
    for entry in client.list_entries(filter_=query, order_by=logging_v2.DESCENDING, page_size=1000):
        entries.append({
            "timestamp": entry.timestamp,
            "severity": entry.severity,
            "resource": dict(entry.resource.labels) if entry.resource else {},
            "payload": entry.payload,
        })
    if not entries:
        raise ExportError("No Cloud Logging entries matched the correlation ID")
    change_events = records.get("change_events", [])
    if len(change_events) != 1:
        raise ExportError("Exactly one ChangeEvent is required to verify orchestration dispatch")
    expected_task_id = deterministic_task_id("orchestrate", change_events[0]["event_id"])
    if not any(
        isinstance(entry.get("payload"), dict)
        and str(entry["payload"].get("task_id", "")).endswith(f"/tasks/{expected_task_id}")
        for entry in entries
    ):
        raise ExportError("Structured Cloud Logging proof for the orchestration task is missing")
    return {"entries": [write_json(root, "logs/correlation.json", entries)]}


def export_public_api(args: argparse.Namespace, root: Path, experiment_id: str, receipt_id: str) -> dict[str, list[str]]:
    files = []
    for name, path in {
        "decision": f"/api/v1/decisions/{experiment_id}",
        "receipt": f"/api/v1/receipts/{receipt_id}",
        "replay": f"/api/v1/replays/{experiment_id}",
    }.items():
        url = args.public_url.rstrip("/") + path
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                if response.status != 200:
                    raise ExportError(f"Public endpoint returned {response.status}: {url}")
                payload = json.loads(response.read())
        except Exception as exc:
            raise ExportError(f"Could not export public endpoint {url}: {exc}") from exc
        files.append(write_json(root, f"public-api/{name}.json", {"url": url, "body": payload}))
    return {"responses": files}


def copy_reports(args: argparse.Namespace, root: Path) -> dict[str, list[str]]:
    if not args.test_report:
        raise ExportError("At least one --test-report is required")
    files = []
    for source_name in args.test_report:
        source = Path(source_name).resolve()
        if not source.is_file():
            raise ExportError(f"Test report missing: {source}")
        target = root / "tests" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        files.append(target.relative_to(root).as_posix())
    return {"reports": files}


def write_checksums(root: Path) -> None:
    entries = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in {"checksums.sha256", "verification-report.json"}:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.relative_to(root).as_posix()}")
    (root / "checksums.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("correlation_id")
    parser.add_argument("--environment", required=True, choices=["development", "rehearsal", "production"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--bigquery-dataset", required=True)
    parser.add_argument("--database", default="(default)")
    parser.add_argument("--collection-prefix", required=True)
    parser.add_argument("--web-service", required=True)
    parser.add_argument("--worker-service", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--test-report", action="append", default=[])
    args = parser.parse_args()
    validate_arguments(args)

    root = Path(args.output).resolve()
    if root.exists() and any(root.iterdir()):
        raise ExportError(f"Output directory must be new or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    git = git_state()
    firestore_files, records = export_firestore(args, root)
    receipt = records["decision_receipts"][0]
    experiment_id = receipt["experiment_id"]
    cloud_tasks = export_tasks(args, root, records)
    cloud_run = export_cloud_run(args, root)
    logs = export_logs(args, root, records)
    public_api = export_public_api(args, root, experiment_id, receipt["receipt_id"])
    tests = copy_reports(args, root)
    terraform_outputs = run_json(["terraform", "-chdir=infra/terraform", "output", "-json"])
    terraform_file = write_json(root, "cloud-run/terraform-outputs.json", terraform_outputs)

    provider_files = {
        "invocations": firestore_files.get("planner_invocations", []),
        "run_results": firestore_files.get("run_results", []),
    }
    manifest = {
        "schema_version": "1.0.0",
        "truth_class": "BENCHPRESS_MEASURED",
        "correlation_id": args.correlation_id,
        "environment": args.environment,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "firestore": firestore_files,
        "cloud_tasks": cloud_tasks,
        "cloud_run": {**cloud_run, "terraform": [terraform_file]},
        "logs": logs,
        "provider": provider_files,
        "public_api": public_api,
        "tests": tests,
    }
    write_json(root, "manifest.json", manifest)
    (root / "README.md").write_text(
        f"# Benchpress measured evidence\n\nCorrelation: `{args.correlation_id}`\n\n"
        "Run `python scripts/verify_evidence_package.py <this-directory>` from the matching repository.\n",
        encoding="utf-8",
    )
    write_checksums(root)
    print(root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExportError as exc:
        print(f"EXPORT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
