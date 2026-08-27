"""
Infrastructure Unit & Schema Test Suite (`test_terraform_environments.py`).
Validates Dev ($0/mo scale-to-zero) vs. Prod (Pre-warmed HA) Terraform configurations,
HCL variable validations, dataset isolation, and CLI deployment scripts.
"""

import os
import re
from pathlib import Path
import pytest

TERRAFORM_DIR = Path("infra/terraform")
ENVIRONMENTS_DIR = TERRAFORM_DIR / "environments"


def parse_tfvars(tfvars_path: Path) -> dict:
    """Simple HCL tfvars parser extracting key-value pairs."""
    data = {}
    content = tfvars_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.isdigit():
                val = int(val)
            data[key] = val
    return data


def test_dev_environment_scale_to_zero_invariants():
    """Verify dev.tfvars enforces $0/month scale-to-zero compute and minimal Redis/Task limits."""
    dev_vars = parse_tfvars(ENVIRONMENTS_DIR / "dev.tfvars")

    assert dev_vars["environment"] == "dev"
    assert dev_vars["web_min_instances"] == 0, "Dev web must scale to zero (min=0)"
    assert dev_vars["worker_min_instances"] == 0, "Dev worker must scale to zero (min=0)"
    assert dev_vars["web_max_instances"] <= 5
    assert dev_vars["worker_max_instances"] <= 10
    assert dev_vars["redis_tier"] == "BASIC"
    assert dev_vars["redis_memory_size_gb"] == 1
    assert dev_vars["cloud_tasks_dispatch_rate"] == 10
    assert dev_vars["cloud_tasks_max_concurrent"] == 5


def test_prod_environment_pre_warmed_ha_invariants():
    """Verify prod.tfvars enforces pre-warmed high-availability compute and multi-zone Redis."""
    prod_vars = parse_tfvars(ENVIRONMENTS_DIR / "prod.tfvars")

    assert prod_vars["environment"] == "prod"
    assert prod_vars["web_min_instances"] >= 1, "Prod web must be pre-warmed (min>=1)"
    assert prod_vars["worker_min_instances"] >= 2, "Prod worker must be pre-warmed for instant execution (min>=2)"
    assert prod_vars["web_max_instances"] >= 20
    assert prod_vars["worker_max_instances"] >= 100
    assert prod_vars["redis_tier"] == "STANDARD_HA"
    assert prod_vars["redis_memory_size_gb"] >= 5
    assert prod_vars["cloud_tasks_dispatch_rate"] >= 500
    assert prod_vars["cloud_tasks_max_concurrent"] >= 50


def test_variables_hcl_schema_validations():
    """Verify variables.tf has strict validation blocks for environment and redis_tier."""
    vars_content = (TERRAFORM_DIR / "variables.tf").read_text(encoding="utf-8")

    # Check environment validation
    assert 'variable "environment"' in vars_content
    assert 'contains(["dev", "prod"], var.environment)' in vars_content

    # Check redis_tier validation
    assert 'variable "redis_tier"' in vars_content
    assert 'contains(["BASIC", "STANDARD_HA"], var.redis_tier)' in vars_content


def test_cloud_run_environment_isolation_and_sizing():
    """Verify cloud_run.tf parameterizes service names, resource limits, and BigQuery datasets."""
    cr_content = (TERRAFORM_DIR / "cloud_run.tf").read_text(encoding="utf-8")

    assert 'name     = "benchpress-web-${var.environment}"' in cr_content
    assert 'name     = "benchpress-worker-${var.environment}"' in cr_content

    # Check dynamic CPU & Memory limits
    assert 'var.environment == "prod" ? "2" : "1"' in cr_content
    assert 'var.environment == "prod" ? "4Gi" : "2Gi"' in cr_content
    assert 'var.environment == "prod" ? "4" : "2"' in cr_content
    assert 'var.environment == "prod" ? "8Gi" : "4Gi"' in cr_content

    # Check BigQuery dataset injection
    assert 'var.environment == "prod" ? "benchpress_analytics" : "benchpress_dev_analytics"' in cr_content


def test_bigquery_dataset_isolation():
    """Verify bigquery.tf isolates dataset naming and sets partitioning & clustering."""
    bq_content = (TERRAFORM_DIR / "bigquery.tf").read_text(encoding="utf-8")

    assert 'var.environment == "prod" ? "benchpress_analytics" : "benchpress_dev_analytics"' in bq_content
    assert 'dataset_id                  = local.dataset_id' in bq_content
    assert 'table_id            = "trajectories"' in bq_content
    assert 'table_id            = "fsm_turns"' in bq_content
    assert 'clustering = ["model_id", "task_suite", "status"]' in bq_content


def test_deploy_script_env_flag_support():
    """Verify scripts/gcp_deploy_all.sh supports --env dev and --env prod cleanly."""
    deploy_script = Path("scripts/gcp_deploy_all.sh").read_text(encoding="utf-8")

    assert "--env" in deploy_script
    assert "environments/${ENV}.tfvars" in deploy_script
    assert "web:${ENV}" in deploy_script
    assert "sandbox-worker:${ENV}" in deploy_script
    assert "secret_scanner.py" in deploy_script


def test_package_json_cloud_scripts():
    """Verify root package.json exposes convenient pnpm/npm cloud commands."""
    import json
    pkg = json.loads(Path("package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})

    assert "cloud:deploy:dev" in scripts
    assert "cloud:deploy:prod" in scripts
    assert "cloud:smoke:dev" in scripts
    assert "cloud:smoke:prod" in scripts
    assert "cloud:teardown:dev" in scripts
    assert "cloud:teardown:prod" in scripts
