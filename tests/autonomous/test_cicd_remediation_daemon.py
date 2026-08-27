"""
Autonomous CI/CD Remediation Daemon Test Suite.
Verifies automated crash ingestion, 2-tier hybrid resolution, and PR generation with CPR telemetry.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))

from src.daemon.cicd_remediator import CiCdRemediator


def test_cicd_remediation_daemon_generates_pr():
    """Verify CiCdRemediator produces a verified PR with CPR economic report upon CI crash."""
    mock_ci_error_log = (
        "============================= FAILURES =============================\n"
        "___________________ test_regex_validator_trailing __________________\n"
        "django/core/validators.py:19: ValidationError: Enter a valid value.\n"
        "AssertionError: regex did not anchor to string end (\\A ... \\Z)\n"
    )

    res = CiCdRemediator.remediate_ci_failure(
        repo_name="enterprise/django-app",
        commit_sha="e8f4a1c2b3d9",
        error_log=mock_ci_error_log,
        failing_file="django/core/validators.py",
    )

    assert res.status == "RESOLVED"
    assert "benchpress/auto-fix-e8f4a1c" in res.pr_branch
    assert "[BENCHPRESS-AUTO]" in res.pr_title
    assert "87.5% Reduction" in res.pr_body or "Reduction" in res.pr_body
    assert res.cpr_cost_usd == 0.185
    assert res.baseline_cost_usd == 1.480
    assert "regex" in res.diff_patch
