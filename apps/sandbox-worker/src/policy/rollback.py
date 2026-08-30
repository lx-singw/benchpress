"""
Policy Rollback Service.
Retains active baseline configuration upon canary failure or early rejection and mints STAY DecisionReceipt.
"""

from typing import Optional
from contracts.models import DecisionReceipt, CanaryResult, Aggregate
from contracts.states import PublicDecision, InternalOutcome, TruthClass
from contracts.hashing import generate_receipt_id, compute_canonical_hash, generate_deterministic_ulid
from .repository import get_policy_repository, PolicyRepository
from config import settings
from .publication import receipt_evidence_fields


class PolicyRollbackService:
    """Handles failed canary containment and mints STAY decision audit receipts."""

    def __init__(self, repo: Optional[PolicyRepository] = None):
        self.repo = repo or get_policy_repository()

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
        trigger_event_id: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        selected_task_ids: Optional[list[str]] = None,
    ) -> DecisionReceipt:
        outcome_name = "CANARY_ROLLED_BACK" if canary_res else "STAY"
        decision_id = f"dec_{generate_deterministic_ulid({'experiment_id': experiment_id, 'outcome': outcome_name, 'canary_id': canary_res.canary_id if canary_res else None})}"
        now_iso = canary_res.evaluated_at if canary_res else max(
            baseline_agg.created_at,
            candidate_agg.created_at if candidate_agg else baseline_agg.created_at,
        )

        active = self.repo.get_active_policy(task_segment_id)
        if active is None:
            raise RuntimeError(f"No active policy for segment '{task_segment_id}'")
        if active.policy_version != baseline_policy_version:
            if not candidate_policy_version or active.policy_version != candidate_policy_version:
                raise RuntimeError("Rollback refused because the active pointer matches neither candidate nor baseline")
            pointer = self.repo.get_active_pointer(task_segment_id)
            restored = self.repo.compare_and_swap_active_policy(
                task_segment_id=task_segment_id,
                expected_active_version=candidate_policy_version,
                new_candidate_version=baseline_policy_version,
                decision_id=decision_id,
                expected_generation=int(pointer["generation"]) if pointer else None,
            )
            if not restored:
                raise RuntimeError("Rollback CAS conflict while restoring exact baseline policy")
            verified = self.repo.get_active_policy(task_segment_id)
            if verified is None or verified.policy_version != baseline_policy_version:
                raise RuntimeError("Rollback completed but exact baseline activation could not be verified")

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
            "why_not_cheapest": "The candidate did not satisfy the frozen quality, safety, sufficiency, or canary boundary.",
            "what_would_reverse_it": "New non-stale evidence that satisfies the frozen boundary would trigger another contained canary.",
            "known_limitations": [f"Baseline attempts: {baseline_agg.total_attempts}; candidate evidence may be incomplete."],
            **receipt_evidence_fields(
                baseline_agg=baseline_agg,
                candidate_agg=candidate_agg,
                trigger_event_id=trigger_event_id,
                fingerprint_id=fingerprint_id,
                plan_id=plan_id,
                baseline_policy_version=baseline_policy_version,
                candidate_policy_version=candidate_policy_version,
                selected_task_ids=selected_task_ids,
                rollback_performed=bool(canary_res),
            ),
            "truth_class": TruthClass.DEMO_FIXTURE if settings.use_local_mock else TruthClass.BENCHPRESS_MEASURED,
            "evidence_hash": evidence_hash,
            "code_commit_sha": settings.release_sha if not settings.use_local_mock else "0" * 40,
            "created_at": now_iso,
        }

        receipt_id = generate_receipt_id(receipt_payload)
        return DecisionReceipt(receipt_id=receipt_id, **receipt_payload)
