"""
Continuous Model Fine-Tuning Exporter Test Suite.
Verifies Vertex AI Gemini SFT JSONL formatting and DPO preference pair generation.
"""

import pytest
from src.telemetry.fine_tune_exporter import FineTuneExporter


def test_fine_tune_exporter_sft_format():
    """Verify passing trajectory is formatted into Vertex AI Gemini multi-turn SFT JSONL."""
    sample_passing_trajectory = {
        "trajectory_id": "traj-pass-01",
        "task_id": "django__django-11099",
        "task_suite": "SWE_BENCH_VERIFIED",
        "pass_at_1": True,
        "resolved": True,
        "total_cost_usd": 0.185,
        "turns": [
            {
                "turn_index": 1,
                "state": "REASONING_PLANNER",
                "action": "Plan to update regex in validators.py",
            },
            {
                "turn_index": 2,
                "state": "TOOL_DISPATCH_CODER",
                "tool_call_name": "editHunk",
                "tool_call_payload": {"path": "django/core/validators.py", "target": "^[\\w.@+-]+$", "replacement": "\\A[\\w.@+-]+\\Z"},
                "sandbox_stdout": "Hunk replaced successfully",
                "sandbox_exit_code": 0,
            },
        ],
    }

    sft_record = FineTuneExporter.export_to_gemini_sft(sample_passing_trajectory)
    assert sft_record is not None
    assert "system_instruction" in sft_record
    assert len(sft_record["contents"]) >= 3

    # First turn is user prompt
    assert sft_record["contents"][0]["role"] == "user"
    assert "django__django-11099" in sft_record["contents"][0]["parts"][0]["text"]

    # Model tool call turn
    assert sft_record["contents"][2]["role"] == "model"
    assert "functionCall" in sft_record["contents"][2]["parts"][0]
    assert sft_record["contents"][2]["parts"][0]["functionCall"]["name"] == "editHunk"


def test_fine_tune_exporter_dpo_pair_generation():
    """Verify DPO preference pair generates chosen (hybrid) vs rejected (monolithic) steps."""
    winning_traj = {
        "trajectory_id": "traj-win-hybrid",
        "task_id": "django__django-11099",
        "task_suite": "SWE_BENCH_VERIFIED",
        "model_id": "hybrid-gemini-pro-flash",
        "total_cost_usd": 0.185,
        "turns": [{"turn_index": 1, "state": "TOOL_DISPATCH_CODER", "tool_call_name": "editHunk", "turn_cost_usd": 0.05}],
    }

    failed_traj = {
        "trajectory_id": "traj-fail-claude",
        "task_id": "django__django-11099",
        "task_suite": "SWE_BENCH_VERIFIED",
        "model_id": "claude-3-7-sonnet",
        "total_cost_usd": 1.480,
        "turns": [
            {"turn_index": 1, "state": "TOOL_DISPATCH_CODER", "tool_call_name": "readFile", "turn_cost_usd": 0.35},
            {"turn_index": 2, "state": "FATAL_HALT", "tool_call_name": None, "turn_cost_usd": 1.13},
        ],
    }

    dpo_pair = FineTuneExporter.export_to_dpo_pair(winning_traj, failed_traj)
    assert dpo_pair.task_id == "django__django-11099"
    assert dpo_pair.cost_savings_pct == 87.5
    assert len(dpo_pair.chosen) == 1
    assert len(dpo_pair.rejected) == 2
    assert dpo_pair.metadata["winning_model"] == "hybrid-gemini-pro-flash"
