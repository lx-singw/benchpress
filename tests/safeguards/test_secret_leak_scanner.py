"""
Test Suite for Safeguard 5: Zero-Secret Leakage High-Entropy Pre-Commit Armor.
"""

import tempfile
from pathlib import Path
import pytest
from scripts.secret_scanner import scan_file, PATTERNS


def test_secret_scanner_detects_google_api_key():
    """Verify that Google Cloud API keys are flagged by the scanner."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write('API_KEY = "AIzaSyD9x8_FakeSecretKeyTestForScanner12345"\n')
        f_path = Path(f.name)

    try:
        violations = scan_file(f_path)
        assert len(violations) >= 1
        assert "Google Cloud API Key" in violations[0][1]
    finally:
        f_path.unlink(missing_ok=True)


def test_secret_scanner_detects_service_account_json():
    """Verify that raw GCP Service Account private key JSONs are flagged."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write('{\n  "type": "service_account",\n  "project_id": "benchpress-prod"\n}\n')
        f_path = Path(f.name)

    try:
        violations = scan_file(f_path)
        assert len(violations) >= 1
        assert "GCP Service Account" in violations[0][1]
    finally:
        f_path.unlink(missing_ok=True)


def test_secret_scanner_detects_github_pat():
    """Verify that GitHub Personal Access Tokens are flagged."""
    with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as f:
        f.write('const token = "ghp_1234567890abcdef1234567890abcdef1234";\n')
        f_path = Path(f.name)

    try:
        violations = scan_file(f_path)
        assert len(violations) >= 1
        assert "GitHub Personal Access Token" in violations[0][1]
    finally:
        f_path.unlink(missing_ok=True)


def test_secret_scanner_passes_clean_source_code():
    """Verify that standard clean source code produces zero false positives."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write('def calculate_cpr(total_cost: float, pass_at_1: bool) -> float:\n    return total_cost if pass_at_1 else total_cost * 2.0\n')
        f_path = Path(f.name)

    try:
        violations = scan_file(f_path)
        assert len(violations) == 0
    finally:
        f_path.unlink(missing_ok=True)
