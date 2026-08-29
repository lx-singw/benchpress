"""
Sufficiency and Decision Mapping Service.
Evaluates statistical evidence sufficiency across baseline and candidate aggregates to guide canary promotion or termination.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from contracts.models import Aggregate
from contracts.states import InternalOutcome, PublicDecision, ExperimentState
from .aggregator import ConfigurationAggregator
from ledger.firestore import get_ledger
from task_queue.cloud_tasks import CloudTasksDispatcher


class SufficiencyEvaluator:
    """Evaluates candidate vs baseline aggregates to determine internal outcome."""

    def evaluate_outcome(
        self,
        baseline_agg: Aggregate,
        candidate_agg: Aggregate,
        cpr_improvement_threshold: float = 0.10,
    ) -> InternalOutcome:
        """Determine whether evidence supports candidate switch, baseline stay, or more testing."""
        # 1. If candidate failed quality floor
        if candidate_agg.quality_floor_breached or candidate_agg.pass_rate < 0.50:
            return InternalOutcome.REJECTED_QUALITY_FLOOR

        # 2. If candidate has 0 successes
        if candidate_agg.resolved_count == 0:
            return InternalOutcome.STAY_CHEAPEST_FAILED

        # 3. Compare CPR
        base_cpr = Decimal(baseline_agg.cpr_usd)
        cand_cpr = Decimal(candidate_agg.cpr_usd)

        # Higher or equal pass rate and lower cost per resolution
        if candidate_agg.pass_rate >= baseline_agg.pass_rate:
            if cand_cpr < base_cpr:
                return InternalOutcome.SWITCH_RECOMMENDED
            elif cand_cpr == base_cpr:
                return InternalOutcome.ABSTAIN_INSUFFICIENT_EVIDENCE

        # Lower pass rate but significant cost savings
        if cand_cpr < (base_cpr * Decimal("0.50")) and candidate_agg.pass_rate >= 0.75:
            return InternalOutcome.SWITCH_RECOMMENDED

        # Otherwise baseline remains superior
        if baseline_agg.pass_rate > candidate_agg.pass_rate:
            return InternalOutcome.STAY_BASELINE_SUPERIOR

        return InternalOutcome.ABSTAIN_INSUFFICIENT_EVIDENCE
