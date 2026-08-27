"""
Predictive FinOps Budget Sentinel & Markov Velocity Downgrade Tests.
"""

import pytest
from sentinel.velocity_sentinel import VelocitySentinel


@pytest.mark.asyncio
async def test_turn_5_markov_velocity_projection_and_downgrade():
    sentinel = VelocitySentinel(
        budget_limit_usd=2.00,
        median_cpr_usd=0.42,
        early_halt_turn_threshold=5,
        max_turns=20,
    )

    # Turns 1 to 4: Normal consumption
    for turn in range(1, 5):
        res = sentinel.evaluate_turn(
            turn_index=turn,
            accumulated_cost_usd=0.04 * turn,
            prompt_tokens=2000,
            completion_tokens=400,
            current_model_id="gemini-2.5-pro",
        )
        assert res.action == "CONTINUE"

    # Turn 5: Explosive token burn rate (15,000 prompt tokens / turn on Pro)
    res_t5 = sentinel.evaluate_turn(
        turn_index=5,
        accumulated_cost_usd=0.65,
        prompt_tokens=18000,
        completion_tokens=2500,
        current_model_id="gemini-2.5-pro",
    )

    # Projected cost should exceed 2.5x median CPR ($1.05) -> triggers autonomous downgrade to Flash
    assert res_t5.action == "DOWNGRADE_TIER"
    assert res_t5.recommended_model_tier == "gemini-2.5-flash"
    assert res_t5.trigger_memory_compaction is True


@pytest.mark.asyncio
async def test_hard_budget_ceiling_early_halt():
    sentinel = VelocitySentinel(budget_limit_usd=1.00)

    # Spend reaches/exceeds $1.00 limit
    res = sentinel.evaluate_turn(
        turn_index=3,
        accumulated_cost_usd=1.05,
        prompt_tokens=2000,
        completion_tokens=500,
    )

    assert res.action == "EARLY_HALT"
    assert "Hard budget cap" in res.reason
