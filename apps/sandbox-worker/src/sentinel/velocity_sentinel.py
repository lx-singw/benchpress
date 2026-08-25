"""
Predictive FinOps Budget Sentinel with Turn-5 Markov Projection.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("benchpress.sentinel.velocity")


@dataclass
class SentinelDecision:
    action: str  # "CONTINUE", "EARLY_HALT", "THROTTLE"
    projected_total_cost_usd: float
    confidence_score: float
    reason: str


class VelocitySentinel:
    """Monitors token velocity and predicts trajectory economic viability."""

    def __init__(
        self,
        budget_limit_usd: float = 2.00,
        early_halt_turn_threshold: int = 5,
        cost_overrun_tolerance: float = 1.15,
    ):
        self.budget_limit_usd = budget_limit_usd
        self.early_halt_turn_threshold = early_halt_turn_threshold
        self.cost_overrun_tolerance = cost_overrun_tolerance
        self.token_history: List[int] = []

    def evaluate_turn(
        self,
        turn_index: int,
        accumulated_cost_usd: float,
        tokens_this_turn: int,
    ) -> SentinelDecision:
        """Evaluate whether to continue or early-halt the trajectory."""
        self.token_history.append(tokens_this_turn)

        # Basic linear + Markov acceleration projection
        avg_tokens_per_turn = sum(self.token_history) / len(self.token_history)
        estimated_remaining_turns = max(1, 15 - turn_index)
        
        # Turn cost rate
        cost_per_turn = accumulated_cost_usd / max(1, turn_index)
        projected_total_cost = accumulated_cost_usd + (cost_per_turn * estimated_remaining_turns)

        # Budget hard cap violation
        if accumulated_cost_usd >= self.budget_limit_usd:
            logger.warning(
                f"[Sentinel] Hard budget cap exceeded at turn {turn_index}: "
                f"${accumulated_cost_usd:.4f} >= ${self.budget_limit_usd:.2f}"
            )
            return SentinelDecision(
                action="EARLY_HALT",
                projected_total_cost_usd=accumulated_cost_usd,
                confidence_score=0.99,
                reason=f"Hard budget cap ${self.budget_limit_usd:.2f} exceeded (${accumulated_cost_usd:.4f})",
            )

        # Turn-5 Markov Early Halt Gate
        if turn_index >= self.early_halt_turn_threshold:
            if projected_total_cost > (self.budget_limit_usd * self.cost_overrun_tolerance):
                logger.warning(
                    f"[Sentinel] Turn-{turn_index} Markov projection indicates cost overrun: "
                    f"${projected_total_cost:.4f} > ${self.budget_limit_usd:.2f}"
                )
                return SentinelDecision(
                    action="EARLY_HALT",
                    projected_total_cost_usd=projected_total_cost,
                    confidence_score=0.91,
                    reason=f"Turn-{turn_index} Markov projection (${projected_total_cost:.2f}) exceeds budget (${self.budget_limit_usd:.2f})",
                )

        return SentinelDecision(
            action="CONTINUE",
            projected_total_cost_usd=projected_total_cost,
            confidence_score=0.85,
            reason="Trajectory proceeding within FinOps bounds",
        )
