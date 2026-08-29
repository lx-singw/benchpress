"""
Manifest and Frozen Judged Cohort Validation Tests (IMP-00).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
scripts_dir = REPO_ROOT / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from validate_demo_manifest import validate_task_cohort, validate_demo_manifest, compute_file_sha256


def test_judged_task_cohort_manifest():
    """Verify that judged_task_cohort.v1.json has valid task hashes and existing files."""
    cohort_path = REPO_ROOT / "tests" / "fixtures" / "manifests" / "judged_task_cohort.v1.json"
    cohort = validate_task_cohort(cohort_path)
    assert cohort["cohort_id"] == "cohort_swe_judged_v1"
    assert len(cohort["tasks"]) == 4
    
    task_ids = {t["task_id"] for t in cohort["tasks"]}
    assert task_ids == {"TASK-001", "TASK-002", "TASK-003", "TASK-004"}


def test_demo_manifest():
    """Verify that demo-manifest.yaml is valid, has correct baseline and candidate configs."""
    manifest_path = REPO_ROOT / "docs" / "hackathon" / "demo-manifest.yaml"
    result = validate_demo_manifest(manifest_path)
    assert result["valid"] is True
    assert len(result["manifest_hash"]) == 64
