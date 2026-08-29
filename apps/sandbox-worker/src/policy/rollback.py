"""
Policy Rollback Service.
Retains active baseline configuration upon canary failure or early rejection and mints STAY DecisionReceipt.
"""

from typing import Optional, List
from contracts.models import DecisionReceipt, CanaryResult, Aggregate
from contracts.states import PublicDecision, InternalOutcome, TruthClass
from contracts.hashing import generate_receipt_id, compute_canonical_hash, utc_now_rfc3339, generate_ulid


class PolicyRollbackService:
    """Handles failed canary containment and mints STAY decision audit receipts."""

    def execute_rollback(
        self,
        experiment_id: str,
        correlation_id: str,
        task_segment_id: str,
        baseline_policy_version: str,
        candidate_policy_version: Optional[str],
        baseline_config_id: str,
        candidate_config_id: Optional[str],
        baseline_agg: Aggregate,
        candidate_agg: Optional[Aggregate] = None,
        canary_res: Optional[CanaryResult] = None,
        rollback_reason: str = "Candidate failed canary guardrail checks.",
    ) -> DecisionReceipt:
        decision_id = f"dec_{generate_ulid()}"
        now_iso = utc_now_rfc3339()

        evidence_payload = {
            "experiment_id": experiment_id,
            "baseline_aggregate_id": baseline_agg.aggregate_id,
            "candidate_aggregate_id": candidate_agg.aggregate_id if candidate_agg else None,
            "canary_id": canary_res.canary_id if canary_res else None,
            "rollback_reason": rollback_reason,
        }
        evidence_hash = compute_canonical_hash(evidence_payload)

        receipt_payload = {
            "schema_version": "1.0.0",
            "decision_id": decision_id,
            "experiment_id": experiment_id,
            "correlation_id": correlation_id,
            "public_decision": PublicDecision.STAY,
            "internal_outcome": InternalOutcome.STAY_BASELINE_SUPERIOR if not canary_res else InternalOutcome.CANARY_ROLLED_BACK,
            "baseline_configuration_id": baseline_config_id,
            "candidate_configuration_id": candidate_config_id,
            "task_segment_id": task_segment_id,
            "baseline_aggregate_id": baseline_agg.aggregate_id,
            "candidate_aggregate_id": candidate_agg.aggregate_id if candidate_agg else None,
            "canary_id": canary_res.canary_id if canary_res else None,
            "why_decision": f"Policy retained on baseline '{baseline_policy_version}'. Reason: {rollback_reason}",
            "why_not_cheapest": "Candidate failed quality/safety guardrails or exceeded cost per resolution.",
            "what_would_reverse_it": "Candidate model updates resolving quality/safety regressions.",
            "known_limitations": ["Evaluated on 4-task cohort with deterministic Pytest assertion oracles."],
            "truth_class": TruthClass.BENCHPRESS_MEASURED,
            "evidence_hash": evidence_hash,
            "code_commit_sha": "72f14ce000000000000000000000000000000000",
            "created_at": now_iso,
        }

        receipt_id = generate_receipt_id(receipt_payload)
        return DecisionReceipt(receipt_id=receipt_id, **receipt_payload)
