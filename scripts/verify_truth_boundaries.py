#!/usr/bin/env python3
"""Fail when fixture artifacts are mislabeled or synthetic evidence enters measured bundles."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    errors: list[str] = []
    fixture_manifest = json.loads((ROOT / "evidence" / "fixture-manifest.json").read_text(encoding="utf-8"))
    if fixture_manifest.get("truth_status") != "DEMO_FIXTURE":
        errors.append("evidence/fixture-manifest.json must be DEMO_FIXTURE")
    for relative in fixture_manifest.get("files", []):
        path = ROOT / "evidence" / relative
        if not path.is_file():
            errors.append(f"Fixture manifest references missing file: {relative}")
            continue
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            serialized = json.dumps(payload)
            if "BENCHPRESS_MEASURED" in serialized:
                errors.append(f"Fixture artifact contains measured classification: {relative}")
    runs = ROOT / "evidence" / "runs"
    if runs.exists():
        for manifest_path in runs.glob("*/manifest.json"):
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if payload.get("truth_class") != "BENCHPRESS_MEASURED":
                errors.append(f"Measured run directory has invalid truth class: {manifest_path}")
            if "DEMO_FIXTURE" in json.dumps(payload):
                errors.append(f"Measured run manifest references a fixture: {manifest_path}")
    for path in (ROOT / "docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "**Status:** Approved / Production" in text:
            errors.append(f"Legacy document claims production status: {path.relative_to(ROOT)}")
    for name in [
        "01-cost-per-resolution-whitepaper.md",
        "02-hybrid-routing-pareto-study.md",
        "03-trajectory-bloat-and-context-rot.md",
    ]:
        path = ROOT / "docs" / "research" / name
        if "Evidence disposition" not in path.read_text(encoding="utf-8"):
            errors.append(f"Historical research lacks an evidence warning: {path.relative_to(ROOT)}")
    smoke_script = (ROOT / "scripts" / "gcp_smoke_test.sh").read_text(encoding="utf-8")
    for forbidden in ["mock.a.run.app", "100% healthy", "|| echo \"200\"", "|| echo \"202\""]:
        if forbidden in smoke_script:
            errors.append(f"Cloud smoke test contains a synthetic success path: {forbidden}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Truth/provenance boundaries verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
