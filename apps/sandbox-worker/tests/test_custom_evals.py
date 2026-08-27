"""
Enterprise Custom Evaluation Ingestor Test Suite.
Verifies YAML manifest parsing, task synthesis, and sandbox context preparation.
"""

import pytest
from src.evals.custom_eval_synthesizer import CustomEvalSynthesizer, CustomEvalTask


SAMPLE_ENTERPRISE_YAML = """
suite_name: "acme_fintech_core_v1"
version: "2.1.0"
organization: "Acme Corp Financial Services"
tasks:
  - task_id: "acme-recon-4402"
    repo_url: "git@github.com:acme-corp/settlement-engine.git"
    base_commit: "9f8e7d6c5b4a"
    issue_description: "Fix rounding anomaly in multi-currency FX settlement batches."
    test_command: "pytest tests/test_settlement_fx.py -k test_rounding_precision"
    setup_commands:
      - "pip install -r requirements-enterprise.txt"
    budget_limit_usd: 0.75
    max_turns: 15
    environment_variables:
      SETTLEMENT_ENV: "sandbox"
"""


def test_custom_eval_manifest_parsing():
    """Verify CustomEvalSynthesizer correctly parses declarative YAML manifests."""
    manifest = CustomEvalSynthesizer.parse_manifest_yaml(SAMPLE_ENTERPRISE_YAML)
    assert manifest.suite_name == "acme_fintech_core_v1"
    assert manifest.organization == "Acme Corp Financial Services"
    assert len(manifest.tasks) == 1

    task = manifest.tasks[0]
    assert task.task_id == "acme-recon-4402"
    assert task.budget_limit_usd == 0.75
    assert task.max_turns == 15
    assert "pytest tests/test_settlement_fx.py" in task.test_command


def test_custom_eval_task_synthesis():
    """Verify task context synthesis generates executable payload for AsyncFSMRunner."""
    manifest = CustomEvalSynthesizer.parse_manifest_yaml(SAMPLE_ENTERPRISE_YAML)
    task = manifest.tasks[0]
    ctx = CustomEvalSynthesizer.synthesize_task_execution_context(task)

    assert ctx["task_id"] == "acme-recon-4402"
    assert ctx["task_suite"] == "CUSTOM_ENTERPRISE"
    assert ctx["test_cmd"] == task.test_command
    assert ctx["budget_limit_usd"] == 0.75
    assert ctx["env"]["SETTLEMENT_ENV"] == "sandbox"
