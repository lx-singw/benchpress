"""
Canary Verification, Promotion & Rollback Lifecycle Tests (IMP-06).
"""

import pytest
from contracts.models import Aggregate, CanaryResult, PolicyVersion
from contracts.states import PublicDecision, InternalOutcome, TruthClass, UncertaintyMethod
from policy.repository import PolicyRepository
from policy.promotion import PolicyPromotionService
from policy.rollback import PolicyRollbackService


@pytest.fixture
def policy_setup():
    repo = PolicyRepository()
    segment = "swe_coding_python_interactive"
    base_policy_ver = "pol_01J6G7R8Q9ABCDEFGHJKMNPQ10"
    cand_policy_ver = "pol_01J6G7R8Q9ABCDEFGHJKMNPQ11"

    cand_policy = PolicyVersion(
        schema_version="1.0.0",
        policy_version=cand_policy_ver,
        task_segment_id=segment,
        configuration_id="cfg_4f1b82d3e9a0c784",
        is_active=False,
        state_version=1,
        created_at="2026-08-29T10:00:00.000Z",
    )
    repo.store_policy_version(cand_policy)

    base_agg = Aggregate(
        schema_version="1.0.0",
        aggregate_id="agg_0123456789abcdef",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id="cfg_948a3f81e3a1b029",
        aggregation_policy_version="agg_pol_v1",
        eligible_run_keys=["run_0123456789abcdef", "run_fedcba9876543210"],
        ineligible_run_keys=[],
        total_attempts=2,
        resolved_count=2,
        failed_count=0,
        pass_rate=1.0,
        total_cost_usd="0.020000",
        cpr_usd="0.010000",
        mean_latency_ms=1200,
        p95_latency_ms=1400,
        uncertainty_method=UncertaintyMethod.WILSON_SCORE,
        pass_rate_lower_bound=0.8,
        pass_rate_upper_bound=1.0,
        evidence_sufficient=True,
        quality_floor_breached=False,
        created_at="2026-08-29T10:00:00.000Z",
    )

    cand_agg = Aggregate(
        schema_version="1.0.0",
        aggregate_id="agg_fedcba9876543210",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id="cfg_4f1b82d3e9a0c784",
        aggregation_policy_version="agg_pol_v1",
        eligible_run_keys=["run_1122334455667788", "run_8877665544332211"],
        ineligible_run_keys=[],
        total_attempts=2,
        resolved_count=2,
        failed_count=0,
        pass_rate=1.0,
        total_cost_usd="0.008000",
        cpr_usd="0.004000",
        mean_latency_ms=1100,
        p95_latency_ms=1300,
        uncertainty_method=UncertaintyMethod.WILSON_SCORE,
        pass_rate_lower_bound=0.8,
        pass_rate_upper_bound=1.0,
        evidence_sufficient=True,
        quality_floor_breached=False,
        created_at="2026-08-29T10:00:00.000Z",
    )

    return {
        "repo": repo,
        "segment": segment,
        "base_ver": base_policy_ver,
        "cand_ver": cand_policy_ver,
        "base_agg": base_agg,
        "cand_agg": cand_agg,
    }


def test_atomic_cas_promotion_on_passing_canary(policy_setup):
    """Verify that passing canary atomically promotes policy and mints SWITCH receipt."""
    repo = policy_setup["repo"]
    promotion_service = PolicyPromotionService(repo=repo)

    canary_res = CanaryResult(
        schema_version="1.0.0",
        canary_id="cnry_01J6G7R8Q9ABCDEFGHJKMNPQ40",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        baseline_policy_version=policy_setup["base_ver"],
        candidate_policy_version=policy_setup["cand_ver"],
        canary_task_ids=["TASK-001"],
        baseline_run_keys=["run_0123456789abcdef"],
        candidate_run_keys=["run_1122334455667788"],
        candidate_passed=True,
        guardrails_evaluated=["QUALITY", "LATENCY"],
        guardrails_breached=[],
        promotion_approved=True,
        rollback_triggered=False,
        evaluated_at="2026-08-29T10:00:00.000Z",
        created_at="2026-08-29T10:00:00.000Z",
    )

    receipt = promotion_service.promote_candidate(
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        task_segment_id=policy_setup["segment"],
        baseline_policy_version=policy_setup["base_ver"],
        candidate_policy_version=policy_setup["cand_ver"],
        baseline_config_id="cfg_948a3f81e3a1b029",
        candidate_config_id="cfg_4f1b82d3e9a0c784",
        baseline_agg=policy_setup["base_agg"],
        candidate_agg=policy_setup["cand_agg"],
        canary_res=canary_res,
    )

    assert receipt.public_decision == PublicDecision.SWITCH
    assert receipt.internal_outcome == InternalOutcome.SWITCH_RECOMMENDED or receipt.internal_outcome == InternalOutcome.SUFFICIENT_CANDIDATE if hasattr(InternalOutcome, "SUFFICIENT_CANDIDATE") else receipt.internal_outcome == InternalOutcome.SWITCH_RECOMMENDED
    assert receipt.receipt_id.startswith("rcpt_")

    # Verify pointer in repository updated
    active = repo.get_active_policy(policy_setup["segment"])
    assert active.policy_version == policy_setup["cand_ver"]
    assert active.is_active is True


def test_rollback_on_failing_canary(policy_setup):
    """Verify that failing canary retains baseline and mints STAY receipt."""
    repo = policy_setup["repo"]
    rollback_service = PolicyRollbackService()

    canary_res = CanaryResult(
        schema_version="1.0.0",
        canary_id="cnry_01J6G7R8Q9ABCDEFGHJKMNPQ41",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        baseline_policy_version=policy_setup["base_ver"],
        candidate_policy_version=policy_setup["cand_ver"],
        canary_task_ids=["TASK-001"],
        baseline_run_keys=["run_0123456789abcdef"],
        candidate_run_keys=["run_1122334455667788"],
        candidate_passed=False,
        guardrails_evaluated=["QUALITY", "LATENCY"],
        guardrails_breached=["QUALITY"],
        promotion_approved=False,
        rollback_triggered=True,
        rollback_reason="Canary failed quality assertions",
        evaluated_at="2026-08-29T10:00:00.000Z",
        created_at="2026-08-29T10:00:00.000Z",
    )

    receipt = rollback_service.execute_rollback(
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        task_segment_id=policy_setup["segment"],
        baseline_policy_version=policy_setup["base_ver"],
        candidate_policy_version=policy_setup["cand_ver"],
        baseline_config_id="cfg_948a3f81e3a1b029",
        candidate_config_id="cfg_4f1b82d3e9a0c784",
        baseline_agg=policy_setup["base_agg"],
        candidate_agg=policy_setup["cand_agg"],
        canary_res=canary_res,
        rollback_reason=canary_res.rollback_reason,
    )

    assert receipt.public_decision == PublicDecision.STAY
    assert receipt.internal_outcome == InternalOutcome.STAY_BASELINE_SUPERIOR or receipt.internal_outcome == InternalOutcome.CANARY_ROLLED_BACK
    assert receipt.receipt_id.startswith("rcpt_")

    # Verify baseline is still active
    active = repo.get_active_policy(policy_setup["segment"])
    assert active.policy_version == policy_setup["base_ver"]


def test_cas_concurrency_conflict(policy_setup):
    """Verify stale CAS attempt raises exception without corrupting pointer."""
    repo = policy_setup["repo"]
    promotion_service = PolicyPromotionService(repo=repo)

    canary_res = CanaryResult(
        schema_version="1.0.0",
        canary_id="cnry_01J6G7R8Q9ABCDEFGHJKMNPQ42",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        baseline_policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ99",
        candidate_policy_version=policy_setup["cand_ver"],
        canary_task_ids=["TASK-001"],
        baseline_run_keys=["run_0123456789abcdef"],
        candidate_run_keys=["run_1122334455667788"],
        candidate_passed=True,
        guardrails_evaluated=["QUALITY"],
        guardrails_breached=[],
        promotion_approved=True,
        rollback_triggered=False,
        evaluated_at="2026-08-29T10:00:00.000Z",
        created_at="2026-08-29T10:00:00.000Z",
    )

    with pytest.raises(RuntimeError, match="CAS policy promotion conflict"):
        promotion_service.promote_candidate(
            experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
            correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
            task_segment_id=policy_setup["segment"],
            baseline_policy_version="pol_01J6G7R8Q9ABCDEFGHJKMNPQ99",
            candidate_policy_version=policy_setup["cand_ver"],
            baseline_config_id="cfg_948a3f81e3a1b029",
            candidate_config_id="cfg_4f1b82d3e9a0c784",
            baseline_agg=policy_setup["base_agg"],
            candidate_agg=policy_setup["cand_agg"],
            canary_res=canary_res,
        )
