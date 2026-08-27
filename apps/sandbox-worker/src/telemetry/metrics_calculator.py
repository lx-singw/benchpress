"""
Economic & Performance Metrics Calculator: CPR, TBR, and Context Window Decay.
"""

from typing import List, Dict, Any, Optional
from fsm.states import TrajectoryContext, TurnRecord


class MetricsCalculator:
    """Calculates Cost Per Resolution (CPR), Trajectory Bloat Ratio (TBR), and Context Window Decay."""

    OPTIMAL_TURNS_BASELINE = {
        "django__django-11099": 4,
        "sympy__sympy-13480": 6,
        "default": 5,
    }

    @classmethod
    def calculate_cpr(cls, total_cost_usd: float, pass_at_1: bool) -> float:
        """Calculate Cost Per Resolution. If unresolved, CPR equals infinity/penalized cap."""
        if pass_at_1 and total_cost_usd > 0:
            return round(total_cost_usd, 4)
        elif pass_at_1:
            return 0.01
        return round(total_cost_usd * 2.5, 4)  # Penalty factor for unresolved tasks

    @classmethod
    def calculate_tbr(cls, task_id: str, actual_turns: int) -> float:
        """Calculate Trajectory Bloat Ratio (Actual Turns / Optimal Baseline Turns)."""
        optimal = cls.OPTIMAL_TURNS_BASELINE.get(task_id, cls.OPTIMAL_TURNS_BASELINE["default"])
        if optimal <= 0:
            return 1.0
        return round(actual_turns / optimal, 2)

    @classmethod
    def calculate_context_decay_score(cls, turns: List[TurnRecord]) -> float:
        """Measures degradation of accuracy or repetition over long context token accumulation."""
        if not turns:
            return 0.0

        total_turns = len(turns)
        ast_heal_turns = [t.turn_index for t in turns if t.ast_healed]
        
        # If errors concentrate heavily in late turns (turn > 5), decay score increases
        late_errors = sum(1 for idx in ast_heal_turns if idx >= 5)
        decay_score = late_errors / max(1, total_turns)
        return round(min(1.0, decay_score), 3)
