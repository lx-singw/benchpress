"""
Task Fixture Loader & Integrity Verifier.
Unpacks task cohort files into isolated sandbox worktrees with SHA-256 checksum validation.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
TASKS_FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "tasks"
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "manifests" / "judged_task_cohort.v1.json"


class TaskFixtureLoader:
    """Loads and verifies immutable task cohort files into sandboxed workspaces."""

    def __init__(self, manifest_path: Path = MANIFEST_PATH):
        self.manifest_path = manifest_path
        self.manifest_data = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {}
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def unpack_task(self, task_id: str, destination_dir: Path) -> List[str]:
        """Copy task fixture files to destination directory and verify checksums."""
        source_dir = TASKS_FIXTURES_DIR / task_id
        if not source_dir.exists():
            raise FileNotFoundError(f"Task fixture directory for '{task_id}' not found at {source_dir}")

        destination_dir.mkdir(parents=True, exist_ok=True)
        unpacked_files = []

        # Find task checksums in manifest
        expected_checksums = {}
        for t in self.manifest_data.get("tasks", []):
            if t["task_id"] == task_id:
                expected_checksums = t.get("file_checksums", {})
                break

        for item in source_dir.iterdir():
            if item.is_file():
                dest_file = destination_dir / item.name
                shutil.copy2(item, dest_file)

                # Verify SHA-256 checksum
                with open(dest_file, "rb") as f:
                    actual_sha = hashlib.sha256(f.read()).hexdigest()

                if item.name in expected_checksums:
                    expected_sha = expected_checksums[item.name]
                    if actual_sha != expected_sha:
                        raise ValueError(
                            f"Checksum mismatch for {item.name} in task {task_id}: "
                            f"expected {expected_sha}, got {actual_sha}"
                        )

                unpacked_files.append(item.name)

        return unpacked_files
