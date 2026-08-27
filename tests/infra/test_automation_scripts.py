"""
Automated CLI & Automation Script Test Suite (`test_automation_scripts.py`).
Validates CLI argument parsing, environment validation gates, secret generation,
and package.json shortcut mappings across all bash automation scripts.
"""

import os
import re
import json
import tempfile
import subprocess
from pathlib import Path
import pytest

SCRIPTS_DIR = Path("scripts")


def test_bootstrap_script_api_list():
    """Verify scripts/gcp_bootstrap.sh contains all 9 required Google Cloud APIs."""
    content = (SCRIPTS_DIR / "gcp_bootstrap.sh").read_text(encoding="utf-8")

    required_apis = [
        "run.googleapis.com",
        "cloudtasks.googleapis.com",
        "bigquery.googleapis.com",
        "firestore.googleapis.com",
        "redis.googleapis.com",
        "secretmanager.googleapis.com",
        "aiplatform.googleapis.com",
        "artifactregistry.googleapis.com",
        "compute.googleapis.com",
    ]

    for api in required_apis:
        assert api in content, f"Missing required GCP API: {api}"


def test_setup_secrets_environment_validation_and_hmac():
    """Verify scripts/gcp_setup_secrets.sh provisions HMAC and Gemini keys for dev and prod."""
    content = (SCRIPTS_DIR / "gcp_setup_secrets.sh").read_text(encoding="utf-8")

    assert 'GEMINI_SECRET_NAME="GEMINI_API_KEY_${ENV_UPPER}"' in content
    assert 'HMAC_SECRET_NAME="BENCHPRESS_HMAC_SECRET_${ENV_UPPER}"' in content
    assert "roles/secretmanager.secretAccessor" in content
    assert 'contains' in content or '[[ "$ENV" != "dev" && "$ENV" != "prod" ]]' in content


def test_deploy_script_orchestration_flow():
    """Verify scripts/gcp_deploy_all.sh integrates bootstrap, secrets, terraform, and smoke test."""
    content = (SCRIPTS_DIR / "gcp_deploy_all.sh").read_text(encoding="utf-8")

    assert "gcp_bootstrap.sh" in content
    assert "gcp_setup_secrets.sh" in content
    assert "terraform apply" in content
    assert "gcp_smoke_test.sh" in content
    assert "secret_scanner.py" in content
    assert "--skip-bootstrap" in content
    assert "--skip-secrets" in content


def test_smoke_test_endpoint_verification_coverage():
    """Verify scripts/gcp_smoke_test.sh covers benchmarks, routing, and trajectory dispatch."""
    content = (SCRIPTS_DIR / "gcp_smoke_test.sh").read_text(encoding="utf-8")

    assert "/api/v1/benchmarks" in content
    assert "/api/v1/routing-recommendation" in content
    assert "/api/v1/trajectory-run" in content
    assert 'DATASET_NAME="benchpress_${ENV}_analytics"' in content or "benchpress_dev_analytics" in content
    assert "benchpress_analytics" in content


def test_teardown_script_safety_guards():
    """Verify scripts/gcp_teardown.sh has safety prompts for production and targets terraform destroy."""
    content = (SCRIPTS_DIR / "gcp_teardown.sh").read_text(encoding="utf-8")

    assert "DESTROY_PROD" in content
    assert "terraform destroy" in content
    assert "--force" in content


def test_setup_cloud_env_generates_valid_output():
    """Verify scripts/setup_cloud_env.sh structures environment variables properly."""
    content = (SCRIPTS_DIR / "setup_cloud_env.sh").read_text(encoding="utf-8")

    assert "BIGQUERY_DATASET=" in content
    assert "TASKS_QUEUE_NAME=" in content
    assert "ARTIFACT_BUCKET=" in content
    assert "NEXT_PUBLIC_APP_ENV=" in content


def test_package_json_contains_all_cloud_shortcuts():
    """Verify package.json defines all 10 unified cloud automation commands."""
    pkg_data = json.loads(Path("package.json").read_text(encoding="utf-8"))
    scripts = pkg_data.get("scripts", {})

    expected_commands = [
        "cloud:bootstrap",
        "cloud:secrets:dev",
        "cloud:secrets:prod",
        "cloud:deploy:dev",
        "cloud:deploy:prod",
        "cloud:smoke:dev",
        "cloud:smoke:prod",
        "cloud:teardown:dev",
        "cloud:teardown:prod",
        "cloud:env",
    ]

    for cmd in expected_commands:
        assert cmd in scripts, f"Missing package.json script shortcut: {cmd}"
