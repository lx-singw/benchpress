"""
Deterministic Plan Policy & Sovereign Approval Gate.
Verifies proposed ExperimentPlans against frozen bounds, baseline inclusion, and spend limits before Cloud Tasks dispatch.
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, List, Optional
from contracts.models import ExperimentPlan, ChangeEvent
from contracts.hashing import compute_canonical_hash, generate_plan_id


@dataclass
class PlanApprovalResult:
    approved: bool
    plan: Optional[ExperimentPlan] = None
    plan_id: Optional[str] = None
    plan_hash: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    reserved_budget_usd: Optional[str] = None


class PlanPolicyValidator:
    """Evaluates and validates proposed ExperimentPlan against strict deterministic invariants."""

    def __init__(
        self,
        supported_config_ids: Optional[List[str]] = None,
        supported_task_ids: Optional[List[str]] = None,
    ):
        self.supported_config_ids = set(supported_config_ids or [
            "cfg_948a3f81e3a1b029",
            "cfg_4f1b82d3e9a0c784",
            "cfg_7c2a93e4f1b80d19",
        ])
        self.supported_task_ids = set(supported_task_ids or [
            "TASK-001",
            "TASK-002",
            "TASK-003",
            "TASK-004",
        ])

    def evaluate_plan(
        self,
        raw_plan: Dict[str, Any],
        trigger_event: Dict[str, Any],
    ) -> PlanApprovalResult:
        reasons: List[str] = []

        # 1. Pydantic Structural Validation
        try:
            plan = ExperimentPlan.model_validate(raw_plan)
        except Exception as e:
            return PlanApprovalResult(
                approved=False,
                reasons=[f"Schema validation error: {str(e)}"],
            )

        # 2. Baseline Configuration Invariant
        expected_baseline = trigger_event.get("baseline_configuration_id")
        if not expected_baseline or plan.baseline_configuration_id != expected_baseline:
            reasons.append(
                f"Missing or mismatched baseline configuration. Expected '{expected_baseline}', "
                f"got '{plan.baseline_configuration_id}'"
            )

        # 3. Candidate Configuration Set
        if not plan.candidate_configuration_ids:
            reasons.append("ExperimentPlan must include at least 1 candidate configuration.")
        else:
            for cfg_id in plan.candidate_configuration_ids:
                if cfg_id not in self.supported_config_ids:
                    reasons.append(f"Unregistered candidate configuration '{cfg_id}'.")

        # 4. Task Cohort Membership
        if not plan.selected_task_ids:
            reasons.append("ExperimentPlan must select at least 1 task from judged cohort.")
        else:
            for task_id in plan.selected_task_ids:
                if task_id not in self.supported_task_ids:
                    reasons.append(f"Unrecognized task '{task_id}' not in frozen judged cohort.")

        # 5. FinOps Budget Limits
        try:
            event_max_spend = Decimal(trigger_event.get("max_spend_usd", "0.000000"))
            plan_max_spend = Decimal(plan.max_matrix_spend_usd)
            plan_reserved = Decimal(plan.reserved_budget_usd)

            if plan_max_spend > event_max_spend:
                reasons.append(
                    f"Plan max_matrix_spend_usd (${plan_max_spend}) exceeds event limit (${event_max_spend})."
                )
            if plan_reserved > plan_max_spend:
                reasons.append(
                    f"Plan reserved_budget_usd (${plan_reserved}) exceeds plan max_matrix_spend_usd (${plan_max_spend})."
                )
        except Exception as e:
            reasons.append(f"Invalid monetary decimal values: {e}")

        # 6. Stop Rules Completeness
        if plan.quality_floor_pass_rate <= 0.0 or plan.quality_floor_pass_rate > 1.0:
            reasons.append("quality_floor_pass_rate must be in range (0.0, 1.0].")
        if plan.early_stop_consecutive_failures < 1:
            reasons.append("early_stop_consecutive_failures must be >= 1.")

        if reasons:
            return PlanApprovalResult(
                approved=False,
                plan=plan,
                reasons=reasons,
            )

        # Calculate Canonical Plan Hash
        clean_dict = plan.model_dump(mode="json")
        plan_hash = compute_canonical_hash(clean_dict)

        return PlanApprovalResult(
            approved=True,
            plan=plan,
            plan_id=plan.plan_id,
            plan_hash=plan_hash,
            reasons=["All deterministic invariants satisfied."],
            reserved_budget_usd=plan.reserved_budget_usd,
        )
