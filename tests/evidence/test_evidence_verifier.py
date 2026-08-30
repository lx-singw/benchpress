import hashlib
import json
import subprocess
import sys
from pathlib import Path


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
