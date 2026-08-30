"""
Plan Policy Deterministic Approval Gate Tests (IMP-02).
"""

import copy
import pytest
from orchestrator.plan_policy import PlanPolicyValidator
from orchestrator.tools import OrchestratorToolRegistry


@pytest.fixture
def valid_plan_dict():
    registry = OrchestratorToolRegistry()
    ce = registry.get_change_event("evt_01J6G7R8Q9ABCDEFGHJKMNPQ01")
    return {
        "schema_version": "1.0.0",
        "plan_id": "plan_9f8e7d6c5b4a3210",
        "experiment_id": "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        "correlation_id": "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        "event_id": "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
        "fingerprint_id": "fp_1a2b3c4d5e6f7a8b",
        "baseline_configuration_id": ce["baseline_configuration_id"],
        "candidate_configuration_ids": ["cfg_4f1b82d3e9a0c784"],
        "task_cohort_version": "cohort_swe_judged_v1",
        "selected_task_ids": ["TASK-001", "TASK-002"],
        "repetitions_per_task": 1,
        "max_matrix_spend_usd": "0.500000",
        "reserved_budget_usd": "0.500000",
        "per_run_timeout_seconds": 60,
        "max_turns_per_run": 15,
        "quality_floor_pass_rate": 0.75,
        "early_stop_consecutive_failures": 2,
        "planner_model": "gemini-2.5-pro",
        "plan_policy_version": "plan_pol_v1_taskmaster",
        "planning_rationale": "Valid plan testing policy approval gate",
        "created_at": "2026-08-29T10:00:20.000Z",
    }


def test_plan_policy_valid_approval(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {"baseline_configuration_id": "cfg_948a3f81e3a1b029", "max_spend_usd": "2.500000"}

    result = validator.evaluate_plan(valid_plan_dict, event_dict)
    assert result.approved is True
    assert result.plan_hash is not None
    assert len(result.plan_hash) == 64


def test_plan_policy_missing_baseline(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {"baseline_configuration_id": "cfg_948a3f81e3a1b029", "max_spend_usd": "2.500000"}

    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["baseline_configuration_id"] = "cfg_4f1b82d3e9a0c784" # Swapped

    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("baseline" in r.lower() for r in result.reasons)


def test_plan_policy_exceeds_budget(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {"baseline_configuration_id": "cfg_948a3f81e3a1b029", "max_spend_usd": "0.200000"}

    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["max_matrix_spend_usd"] = "0.500000" # Exceeds 0.20

    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("exceeds event limit" in r for r in result.reasons)


def test_plan_policy_unregistered_candidate(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {"baseline_configuration_id": "cfg_948a3f81e3a1b029", "max_spend_usd": "2.500000"}

    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["candidate_configuration_ids"] = ["cfg_0000000000000000"]

    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("Unregistered candidate configuration" in r for r in result.reasons)


def test_plan_policy_rejects_multiple_candidates(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {
        "baseline_configuration_id": "cfg_948a3f81e3a1b029",
        "max_spend_usd": "2.500000",
    }
    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["candidate_configuration_ids"] = [
        "cfg_4f1b82d3e9a0c784",
        "cfg_7c2a93e4f1b80d19",
    ]

    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("exactly 1 candidate" in reason for reason in result.reasons)


def test_plan_policy_resolves_nonlocal_configuration_registry(valid_plan_dict):
    class Repository:
        def get_configuration(self, configuration_id):
            return object() if configuration_id in {
                "cfg_948a3f81e3a1b029",
                "cfg_4f1b82d3e9a0c784",
            } else None

    validator = PlanPolicyValidator(configuration_repository=Repository())
    event_dict = {
        "baseline_configuration_id": "cfg_948a3f81e3a1b029",
        "max_spend_usd": "2.500000",
    }

    assert validator.evaluate_plan(valid_plan_dict, event_dict).approved is True

    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["candidate_configuration_ids"] = ["cfg_0000000000000000"]
    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("Unregistered candidate configuration" in reason for reason in result.reasons)


def test_plan_policy_unrecognized_task(valid_plan_dict):
    validator = PlanPolicyValidator()
    event_dict = {"baseline_configuration_id": "cfg_948a3f81e3a1b029", "max_spend_usd": "2.500000"}

    bad_plan = copy.deepcopy(valid_plan_dict)
    bad_plan["selected_task_ids"] = ["TASK-999_UNAUTHORIZED"]

    result = validator.evaluate_plan(bad_plan, event_dict)
    assert result.approved is False
    assert any("Unrecognized task" in r for r in result.reasons)
