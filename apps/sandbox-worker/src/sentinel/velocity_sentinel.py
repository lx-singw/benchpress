"""
Predictive FinOps Budget Sentinel with Turn-5 Markov Token Velocity Projection & Model Downgrader.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("benchpress.sentinel.velocity")


@dataclass
class SentinelEvaluationResult:
    action: str  # "CONTINUE", "DOWNGRADE_TIER", "EARLY_HALT"
    projected_total_cost_usd: float
    recommended_model_tier: str
    confidence_score: float
    reason: str
    trigger_memory_compaction: bool = False


class VelocitySentinel:
    """Monitors token velocity and predicts trajectory economic viability using Markov expectations."""

    # Price cards per 1M tokens ($)
    PRICE_CARDS = {
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "claude-3-7-sonnet": {"input": 3.00, "output": 15.00},
    }

    def __init__(
        self,
        budget_limit_usd: float = 2.00,
        median_cpr_usd: float = 0.42,
        early_halt_turn_threshold: int = 5,
        max_turns: int = 20,
        alpha_input_weight: float = 1.0,
        beta_output_weight: float = 1.2,
    ):
        self.budget_limit_usd = budget_limit_usd
        self.median_cpr_usd = median_cpr_usd
        self.early_halt_turn_threshold = early_halt_turn_threshold
        self.max_turns = max_turns
        self.alpha = alpha_input_weight
        self.beta = beta_output_weight

        self.input_tokens_history: List[int] = []
        self.output_tokens_history: List[int] = []
        self.turn_costs_history: List[float] = []

    def evaluate_turn(
        self,
        turn_index: int,
        accumulated_cost_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        current_model_id: str = "gemini-2.5-pro",
    ) -> SentinelEvaluationResult:
        """Evaluate whether to continue, down-tier to Flash, or early-halt the trajectory."""
        self.input_tokens_history.append(prompt_tokens)
        self.output_tokens_history.append(completion_tokens)
        
        # Calculate turn cost based on model price card
        card = self.PRICE_CARDS.get(current_model_id, self.PRICE_CARDS["gemini-2.5-pro"])
        turn_cost = (prompt_tokens / 1_000_000 * card["input"]) + (completion_tokens / 1_000_000 * card["output"])
        self.turn_costs_history.append(turn_cost)

        # 1. Check Hard Budget Cap
        if accumulated_cost_usd >= self.budget_limit_usd:
            logger.warning(
                f"[Sentinel] Hard budget cap exceeded at turn {turn_index}: "
                f"${accumulated_cost_usd:.4f} >= ${self.budget_limit_usd:.2f}"
            )
            return SentinelEvaluationResult(
                action="EARLY_HALT",
                projected_total_cost_usd=accumulated_cost_usd,
                recommended_model_tier=current_model_id,
                confidence_score=0.99,
                reason=f"Hard budget cap ${self.budget_limit_usd:.2f} exceeded (${accumulated_cost_usd:.4f})",
                trigger_memory_compaction=False,
            )

        # 2. Compute Markov Expectation for Remaining Turns: E[Total Cost | Turn t]
        remaining_turns = max(1, self.max_turns - turn_index)
        
        # In Markov acceleration, recent turn velocity is the primary predictor of runaway trajectory burn
        avg_delta_in = max(sum(self.input_tokens_history) / len(self.input_tokens_history), float(prompt_tokens))
        avg_delta_out = max(sum(self.output_tokens_history) / len(self.output_tokens_history), float(completion_tokens))

        p_in = card["input"] / 1_000_000
        p_out = card["output"] / 1_000_000

        projected_future_cost = remaining_turns * (self.alpha * avg_delta_in * p_in + self.beta * avg_delta_out * p_out)
        projected_total_cost = accumulated_cost_usd + projected_future_cost

        # 3. Turn-5 Markov Evaluation Gate
        if turn_index >= self.early_halt_turn_threshold:
            # Condition A: Catastrophic overrun exceeding 2.5x Median CPR or budget limit
            if projected_total_cost > (self.median_cpr_usd * 2.5) or projected_total_cost > self.budget_limit_usd:
                if current_model_id != "gemini-2.5-flash":
                    logger.warning(
                        f"[Sentinel] Turn-{turn_index} Markov projection (${projected_total_cost:.4f}) exceeds threshold. "
                        f"Autonomous Downgrade: {current_model_id} -> gemini-2.5-flash"
                    )
                    return SentinelEvaluationResult(
                        action="DOWNGRADE_TIER",
                        projected_total_cost_usd=projected_total_cost,
                        recommended_model_tier="gemini-2.5-flash",
                        confidence_score=0.92,
                        reason=f"Turn-{turn_index} velocity (${projected_total_cost:.2f} est) triggered tier downgrade to Flash and L2 compaction",
                        trigger_memory_compaction=True,
                    )
                elif projected_total_cost > (self.budget_limit_usd * 1.2):
                    # Even on Flash, cost exceeds tolerance -> Early Halt
                    return SentinelEvaluationResult(
                        action="EARLY_HALT",
                        projected_total_cost_usd=projected_total_cost,
                        recommended_model_tier="gemini-2.5-flash",
                        confidence_score=0.89,
                        reason=f"Turn-{turn_index} Markov projection (${projected_total_cost:.2f}) exceeds budget cap",
                        trigger_memory_compaction=False,
                    )

        return SentinelEvaluationResult(
            action="CONTINUE",
            projected_total_cost_usd=projected_total_cost,
            recommended_model_tier=current_model_id,
            confidence_score=0.85,
            reason="Trajectory proceeding within FinOps bounds",
            trigger_memory_compaction=False,
        )
