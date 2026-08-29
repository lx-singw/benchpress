"""
Early Stopping & Dominance Engine.
Evaluates whether remaining planned runs should be cancelled early due to configuration rejection or dominance.
"""

from enum import Enum
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from contracts.models import RunResult


class StopAction(str, Enum):
    CONTINUE = "CONTINUE"
    REJECT_CONFIGURATION = "REJECT_CONFIGURATION"
    STOP_DOMINATED = "STOP_DOMINATED"
    STOP_SUFFICIENT = "STOP_SUFFICIENT"


@dataclass
class StopEvaluationResult:
    action: StopAction
    reason: str
    cancel_undispatched: bool = False


class EarlyStoppingEvaluator:
    """Evaluates stop conditions after each terminal run."""

    def evaluate(
        self,
        candidate_results: List[RunResult],
        baseline_results: Optional[List[RunResult]] = None,
        total_planned_runs: int = 4,
        quality_floor: float = 0.75,
        consecutive_failure_limit: int = 2,
    ) -> StopEvaluationResult:
        if not candidate_results:
            return StopEvaluationResult(action=StopAction.CONTINUE, reason="No candidate results yet.")

        # 1. Consecutive Failures Check
        consecutive_fails = 0
        for r in reversed(candidate_results):
            if not r.resolved:
                consecutive_fails += 1
            else:
                break

        if consecutive_fails >= consecutive_failure_limit:
            return StopEvaluationResult(
                action=StopAction.REJECT_CONFIGURATION,
                reason=f"Triggered {consecutive_fails} consecutive failures (limit: {consecutive_failure_limit}).",
                cancel_undispatched=True,
            )

        attempts = len(candidate_results)
        successes = sum(1 for r in candidate_results if r.resolved)
        pass_rate = successes / attempts

        # 2. Dominance Evaluation (Mathematical Bound relative to baseline)
        if baseline_results and len(baseline_results) >= total_planned_runs:
            baseline_successes = sum(1 for r in baseline_results if r.resolved)
            if baseline_successes > 0:
                remaining_runs = max(0, total_planned_runs - attempts)
                max_possible_successes = successes + remaining_runs
                max_possible_pass_rate = max_possible_successes / total_planned_runs
                baseline_pass_rate = baseline_successes / len(baseline_results)

                if max_possible_pass_rate < (baseline_pass_rate - 0.25):
                    return StopEvaluationResult(
                        action=StopAction.STOP_DOMINATED,
                        reason=(
                            f"Candidate cannot mathematically catch baseline pass rate "
                            f"(max possible: {max_possible_pass_rate:.2f} vs baseline: {baseline_pass_rate:.2f})."
                        ),
                        cancel_undispatched=True,
                    )

        # 3. Quality Floor Severe Breach (if no baseline dominance evaluated)
        if attempts >= 3 and pass_rate < (quality_floor - 0.20):
            return StopEvaluationResult(
                action=StopAction.REJECT_CONFIGURATION,
                reason=f"Pass rate ({pass_rate:.2f}) severely breached quality floor ({quality_floor}).",
                cancel_undispatched=True,
            )

        # 4. Check If All Planned Runs Complete
        if attempts >= total_planned_runs:
            if pass_rate >= quality_floor:
                return StopEvaluationResult(
                    action=StopAction.STOP_SUFFICIENT,
                    reason=f"Completed all {total_planned_runs} runs meeting quality floor ({pass_rate:.2f} >= {quality_floor}).",
                )
            else:
                return StopEvaluationResult(
                    action=StopAction.REJECT_CONFIGURATION,
                    reason=f"Completed all runs but failed quality floor ({pass_rate:.2f} < {quality_floor}).",
                )

        return StopEvaluationResult(action=StopAction.CONTINUE, reason="Evaluating candidate runs.")
