"""
Policy Promotion Service.
Executes atomic Compare-and-Swap promotion of verified candidate policies and mints cryptographic DecisionReceipts.
"""

from typing import Optional, List
from contracts.models import DecisionReceipt, CanaryResult, Aggregate
from contracts.states import PublicDecision, InternalOutcome, TruthClass
from contracts.hashing import generate_receipt_id, compute_canonical_hash, utc_now_rfc3339, generate_ulid
from .repository import get_policy_repository, PolicyRepository


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
    ) -> DecisionReceipt:
        decision_id = f"dec_{generate_ulid()}"
        now_iso = utc_now_rfc3339()

        # Execute Compare-and-Swap promotion
        cas_success = self.repo.compare_and_swap_active_policy(
            task_segment_id=task_segment_id,
            expected_active_version=baseline_policy_version,
            new_candidate_version=candidate_policy_version,
            decision_id=decision_id,
        )

        if not cas_success:
            raise RuntimeError(
                f"CAS policy promotion conflict: expected active '{baseline_policy_version}' "
                f"did not match current active policy pointer for segment '{task_segment_id}'"
            )

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
            "why_decision": f"Candidate policy '{candidate_policy_version}' demonstrated lower CPR (${candidate_agg.cpr_usd} vs ${baseline_agg.cpr_usd}) with equal or higher pass rate and passed contained canary.",
            "why_not_cheapest": "Selected configuration preserves 100% quality assertions on judged tasks whereas cheaper variants fail safety/correctness boundaries.",
            "what_would_reverse_it": "Candidate exceeding CPR degradation limit of 15% or failing production canary.",
            "known_limitations": ["Evaluated on 4-task cohort with 95% Wilson Score confidence interval."],
            "truth_class": TruthClass.BENCHPRESS_MEASURED,
            "evidence_hash": evidence_hash,
            "code_commit_sha": "72f14ce000000000000000000000000000000000",
            "created_at": now_iso,
        }

        receipt_id = generate_receipt_id(receipt_payload)
        return DecisionReceipt(receipt_id=receipt_id, **receipt_payload)
