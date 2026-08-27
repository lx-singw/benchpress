"""
Chaos Engineering & Resilience Mesh Test Suite.
Verifies AST fault corruption recovery and token velocity surge triggers.
"""

import pytest
from src.chaos.chaos_mesh import ChaosMesh, ChaosFaultType
from src.supervisor.ast_interceptor import AstInterceptor
from src.supervisor.ast_healer import AstHealer
from src.sentinel.velocity_sentinel import VelocitySentinel


@pytest.mark.asyncio
async def test_chaos_mesh_ast_corruption_and_self_healing():
    """Verify ChaosMesh injects AST schema corruption and Autonomous AST Healer repairs it."""
    chaos = ChaosMesh(active_fault=ChaosFaultType.AST_SCHEMA_CORRUPTION)
    interceptor = AstInterceptor()
    healer = AstHealer()

    # Agent attempts valid tool call
    original_tool = "editHunk"
    original_args = {"path": "django/core/validators.py", "target": "^[\\w.@+-]+$", "replacement": "\\A[\\w.@+-]+\\Z"}

    # Chaos mesh mutates it into legacy corrupted format
    corrupted_tool, corrupted_args = chaos.apply_tool_call_chaos(original_tool, original_args)
    assert corrupted_tool == "edit_file"
    assert "file_path" in corrupted_args

    # AST Interceptor detects invalid parameter schema
    is_valid, err_msg, parsed_args = interceptor.intercept_and_validate(corrupted_tool, corrupted_args)
    assert not is_valid

    # AST Healer synthesizes wrapper adapter patch
    healed, rep_tool, rep_args, trace = await healer.heal_tool_call(corrupted_tool, corrupted_args, err_msg)
    assert healed is True
    assert rep_tool == "editHunk"
    assert "path" in rep_args
    assert rep_args["path"] == "django/core/validators.py"


@pytest.mark.asyncio
async def test_chaos_mesh_token_surge_triggers_velocity_sentinel():
    """Verify ChaosMesh token surge causes Velocity Sentinel to downgrade model tier."""
    chaos = ChaosMesh(active_fault=ChaosFaultType.TOKEN_VELOCITY_SURGE)
    sentinel = VelocitySentinel(budget_limit_usd=2.00, median_cpr_usd=0.42, early_halt_turn_threshold=5)

    # Simulate Turn 1-4 baseline
    for i in range(1, 5):
        sentinel.evaluate_turn(
            turn_index=i,
            accumulated_cost_usd=0.04 * i,
            prompt_tokens=2000,
            completion_tokens=400,
            current_model_id="gemini-2.5-pro",
        )

    # Turn 5 has a 10x chaos token surge
    base_prompt_tokens = 18000
    base_comp_tokens = 2500
    spiked_prompt, spiked_comp = chaos.apply_token_surge_chaos(base_prompt_tokens, base_comp_tokens)

    eval_result = sentinel.evaluate_turn(
        turn_index=5,
        accumulated_cost_usd=0.65,
        prompt_tokens=spiked_prompt,
        completion_tokens=spiked_comp,
        current_model_id="gemini-2.5-pro",
    )

    # Sentinel must trigger model downgrade or early halt to protect budget ceiling
    assert eval_result.projected_total_cost_usd > 0
    assert eval_result.action in ["DOWNGRADE_TIER", "EARLY_HALT"]
    assert eval_result.trigger_memory_compaction is True or eval_result.action == "EARLY_HALT"
