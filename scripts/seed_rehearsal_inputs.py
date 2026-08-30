#!/usr/bin/env python3
"""Validate and immutably seed the frozen inputs for a live rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER_SRC = ROOT / "apps" / "sandbox-worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from config import RuntimeMode, settings  # noqa: E402
from contracts.hashing import generate_configuration_id  # noqa: E402
from contracts.models import NativeConfiguration, PolicyVersion, TaskFingerprint  # noqa: E402


class IntegrityConflict(RuntimeError):
    """Raised when a frozen rehearsal document already exists with other content."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha256(payload: object) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode()).hexdigest()


def short_lived_access_token() -> str:
    injected = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN", "").strip()
    if injected:
        return injected
    return subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def immutable_create(client, collection_name: str, document_id: str, payload: dict) -> None:
    from google.cloud import firestore

    reference = client.collection(collection_name).document(document_id)
    transaction = client.transaction()

    @firestore.transactional
    def create(txn):
        snapshot = reference.get(transaction=txn)
        if snapshot.exists:
            if snapshot.to_dict() != payload:
                raise IntegrityConflict(
                    f"Conflicting immutable content for {collection_name}/{document_id}"
                )
            return
        txn.create(reference, payload)

    create(transaction)


def initialize_active_policy(client, collection_prefix: str, policy: PolicyVersion) -> None:
    from google.cloud import firestore

    policy_ref = client.collection(f"{collection_prefix}_policy_versions").document(
        policy.policy_version
    )
    pointer_ref = client.collection(f"{collection_prefix}_policy_pointers").document(
        policy.task_segment_id
    )
    payload = policy.model_dump(mode="json")
    transaction = client.transaction()

    @firestore.transactional
    def initialize(txn):
        pointer = pointer_ref.get(transaction=txn)
        if pointer.exists:
            if pointer.get("active_policy_version") != policy.policy_version:
                raise IntegrityConflict("Active policy pointer already initialized differently")
            return
        policy_snapshot = policy_ref.get(transaction=txn)
        if policy_snapshot.exists and policy_snapshot.to_dict() != payload:
            raise IntegrityConflict(f"Conflicting policy content for {policy.policy_version}")
        if not policy_snapshot.exists:
            txn.create(policy_ref, payload)
        txn.create(
            pointer_ref,
            {
                "task_segment_id": policy.task_segment_id,
                "active_policy_version": policy.policy_version,
                "generation": 1,
                "updated_at": policy.created_at,
            },
        )

    initialize(transaction)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Frozen rehearsal-input JSON document")
    parser.add_argument("--output", type=Path, help="Optional sanitized seeding report")
    parser.add_argument(
        "--gcloud-auth",
        action="store_true",
        help="Use a short-lived token from the active gcloud user session instead of ADC",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the complete bundle without writing Firestore documents",
    )
    args = parser.parse_args()

    if settings.runtime_mode is RuntimeMode.LOCAL_MOCK:
        raise SystemExit("Rehearsal input seeding refuses RUNTIME_MODE=local_mock")
    if settings.repository_backend != "firestore":
        raise SystemExit("Rehearsal input seeding requires REPOSITORY_BACKEND=firestore")

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "1.0.0":
        raise SystemExit("Unsupported rehearsal-input schema_version")
    if raw.get("release_sha") != settings.release_sha:
        raise SystemExit("Frozen input release_sha does not match configured RELEASE_SHA")
    if raw.get("collection_prefix") != settings.firestore_collection_prefix:
        raise SystemExit("Frozen input collection_prefix does not match configured prefix")

    configurations = [NativeConfiguration.model_validate(item) for item in raw["configurations"]]
    if len(configurations) < 2:
        raise SystemExit("At least one baseline and one candidate configuration are required")
    configuration_ids = {item.configuration_id for item in configurations}
    if len(configuration_ids) != len(configurations):
        raise SystemExit("Configuration IDs must be unique")
    for configuration in configurations:
        canonical_configuration = configuration.model_dump(mode="json", exclude_none=True)
        canonical_configuration.pop("configuration_id", None)
        canonical_configuration.pop("created_at", None)
        expected_id = generate_configuration_id(canonical_configuration)
        if configuration.configuration_id != expected_id:
            raise SystemExit(
                f"Configuration {configuration.configuration_id} has canonical ID {expected_id}"
            )

    fingerprint = TaskFingerprint.model_validate(raw["task_fingerprint"])
    if fingerprint.fingerprint_id != settings.task_fingerprint_id:
        raise SystemExit("Frozen fingerprint does not match TASK_FINGERPRINT_ID")
    baseline_policy = PolicyVersion.model_validate(raw["baseline_policy"])
    if not baseline_policy.is_active:
        raise SystemExit("The initial baseline policy must be active")
    if baseline_policy.configuration_id not in configuration_ids:
        raise SystemExit("Baseline policy references an unknown configuration")

    report = {
        "schema_version": "1.0.0",
        "status": "VALIDATED" if args.dry_run else "RUNNING",
        "release_sha": settings.release_sha,
        "project": settings.google_cloud_project,
        "database": settings.firestore_database_id,
        "collection_prefix": settings.firestore_collection_prefix,
        "configuration_ids": sorted(configuration_ids),
        "baseline_policy_version": baseline_policy.policy_version,
        "task_fingerprint_id": fingerprint.fingerprint_id,
        "input_sha256": canonical_sha256(raw),
        "completed_at": utc_now(),
    }

    if not args.dry_run:
        from google.cloud import firestore

        credentials = None
        if args.gcloud_auth:
            from google.oauth2.credentials import Credentials

            credentials = Credentials(token=short_lived_access_token())
        client = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database_id,
            credentials=credentials,
        )
        for configuration in configurations:
            immutable_create(
                client,
                f"{settings.firestore_collection_prefix}_configurations",
                configuration.configuration_id,
                configuration.model_dump(mode="json", exclude_none=True),
            )
        immutable_create(
            client,
            f"{settings.firestore_collection_prefix}_task_fingerprints",
            fingerprint.fingerprint_id,
            fingerprint.model_dump(mode="json"),
        )
        initialize_active_policy(
            client,
            settings.firestore_collection_prefix,
            baseline_policy,
        )
        report["status"] = "PASS"
        report["completed_at"] = utc_now()

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
