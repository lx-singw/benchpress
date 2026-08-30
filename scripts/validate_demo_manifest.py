#!/usr/bin/env python3
"""
Benchpress Demo Manifest & Cohort Validator (IMP-00).
Verifies frozen demo-manifest.yaml and judged_task_cohort.v1.json integrity and fixture checksums without external provider calls.
"""

import sys
import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_simple_yaml(text: str) -> dict:
    """Simple parser for YAML without requiring third-party library if PyYAML is not in system path."""
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        # Minimalist fallback parser for our manifest structure if yaml is absent
        import json
        import re
        # Convert simple key-value YAML lines to JSON dictionary
        # If PyYAML is available, safe_load is used.
        raise RuntimeError("PyYAML required for full YAML parsing. Install pyyaml or run in project venv.")


def validate_task_cohort(cohort_path: Path) -> dict:
    if not cohort_path.exists():
        raise FileNotFoundError(f"Cohort manifest not found: {cohort_path}")
    
    with open(cohort_path, "r", encoding="utf-8") as f:
        cohort = json.load(f)

    assert cohort.get("schema_version") == "1.0.0", "Invalid cohort schema_version"
    assert "tasks" in cohort and len(cohort["tasks"]) >= 4, "Cohort must contain at least 4 tasks"

    for task in cohort["tasks"]:
        task_id = task["task_id"]
        task_dir = REPO_ROOT / "tests" / "fixtures" / "tasks" / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"Task fixture directory missing: {task_dir}")
        
        # Verify files inside task dir
        files = sorted([f for f in task_dir.iterdir() if f.is_file()])
        hasher = hashlib.sha256()
        for f in files:
            hasher.update(f.read_bytes())
        actual_hash = hasher.hexdigest()
        expected_hash = task["task_version_hash"]
        if actual_hash != expected_hash:
            raise ValueError(f"Task {task_id} checksum mismatch! Expected: {expected_hash}, Actual: {actual_hash}")

    return cohort


def validate_demo_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Demo manifest not found: {manifest_path}")

    raw_text = manifest_path.read_text(encoding="utf-8")
    manifest_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    # Parse YAML
    try:
        import yaml
        data = yaml.safe_load(raw_text)
    except ImportError:
        # Fallback: check required keys in text
        data = {}
        for key in ["schema_version", "replay_event", "baseline_policy", "candidate_configurations", "judged_task_cohort", "finops_budget"]:
            assert key in raw_text, f"Missing required key '{key}' in {manifest_path}"
        print("Note: PyYAML not installed in current environment; basic text validation passed.")
        return {"manifest_hash": manifest_hash, "valid": True}

    assert data.get("schema_version") == "1.0.0"
    assert data.get("truth_class") == "DEMO_FIXTURE", "Demo manifest must never be classified as measured"
    assert "replay_event" in data
    assert "baseline_policy" in data
    assert len(data.get("candidate_configurations", [])) >= 2
    assert "finops_budget" in data
    assert "decision_rules" in data

    # Verify task cohort reference
    cohort_rel = data["judged_task_cohort"]["manifest_path"]
    cohort_path = REPO_ROOT / cohort_rel
    validate_task_cohort(cohort_path)

    return {"manifest_hash": manifest_hash, "data": data, "valid": True}


def main():
    manifest_path = REPO_ROOT / "docs" / "hackathon" / "demo-manifest.yaml"
    cohort_path = REPO_ROOT / "tests" / "fixtures" / "manifests" / "judged_task_cohort.v1.json"

    print("=" * 60)
    print("Validating Judged Task Cohort Manifest...")
    cohort = validate_task_cohort(cohort_path)
    cohort_hash = compute_file_sha256(cohort_path)
    print(f"✅ Cohort Validated ({len(cohort['tasks'])} tasks). SHA-256: {cohort_hash}")

    print("Validating Demo Manifest...")
    result = validate_demo_manifest(manifest_path)
    print(f"✅ Demo Manifest Validated. SHA-256: {result['manifest_hash']}")
    print("=" * 60)
    print("All manifests and task fixtures verified successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
