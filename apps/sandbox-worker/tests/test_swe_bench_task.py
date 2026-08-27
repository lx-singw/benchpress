"""
SWE-bench Verified Live Assertion Verification on `django__django-11099`.
"""

import pytest
import os
from sandbox.worktree import EphemeralWorktreeProvisioner
from tools.file_ops import FileOpsTool
from tools.pytest_runner import PytestRunnerTool
from telemetry.metrics_calculator import MetricsCalculator


@pytest.mark.asyncio
async def test_swe_bench_django_11099_execution_and_assertion():
    # 1. Provision ephemeral worktree with Django 11099 fixture
    worktree = await EphemeralWorktreeProvisioner.provision_task_worktree(
        task_suite="SWE_BENCH_VERIFIED",
        task_id="django__django-11099",
    )

    try:
        # 2. Run initial pytest -> Must FAIL on buggy regex
        initial_test = await PytestRunnerTool.run_pytest(worktree, "tests/test_validators.py")
        assert initial_test["passed"] is False

        # 3. Read file contents with FileOpsTool
        read_res = FileOpsTool.read_file(worktree, "django/core/validators.py")
        assert read_res["success"] is True
        assert "ASCIIUsernameValidator" in read_res["content"]

        # 4. Apply fix with editHunk (updating regex to \A[\w.@+-]+\Z)
        target_hunk = "    regex = r'^[\\w.@+-]+$'"
        replacement_hunk = "    regex = r'\\A[\\w.@+-]+\\Z'"

        edit_res = FileOpsTool.edit_hunk(
            worktree,
            "django/core/validators.py",
            target_hunk,
            replacement_hunk,
        )
        assert edit_res["success"] is True

        # 5. Run pytest again -> Must PASS
        verified_test = await PytestRunnerTool.run_pytest(worktree, "tests/test_validators.py")
        assert verified_test["passed"] is True
        assert verified_test["exit_code"] == 0

        # 6. Verify CPR and TBR Calculations
        simulated_cost = 0.2850
        cpr = MetricsCalculator.calculate_cpr(simulated_cost, pass_at_1=True)
        assert cpr == 0.2850

        tbr = MetricsCalculator.calculate_tbr("django__django-11099", actual_turns=4)
        assert tbr == 1.0  # 4 / 4 = 1.0 optimal bloat ratio

    finally:
        await EphemeralWorktreeProvisioner.cleanup_worktree(worktree)
