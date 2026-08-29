"""
Failure-Inclusive Aggregation & Early Stopping Tests (IMP-05).
"""

from decimal import Decimal
import pytest
from contracts.models import RunResult
from contracts.states import LogicalRunState, FailureReason
from aggregation.aggregator import ConfigurationAggregator, calculate_wilson_score_interval
from aggregation.early_stopping import EarlyStoppingEvaluator, StopAction


def make_dummy_result(key_suffix: str, config_id: str, resolved: bool, cost_usd: str) -> RunResult:
    # Ensure key matches ^run_[a-f0-9]{16}$
    hex_suffix = (key_suffix.replace("_", "").replace("-", "") + "0000000000000000")[:16]
    run_key = f"run_{hex_suffix}"
    attempt_id = "att_01J6G7R8Q9ABCDEFGHJKMNPQ30"

    return RunResult(
        schema_version="1.0.0",
        logical_run_key=run_key,
        attempt_id=attempt_id,
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id=config_id,
        task_id="TASK-001",
        repetition_index=0,
        run_state=LogicalRunState.SUCCEEDED if resolved else LogicalRunState.FAILED_MODEL,
        resolved=resolved,
        failure_reason=FailureReason.NONE if resolved else FailureReason.ORACLE_ASSERTION_FAILED,
        turns_executed=2,
        prompt_tokens=500,
        completion_tokens=200,
        cached_tokens=0,
        total_tokens=700,
        observed_cost_usd=cost_usd,
        price_version="2026-08-29",
        latency_ms=1500,
        exit_code=0 if resolved else 1,
        assertions_passed=2 if resolved else 0,
        assertions_failed=0 if resolved else 1,
        eligible_for_aggregation=True,
        lease_owner="worker_1",
        started_at="2026-08-29T10:00:00.000Z",
        finished_at="2026-08-29T10:00:02.000Z",
        created_at="2026-08-29T10:00:02.000Z",
    )


def test_failure_inclusive_cpr_accounting():
    """Verify that failed runs are included in total cost and CPR denominator."""
    aggregator = ConfigurationAggregator()
    config_id = "cfg_4f1b82d3e9a0c784"
    runs = [
        make_dummy_result("1a", config_id, resolved=True, cost_usd="0.010000"),
        make_dummy_result("2b", config_id, resolved=False, cost_usd="0.020000"),
        make_dummy_result("3c", config_id, resolved=False, cost_usd="0.030000"),
    ]

    agg = aggregator.aggregate_runs(
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id=config_id,
        results=runs,
    )

    assert agg.total_attempts == 3
    assert agg.resolved_count == 1
    assert agg.failed_count == 2
    assert agg.pass_rate == 0.3333
    # Total cost = 0.01 + 0.02 + 0.03 = 0.060000
    assert agg.total_cost_usd == "0.060000"
    # CPR = 0.060000 / 1 = 0.060000
    assert agg.cpr_usd == "0.060000"


def test_zero_division_resilience():
    """Verify that 0 passing runs does not trigger ZeroDivisionError and sets safe fallback."""
    aggregator = ConfigurationAggregator()
    config_id = "cfg_4f1b82d3e9a0c784"
    runs = [
        make_dummy_result("1a", config_id, resolved=False, cost_usd="0.020000"),
        make_dummy_result("2b", config_id, resolved=False, cost_usd="0.030000"),
    ]

    agg = aggregator.aggregate_runs(
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id=config_id,
        results=runs,
    )

    assert agg.resolved_count == 0
    assert agg.cpr_usd == "0.000000"
    assert agg.evidence_sufficient is False


def test_early_stopping_consecutive_failures():
    """Verify early stopping triggers on consecutive failures."""
    evaluator = EarlyStoppingEvaluator()
    config_id = "cfg_4f1b82d3e9a0c784"
    runs = [
        make_dummy_result("1a", config_id, resolved=False, cost_usd="0.010000"),
        make_dummy_result("2b", config_id, resolved=False, cost_usd="0.010000"),
    ]

    result = evaluator.evaluate(runs, total_planned_runs=4, consecutive_failure_limit=2)
    assert result.action == StopAction.REJECT_CONFIGURATION
    assert result.cancel_undispatched is True


def test_early_stopping_stop_dominated():
    """Verify candidate cannot catch baseline triggers STOP_DOMINATED."""
    evaluator = EarlyStoppingEvaluator()
    base_config_id = "cfg_948a3f81e3a1b029"
    cand_config_id = "cfg_4f1b82d3e9a0c784"

    baseline_runs = [
        make_dummy_result(f"ba{i}", base_config_id, resolved=True, cost_usd="0.010000")
        for i in range(4)
    ] # Baseline has 4/4 = 1.00 pass rate

    # Candidate has 1 pass then 2 fails with consecutive_failure_limit=3
    cand_runs = [
        make_dummy_result("c1", cand_config_id, resolved=True, cost_usd="0.010000"),
        make_dummy_result("c2", cand_config_id, resolved=False, cost_usd="0.010000"),
        make_dummy_result("c3", cand_config_id, resolved=False, cost_usd="0.010000"),
    ] # Max possible for candidate: (1 + 1) / 4 = 0.50 (vs baseline 1.00)

    result = evaluator.evaluate(cand_runs, baseline_results=baseline_runs, total_planned_runs=4, consecutive_failure_limit=3)
    assert result.action == StopAction.STOP_DOMINATED
    assert result.cancel_undispatched is True
