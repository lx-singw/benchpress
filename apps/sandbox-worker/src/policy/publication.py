"""Deterministic receipt publication for abstention outcomes."""

from __future__ import annotations

from config import settings
from contracts.hashing import compute_canonical_hash, generate_deterministic_ulid, generate_receipt_id
from contracts.models import Aggregate, DecisionReceipt
from contracts.states import InternalOutcome, PublicDecision, TruthClass


def receipt_evidence_fields(
    *,
    baseline_agg: Aggregate,
    candidate_agg: Aggregate | None,
    trigger_event_id: str | None = None,
    fingerprint_id: str | None = None,
    plan_id: str | None = None,
    baseline_policy_version: str | None = None,
    candidate_policy_version: str | None = None,
    selected_task_ids: list[str] | None = None,
    rollback_performed: bool = False,
) -> dict:
    aggregates = [baseline_agg] + ([candidate_agg] if candidate_agg else [])
    excluded = {
        key: reason
        for aggregate in aggregates
        for key, reason in aggregate.ineligible_run_reasons.items()
    }
    return {
        "trigger_event_id": trigger_event_id,
        "fingerprint_id": fingerprint_id,
        "plan_id": plan_id,
        "baseline_policy_version": baseline_policy_version,
        "candidate_policy_version": candidate_policy_version,
        "selected_task_ids": sorted(selected_task_ids or []),
        "eligible_run_keys": sorted({key for aggregate in aggregates for key in aggregate.eligible_run_keys}),
        "excluded_run_reasons": dict(sorted(excluded.items())),
        "baseline_evidence": baseline_agg.model_dump(mode="json"),
        "candidate_evidence": candidate_agg.model_dump(mode="json") if candidate_agg else None,
        "approval_boundary_version": "decision_policy_v1",
        "rollback_performed": rollback_performed,
        "publication_status": "PUBLISHED",
    }


def mint_test_more_receipt(
    *,
    experiment_id: str,
    correlation_id: str,
    task_segment_id: str,
    baseline_config_id: str,
    candidate_config_id: str,
    baseline_agg: Aggregate,
    candidate_agg: Aggregate,
    reason: str,
    trigger_event_id: str | None = None,
    fingerprint_id: str | None = None,
    plan_id: str | None = None,
    baseline_policy_version: str | None = None,
    selected_task_ids: list[str] | None = None,
) -> DecisionReceipt:
    decision_id = f"dec_{generate_deterministic_ulid({'experiment_id': experiment_id, 'outcome': 'TEST_MORE'})}"
    evidence = {
        "experiment_id": experiment_id,
        "baseline_aggregate_id": baseline_agg.aggregate_id,
        "candidate_aggregate_id": candidate_agg.aggregate_id,
        "outcome": InternalOutcome.ABSTAIN_INSUFFICIENT_EVIDENCE.value,
        "reason": reason,
    }
    payload = {
        "schema_version": "1.0.0",
        "decision_id": decision_id,
        "experiment_id": experiment_id,
        "correlation_id": correlation_id,
        "public_decision": PublicDecision.TEST_MORE,
        "internal_outcome": InternalOutcome.ABSTAIN_INSUFFICIENT_EVIDENCE,
        "baseline_configuration_id": baseline_config_id,
        "candidate_configuration_id": candidate_config_id,
        "task_segment_id": task_segment_id,
        "baseline_aggregate_id": baseline_agg.aggregate_id,
        "candidate_aggregate_id": candidate_agg.aggregate_id,
        "canary_id": None,
        "why_decision": reason,
        "why_not_cheapest": "No candidate is selected while the frozen evidence-sufficiency boundary is unmet.",
        "what_would_reverse_it": "Additional eligible runs or refreshed non-stale inputs may satisfy the frozen boundary.",
        "known_limitations": [
            f"Baseline attempts: {baseline_agg.total_attempts}; candidate attempts: {candidate_agg.total_attempts}."
        ],
        **receipt_evidence_fields(
            baseline_agg=baseline_agg,
            candidate_agg=candidate_agg,
            trigger_event_id=trigger_event_id,
            fingerprint_id=fingerprint_id,
            plan_id=plan_id,
            baseline_policy_version=baseline_policy_version,
            selected_task_ids=selected_task_ids,
        ),
        "truth_class": TruthClass.DEMO_FIXTURE if settings.use_local_mock else TruthClass.BENCHPRESS_MEASURED,
        "evidence_hash": compute_canonical_hash(evidence),
        "code_commit_sha": settings.release_sha if not settings.use_local_mock else "0" * 40,
        "created_at": max(baseline_agg.created_at, candidate_agg.created_at),
    }
    return DecisionReceipt(receipt_id=generate_receipt_id(payload), **payload)
