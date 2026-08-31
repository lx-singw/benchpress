import hashlib
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from scripts.export_evidence_package import ExportError, duration_json, enum_name
from scripts.verify_evidence_package import VerificationFailure, contract_projection


ROOT = Path(__file__).resolve().parents[2]


def test_verifier_rejects_fixture_manifest(tmp_path):
    manifest = {
        "schema_version": "1.0.0",
        "truth_class": "DEMO_FIXTURE",
        "correlation_id": "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        "environment": "development",
        "exported_at": "2026-08-29T10:00:00.000Z",
        "git": {"commit_sha": "0" * 40, "clean": True},
        "firestore": {},
        "cloud_tasks": {},
        "cloud_run": {},
        "logs": {},
        "provider": {},
        "public_api": {},
        "tests": {},
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (tmp_path / "checksums.sha256").write_text(f"{digest}  manifest.json\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_evidence_package.py"), str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    report = json.loads((tmp_path / "verification-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"


def test_truth_boundary_scan_passes_for_quarantined_root_evidence():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_truth_boundaries.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_cloud_tasks_duration_supports_proto_plus_timedelta():
    assert duration_json(timedelta(seconds=12, microseconds=345_678)) == {
        "seconds": 12,
        "nanos": 345_678_000,
    }


def test_cloud_tasks_duration_supports_protobuf_shape():
    class Duration:
        seconds = 7
        nanos = 123

    assert duration_json(Duration()) == {"seconds": 7, "nanos": 123}


def test_cloud_tasks_duration_rejects_unknown_shape():
    with pytest.raises(ExportError, match="Unsupported Cloud Tasks duration"):
        duration_json(object())


def test_cloud_tasks_enum_uses_semantic_name():
    from enum import IntEnum

    class State(IntEnum):
        RUNNING = 1

    assert str(State.RUNNING) == "1"
    assert enum_name(State.RUNNING) == "RUNNING"


def test_run_manifest_contract_projection_retains_lifecycle_evidence():
    document = {
        "schema_version": "1.0.0",
        "logical_run_key": "run_0123456789abcdef",
        "run_state": "SUCCEEDED",
        "state_version": 3,
        "invocation_fence": 1,
        "terminal_result_key": "run_0123456789abcdef",
    }
    assert contract_projection("run_manifests", document) == {
        "schema_version": "1.0.0",
        "logical_run_key": "run_0123456789abcdef",
    }


def test_run_manifest_contract_projection_rejects_unknown_fields():
    with pytest.raises(VerificationFailure, match="Unexpected persistence fields"):
        contract_projection("run_manifests", {"schema_version": "1.0.0", "unexpected": True})
