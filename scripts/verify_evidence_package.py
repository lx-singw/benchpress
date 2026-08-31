#!/usr/bin/env python3
"""Offline, fail-closed verification of a Benchpress measured evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKER_SRC = REPO_ROOT / "apps" / "sandbox-worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

from contracts.hashing import (
    generate_aggregate_id,
    generate_configuration_id,
    generate_logical_run_key,
    generate_receipt_id,
)
from contracts.models import (
    Aggregate,
    CanaryResult,
    ChangeEvent,
    DecisionReceipt,
    ExperimentPlan,
    NativeConfiguration,
    PolicyVersion,
    ReplayEvent,
    RunManifest,
    RunResult,
    TaskFingerprint,
)
from contracts.states import (
    ExperimentState,
    LogicalRunState,
    PublicDecision,
    validate_experiment_transition,
)


SCHEMA_BY_CATEGORY = {
    "change_events": "change-event.v1.json",
    "task_fingerprints": "task-fingerprint.v1.json",
    "configurations": "native-configuration.v1.json",
    "plans": "experiment-plan.v1.json",
    "run_manifests": "run-manifest.v1.json",
    "run_results": "run-result.v1.json",
    "aggregates": "aggregate.v1.json",
    "policy_versions": "policy-version.v1.json",
    "canary_results": "canary-result.v1.json",
    "decision_receipts": "decision-receipt.v1.json",
    "replay_events": "replay-event.v1.json",
}
MODEL_BY_CATEGORY = {
    "change_events": ChangeEvent,
    "task_fingerprints": TaskFingerprint,
    "configurations": NativeConfiguration,
    "plans": ExperimentPlan,
    "run_manifests": RunManifest,
    "run_results": RunResult,
    "aggregates": Aggregate,
    "policy_versions": PolicyVersion,
    "canary_results": CanaryResult,
    "decision_receipts": DecisionReceipt,
    "replay_events": ReplayEvent,
}
PERSISTENCE_FIELDS_BY_CATEGORY = {
    "run_manifests": {
        "invocation_fence",
        "run_state",
        "state_version",
        "terminal_result_key",
    },
}


class VerificationFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def deterministic_task_name(queue_name: str, kind: str, logical_id: str) -> str:
    digest = hashlib.sha256(f"{kind}:{logical_id}".encode()).hexdigest()[:32]
    return f"{queue_name}/tasks/{kind}-{digest}"


def load_json(root: Path, relative: str) -> Any:
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"Manifest path escapes bundle: {relative}")
    require(path.is_file(), f"Manifest references missing file: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_checksums(root: Path) -> int:
    checksum_file = root / "checksums.sha256"
    require(checksum_file.is_file(), "checksums.sha256 is missing")
    checked = 0
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()) and path.is_file(), f"Checksum target missing: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"Checksum mismatch: {relative}")
        checked += 1
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"checksums.sha256", "verification-report.json"}
    }
    listed = {
        line.split("  ", 1)[1]
        for line in checksum_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    require(actual == listed, "Checksum inventory does not cover every source artifact")
    return checked


def validate_schema(document: Any, schema_name: str) -> None:
    schema_path = REPO_ROOT / "packages" / "contracts" / "schemas" / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        return
    jsonschema.validate(document, schema, format_checker=jsonschema.FormatChecker())


def contract_projection(category: str, document: dict[str, Any]) -> dict[str, Any]:
    """Project an authoritative record onto its immutable contract payload."""
    model = MODEL_BY_CATEGORY[category]
    contract_fields = set(model.model_fields)
    persistence_fields = PERSISTENCE_FIELDS_BY_CATEGORY.get(category, set())
    unknown = set(document) - contract_fields - persistence_fields
    require(not unknown, f"Unexpected persistence fields in {category}: {sorted(unknown)}")
    return {key: value for key, value in document.items() if key in contract_fields}


def verify_run_manifest_lifecycle(document: dict[str, Any]) -> None:
    required = PERSISTENCE_FIELDS_BY_CATEGORY["run_manifests"]
    missing = required - set(document)
    require(not missing, f"Run manifest lifecycle fields are missing: {sorted(missing)}")
    require(
        isinstance(document["state_version"], int) and document["state_version"] >= 1,
        "Run manifest state_version is invalid",
    )
    require(
        isinstance(document["invocation_fence"], int) and document["invocation_fence"] >= 0,
        "Run manifest invocation_fence is invalid",
    )
    LogicalRunState(document["run_state"])
    require(
        document["terminal_result_key"] == document["logical_run_key"],
        "Terminal run manifest points to another result",
    )


def load_firestore(manifest: dict[str, Any], root: Path) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {}
    for category, files in manifest["firestore"].items():
        documents = [load_json(root, relative) for relative in files]
        for document in documents:
            text = json.dumps(document, sort_keys=True)
            require("DEMO_FIXTURE" not in text, f"Fixture contamination in {category}")
            if category in SCHEMA_BY_CATEGORY:
                projection = contract_projection(category, document)
                validate_schema(projection, SCHEMA_BY_CATEGORY[category])
                MODEL_BY_CATEGORY[category].model_validate(projection)
                if category == "run_manifests":
                    verify_run_manifest_lifecycle(document)
        records[category] = documents
    return records


def verify_configuration_ids(records: dict[str, list[dict[str, Any]]]) -> None:
    for config in records.get("configurations", []):
        payload = {key: value for key, value in config.items() if key not in {"configuration_id", "created_at"}}
        require(generate_configuration_id(payload) == config["configuration_id"], f"Configuration ID mismatch: {config['configuration_id']}")


def verify_run_keys(records: dict[str, list[dict[str, Any]]]) -> None:
    for manifest in records.get("run_manifests", []):
        payload = {
            key: manifest[key]
            for key in [
                "experiment_id", "task_id", "task_version_hash", "configuration_id",
                "repetition_index", "harness_version", "oracle_version",
            ]
        }
        require(generate_logical_run_key(payload) == manifest["logical_run_key"], f"Run key mismatch: {manifest['logical_run_key']}")


def verify_aggregates(records: dict[str, list[dict[str, Any]]]) -> None:
    results = {item["logical_run_key"]: item for item in records.get("run_results", [])}
    for aggregate in records.get("aggregates", []):
        expected_id = generate_aggregate_id({
            "experiment_id": aggregate["experiment_id"],
            "configuration_id": aggregate["configuration_id"],
            "aggregation_policy_version": aggregate["aggregation_policy_version"],
            "eligible_run_keys": aggregate["eligible_run_keys"],
        })
        require(expected_id == aggregate["aggregate_id"], f"Aggregate ID mismatch: {aggregate['aggregate_id']}")
        included = [results[key] for key in aggregate["eligible_run_keys"] if key in results]
        require(len(included) == len(aggregate["eligible_run_keys"]), f"Aggregate has missing run results: {aggregate['aggregate_id']}")
        require(all(item["eligible_for_aggregation"] for item in included), "Aggregate includes an ineligible run")
        resolved = sum(bool(item["resolved"]) for item in included)
        cost = sum(Decimal(item["observed_cost_usd"]) for item in included)
        require(aggregate["total_attempts"] == len(included), "Aggregate attempt count mismatch")
        require(aggregate["resolved_count"] == resolved, "Aggregate success count mismatch")
        require(aggregate["failed_count"] == len(included) - resolved, "Aggregate failure count mismatch")
        require(aggregate["total_cost_usd"] == f"{cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP):.6f}", "Aggregate cost mismatch")
        if resolved:
            cpr = (cost / Decimal(resolved)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            require(aggregate.get("cpr_defined") is True and aggregate.get("cpr_usd") == f"{cpr:.6f}", "Aggregate CPR mismatch")
        else:
            require(aggregate.get("cpr_defined") is False, "Zero-success CPR must be undefined")
            require(aggregate.get("cpr_usd") is None, "Zero-success CPR cannot be numeric")
            require(aggregate.get("cpr_undefined_reason") == "ZERO_VERIFIED_SUCCESSES", "Missing zero-success CPR reason")


def verify_receipt(records: dict[str, list[dict[str, Any]]], correlation_id: str) -> dict[str, Any]:
    receipts = records.get("decision_receipts", [])
    publications = records.get("published_decisions", [])
    require(len(receipts) == 1 and len(publications) == 1, "Expected exactly one receipt and publication")
    receipt = receipts[0]
    require(receipt["truth_class"] == "BENCHPRESS_MEASURED", "Receipt is not measured")
    require(receipt["correlation_id"] == correlation_id, "Receipt correlation mismatch")
    require(generate_receipt_id(receipt) == receipt["receipt_id"], "Receipt digest/ID mismatch")
    publication = publications[0]
    require(publication.get("publication_status") == "PUBLISHED", "Publication pointer is not PUBLISHED")
    require(publication.get("receipt_id") == receipt["receipt_id"], "Publication points to another receipt")
    for field in [
        "trigger_event_id", "fingerprint_id", "plan_id", "baseline_policy_version",
        "selected_task_ids", "eligible_run_keys", "baseline_evidence",
        "approval_boundary_version", "publication_status",
    ]:
        require(bool(receipt.get(field)), f"Measured receipt is missing {field}")
    require(receipt["publication_status"] == "PUBLISHED", "Receipt publication status is invalid")

    plans = records.get("plans", [])
    fingerprints = records.get("task_fingerprints", [])
    triggers = records.get("change_events", [])
    require(len(plans) == 1, "Expected exactly one approved plan")
    require(len(fingerprints) == 1, "Expected exactly one referenced task fingerprint")
    require(len(triggers) == 1, "Expected exactly one trigger ChangeEvent")
    plan = plans[0]
    require(plan["plan_id"] == receipt["plan_id"], "Receipt points to another plan")
    require(plan["fingerprint_id"] == receipt["fingerprint_id"], "Receipt/plan fingerprint mismatch")
    require(fingerprints[0]["fingerprint_id"] == receipt["fingerprint_id"], "Task fingerprint record mismatch")
    require(plan["event_id"] == receipt["trigger_event_id"], "Receipt/plan trigger mismatch")
    require(triggers[0]["event_id"] == receipt["trigger_event_id"], "ChangeEvent record mismatch")
    require(plan["selected_task_ids"] == receipt["selected_task_ids"], "Receipt cohort differs from approved plan")
    policies = {item["policy_version"]: item for item in records.get("policy_versions", [])}
    require(receipt["baseline_policy_version"] in policies, "Receipt baseline policy is missing")
    if receipt.get("candidate_policy_version"):
        require(receipt["candidate_policy_version"] in policies, "Receipt candidate policy is missing")

    aggregates = {item["aggregate_id"]: item for item in records.get("aggregates", [])}
    require(receipt["baseline_aggregate_id"] in aggregates, "Receipt baseline aggregate missing")
    require(
        receipt["baseline_evidence"].get("aggregate_id") == receipt["baseline_aggregate_id"],
        "Embedded baseline evidence mismatch",
    )
    if receipt.get("candidate_aggregate_id"):
        require(receipt["candidate_aggregate_id"] in aggregates, "Receipt candidate aggregate missing")
    canaries = {item["canary_id"]: item for item in records.get("canary_results", [])}
    decision = PublicDecision(receipt["public_decision"])
    if decision == PublicDecision.SWITCH:
        require(receipt.get("canary_id") in canaries, "SWITCH requires a canary")
        canary = canaries[receipt["canary_id"]]
        require(canary["candidate_passed"] and canary["promotion_approved"], "SWITCH canary did not pass")
    elif decision == PublicDecision.TEST_MORE:
        require(receipt["internal_outcome"] == "ABSTAIN_INSUFFICIENT_EVIDENCE", "TEST MORE mapping is invalid")
    elif receipt.get("canary_id"):
        require(canaries[receipt["canary_id"]]["candidate_passed"] is False, "STAY canary evidence is inconsistent")
    return receipt


def verify_replay(records: dict[str, list[dict[str, Any]]]) -> None:
    events = sorted(records.get("replay_events", []), key=lambda item: item["sequence_id"])
    require(events, "Replay events are missing")
    require([event["sequence_id"] for event in events] == list(range(1, len(events) + 1)), "Replay sequence is not contiguous")
    prior_to = None
    for event in events:
        if prior_to is not None:
            require(event["from_state"] == prior_to, "Replay state chain is discontinuous")
        validate_experiment_transition(ExperimentState(event["from_state"]), ExperimentState(event["to_state"]))
        prior_to = event["to_state"]
    require(prior_to == ExperimentState.PUBLISHED.value, "Replay does not end in PUBLISHED")


def verify_cloud_release(manifest: dict[str, Any], root: Path, receipt: dict[str, Any]) -> None:
    terraform_paths = manifest["cloud_run"].get("terraform", [])
    require(len(terraform_paths) == 1, "Terraform outputs are missing")
    outputs = load_json(root, terraform_paths[0])
    release_sha = outputs.get("release_sha", {}).get("value")
    require(release_sha == manifest["git"]["commit_sha"] == receipt["code_commit_sha"], "Release SHA mismatch")
    for key in ["web_image", "worker_image"]:
        image = outputs.get(key, {}).get("value", "")
        require(image.endswith(release_sha) or "@sha256:" in image, f"Mutable or mismatched {key}")

    service_files = manifest["cloud_run"].get("services", [])
    require(len(service_files) == 2, "Expected web and worker Cloud Run metadata")
    service_data = [load_json(root, relative) for relative in service_files]
    serialized = json.dumps(service_data)
    require(release_sha in serialized, "Cloud Run metadata does not expose the release SHA")
    require("-compute@developer.gserviceaccount.com" not in serialized, "Default compute identity is deployed")


def verify_public_api(manifest: dict[str, Any], root: Path, receipt: dict[str, Any]) -> None:
    responses = [load_json(root, path) for path in manifest["public_api"].get("responses", [])]
    require(len(responses) == 3, "Decision, receipt, and replay API exports are required")
    receipt_responses = [item["body"] for item in responses if "/receipts/" in item["url"]]
    require(receipt_responses == [receipt], "Public receipt response differs from stored receipt")
    decision_responses = [item["body"] for item in responses if "/decisions/" in item["url"]]
    require(len(decision_responses) == 1 and decision_responses[0]["receipt_id"] == receipt["receipt_id"], "Public decision mismatch")


def verify_cloud_tasks(
    manifest: dict[str, Any],
    root: Path,
    records: dict[str, list[dict[str, Any]]],
) -> None:
    paths = manifest["cloud_tasks"].get("tasks", [])
    require(len(paths) == 1, "Cloud Tasks evidence is missing")
    evidence = load_json(root, paths[0])
    queue = evidence.get("queue", {})
    require(bool(queue.get("name")), "Cloud Tasks queue name is missing")
    require("RUNNING" in queue.get("state", ""), "Cloud Tasks queue was not running")
    expected = set(evidence.get("expected_run_task_names", []))
    require(len(expected) == len(records.get("run_manifests", [])), "Expected task inventory does not match manifests")
    recomputed = {
        deterministic_task_name(queue["name"], "run", item["logical_run_key"])
        for item in records.get("run_manifests", [])
    }
    require(expected == recomputed, "Cloud Tasks deterministic run identities do not match manifests")
    observations = evidence.get("dispatch_observations", [])
    require(observations, "Durable dispatch observations are missing")
    require(
        all(event.get("correlation_id") == manifest["correlation_id"] for event in observations),
        "Dispatch observation correlation mismatch",
    )
    initial = Counter(
        event.get("object_id")
        for event in observations
        if event.get("event_type") == "CLOUD_TASK_DISPATCHED"
        and event.get("details", {}).get("kind") == "run"
    )
    require(all(initial[name] == 1 for name in expected), "Each logical run requires one initial task dispatch")
    require(
        all(event.get("release_sha") == manifest["git"]["commit_sha"] for event in observations),
        "Dispatch observation release SHA mismatch",
    )
    require(
        any(event.get("details", {}).get("kind") == "aggregate" for event in observations),
        "Aggregate dispatch evidence is missing",
    )
    if records.get("canary_results"):
        require(
            any(event.get("details", {}).get("kind") == "canary" for event in observations),
            "Canary dispatch evidence is missing",
        )


def verify_git(manifest: dict[str, Any]) -> None:
    sha = manifest["git"]["commit_sha"]
    require(len(sha) == 40 and manifest["git"]["clean"] is True, "Invalid Git provenance")
    result = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=REPO_ROOT, capture_output=True)
    require(result.returncode == 0, f"Release commit is unavailable in this clone: {sha}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    args = parser.parse_args()
    root = Path(args.bundle).resolve()
    report_path = root / "verification-report.json"
    report: dict[str, Any] = {"status": "FAIL", "checks": [], "errors": []}
    try:
        require(root.is_dir(), f"Bundle directory not found: {root}")
        checksum_count = verify_checksums(root)
        report["checks"].append({"name": "checksums", "files": checksum_count})
        manifest = load_json(root, "manifest.json")
        validate_schema(manifest, "evidence-manifest.v1.json")
        require(manifest["truth_class"] == "BENCHPRESS_MEASURED", "Manifest is not measured")
        records = load_firestore(manifest, root)
        verify_configuration_ids(records)
        verify_run_keys(records)
        verify_aggregates(records)
        receipt = verify_receipt(records, manifest["correlation_id"])
        verify_replay(records)
        verify_git(manifest)
        verify_cloud_release(manifest, root, receipt)
        verify_public_api(manifest, root, receipt)
        verify_cloud_tasks(manifest, root, records)
        require(bool(manifest["logs"].get("entries")), "Correlation logs are missing")
        require(bool(manifest["tests"].get("reports")), "Test reports are missing")
        report.update({
            "status": "PASS",
            "correlation_id": manifest["correlation_id"],
            "receipt_id": receipt["receipt_id"],
            "release_sha": manifest["git"]["commit_sha"],
        })
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["status"])
    if report["errors"]:
        print(report["errors"][0], file=sys.stderr)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
