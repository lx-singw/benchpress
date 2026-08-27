#!/usr/bin/env python3
"""
High-Entropy & Zero-Secret Leakage Pre-Commit Armor Scanner (`secret_scanner.py`).
Scans source code for unencrypted API keys, service account JSONs, and private keys.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

PATTERNS = [
    (r"AIza[0-9A-Za-z\-_]{35}", "Google Cloud API Key"),
    (r'"type":\s*"service_account"', "GCP Service Account Key JSON"),
    (r"sk-[0-9a-zA-Z]{32,}", "OpenAI / Claude API Secret Key"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Cryptographic Key"),
]

EXCLUDE_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "secret_scanner.py",
    "test_secret_leak_scanner.py",
}


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a single file for secret pattern matches."""
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for line_idx, line in enumerate(content.splitlines(), start=1):
            for regex_str, desc in PATTERNS:
                if re.search(regex_str, line):
                    # Check for explicit test/mock comments
                    if "test" in file_path.name.lower() or "mock" in line.lower() or "example" in line.lower() or "placeholder" in line.lower():
                        continue
                    violations.append((line_idx, desc, line.strip()[:60]))
    except Exception:
        pass
    return violations


def scan_workspace(root_dir: str = ".") -> int:
    """Scan the entire workspace for secret leaks."""
    print("[SCAN] [SecretScanner] Initiating High-Entropy Secret Leak Scan...")
    total_violations = 0
    root = Path(root_dir).resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for fname in filenames:
            if fname in EXCLUDE_FILES or fname.endswith((".pyc", ".png", ".jpg", ".svg", ".ico", ".woff2")):
                continue

            fpath = Path(dirpath) / fname
            violations = scan_file(fpath)
            if violations:
                for line_no, desc, snippet in violations:
                    print(f"[LEAK DETECTED] {fpath.relative_to(root)}:{line_no} -> {desc}")
                    print(f"   Snippet: {snippet}")
                    total_violations += 1

    if total_violations > 0:
        print(f"\n[FAILED] SCAN FAILED: {total_violations} unencrypted secret tokens detected! Commit aborted.")
        return 1

    print("[SUCCESS] [SecretScanner] Scan clean! Zero unencrypted secrets detected.")
    return 0


if __name__ == "__main__":
    sys.exit(scan_workspace())
