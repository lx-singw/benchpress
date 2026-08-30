"""
Policy Promotion Service.
Executes atomic Compare-and-Swap promotion of verified candidate policies and mints cryptographic DecisionReceipts.
"""

from typing import Optional
from contracts.models import DecisionReceipt, CanaryResult, Aggregate
from contracts.states import PublicDecision, InternalOutcome, TruthClass
from contracts.hashing import generate_receipt_id, compute_canonical_hash, generate_deterministic_ulid
from .repository import get_policy_repository, PolicyRepository
from config import settings
from .publication import receipt_evidence_fields


class PolicyPromotionService:
    """Manages transactional active policy promotion and audit receipt generation."""

    def __init__(self, repo: Optional[PolicyRepository] = None):
        self.repo = repo or get_policy_repository()

    def promote_candidate(
        self,
        experiment_id: str,
        correlation_id: str,
        task_segment_id: str,
        baseline_policy_version: str,
        candidate_policy_version: str,
        baseline_config_id: str,
        candidate_config_id: str,
        baseline_agg: Aggregate,
        candidate_agg: Aggregate,
        canary_res: CanaryResult,
        trigger_event_id: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        selected_task_ids: Optional[list[str]] = None,
    ) -> DecisionReceipt:
        decision_id = f"dec_{generate_deterministic_ulid({'experiment_id': experiment_id, 'outcome': 'SWITCH', 'canary_id': canary_res.canary_id})}"
        now_iso = canary_res.evaluated_at

        if not canary_res.promotion_approved or not canary_res.candidate_passed:
            raise ValueError("Candidate promotion requires a passing, approved canary result")

        # Execute Compare-and-Swap promotion
        pointer = self.repo.get_active_pointer(task_segment_id)
        active = self.repo.get_active_policy(task_segment_id)
        if active is None:
            raise RuntimeError(f"No active policy for segment '{task_segment_id}'")
        if active.policy_version == candidate_policy_version:
            candidate = self.repo.get_policy(candidate_policy_version)
            cas_success = bool(candidate and candidate.parent_policy_version == baseline_policy_version)
        else:
            cas_success = self.repo.compare_and_swap_active_policy(
                task_segment_id=task_segment_id,
                expected_active_version=baseline_policy_version,
                new_candidate_version=candidate_policy_version,
                decision_id=decision_id,
                expected_generation=int(pointer["generation"]) if pointer else None,
            )

        if not cas_success:
            raise RuntimeError(
                f"CAS policy promotion conflict: expected active '{baseline_policy_version}' "
                f"did not match current active policy pointer for segment '{task_segment_id}'"
            )

        active_after = self.repo.get_active_policy(task_segment_id)
        if active_after is None or active_after.policy_version != candidate_policy_version:
            rollback_pointer = self.repo.get_active_pointer(task_segment_id)
            restored = self.repo.compare_and_swap_active_policy(
                task_segment_id=task_segment_id,
                expected_active_version=candidate_policy_version,
                new_candidate_version=baseline_policy_version,
                decision_id=decision_id,
                expected_generation=int(rollback_pointer["generation"]) if rollback_pointer else None,
            )
            restored_policy = self.repo.get_active_policy(task_segment_id)
            if not restored or restored_policy is None or restored_policy.policy_version != baseline_policy_version:
                raise RuntimeError("Post-promotion verification failed and exact baseline restoration could not be proven")
            raise RuntimeError("Post-promotion verification failed; exact baseline policy was restored")

        evidence_payload = {
            "experiment_id": experiment_id,
            "baseline_aggregate_id": baseline_agg.aggregate_id,
            "candidate_aggregate_id": candidate_agg.aggregate_id,
            "canary_id": canary_res.canary_id,
        }
        evidence_hash = compute_canonical_hash(evidence_payload)

        receipt_payload = {
            "schema_version": "1.0.0",
            "decision_id": decision_id,
            "experiment_id": experiment_id,
            "correlation_id": correlation_id,
            "public_decision": PublicDecision.SWITCH,
            "internal_outcome": InternalOutcome.SWITCH_RECOMMENDED,
            "baseline_configuration_id": baseline_config_id,
            "candidate_configuration_id": candidate_config_id,
            "task_segment_id": task_segment_id,
            "baseline_aggregate_id": baseline_agg.aggregate_id,
            "candidate_aggregate_id": candidate_agg.aggregate_id,
            "canary_id": canary_res.canary_id,
            "why_decision": f"Candidate policy '{candidate_policy_version}' passed its contained canary with pass rate {candidate_agg.pass_rate:.4f} versus baseline {baseline_agg.pass_rate:.4f}; CPR values are {candidate_agg.cpr_usd or 'undefined'} and {baseline_agg.cpr_usd or 'undefined'} respectively.",
            "why_not_cheapest": "Selection follows the frozen quality floor and failure-inclusive aggregate; see the referenced eligible runs and failures.",
            "what_would_reverse_it": "A versioned staleness event, quality-floor breach, failed contained canary, or policy threshold change requires reevaluation.",
            "known_limitations": [f"Baseline attempts: {baseline_agg.total_attempts}; candidate attempts: {candidate_agg.total_attempts}."],
            **receipt_evidence_fields(
                baseline_agg=baseline_agg,
                candidate_agg=candidate_agg,
                trigger_event_id=trigger_event_id,
                fingerprint_id=fingerprint_id,
                plan_id=plan_id,
                baseline_policy_version=baseline_policy_version,
                candidate_policy_version=candidate_policy_version,
                selected_task_ids=selected_task_ids,
            ),
            "truth_class": TruthClass.DEMO_FIXTURE if settings.use_local_mock else TruthClass.BENCHPRESS_MEASURED,
            "evidence_hash": evidence_hash,
            "code_commit_sha": settings.release_sha if not settings.use_local_mock else "0" * 40,
            "created_at": now_iso,
        }

        receipt_id = generate_receipt_id(receipt_payload)
        return DecisionReceipt(receipt_id=receipt_id, **receipt_payload)
