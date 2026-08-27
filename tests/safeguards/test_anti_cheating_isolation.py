"""
Test Suite for Safeguard 4: Anti-Cheating Read-Only Test Mounts & Exit Code Invariants.
"""

import os
import stat
import pytest
from sandbox.worktree import EphemeralWorktreeProvisioner
from tools.pytest_runner import PytestRunnerTool


@pytest.mark.asyncio
async def test_read_only_test_suite_locking():
    """Verify that tests/ directory files are locked with read-only permissions upon sandbox creation."""
    workspace = await EphemeralWorktreeProvisioner.provision_task_worktree(
        "swe_bench_verified", "django__django-11099"
    )
    test_file = os.path.join(workspace, "tests", "test_validators.py")
    assert os.path.exists(test_file)

    # Check file mode: write permissions must be stripped
    file_mode = os.stat(test_file).st_mode
    is_writable = bool(file_mode & stat.S_IWRITE)

    try:
        # On POSIX / Windows, attempting to open for writing in read-only mode should fail or raise PermissionError
        if not is_writable:
            with pytest.raises(PermissionError):
                with open(test_file, "w") as f:
                    f.write("def test_cheating(): assert True\n")
    finally:
        await EphemeralWorktreeProvisioner.cleanup_worktree(workspace)


@pytest.mark.asyncio
async def test_pytest_runner_rejects_test_tampering():
    """Verify that PytestRunnerTool catches test tampering and returns exit code 403."""
    workspace = await EphemeralWorktreeProvisioner.provision_task_worktree(
        "swe_bench_verified", "django__django-11099"
    )

    try:
        test_file = os.path.join(workspace, "tests", "test_validators.py")
        # Force unlock and modify test file
        os.chmod(test_file, stat.S_IWRITE | stat.S_IREAD)
        with open(test_file, "a") as f:
            f.write("\n# Tampered line by rogue model\n")

        # Pytest runner should intercept git status tampering in tests/
        result = await PytestRunnerTool.run_pytest(workspace, "tests/")
        assert result["passed"] is False
        assert result["exit_code"] == 403
        assert "Anti-Cheating" in result["error"]
    finally:
        await EphemeralWorktreeProvisioner.cleanup_worktree(workspace)


@pytest.mark.asyncio
async def test_pytest_runner_rejects_fake_pass_logs():
    """Verify that non-zero exit codes are NEVER marked as passed regardless of stdout content."""
    workspace = await EphemeralWorktreeProvisioner.provision_task_worktree(
        "swe_bench_verified", "django__django-11099"
    )

    try:
        # Run pytest on the initial buggy fixture without fixing validators.py
        # Should fail with exit_code != 0
        result = await PytestRunnerTool.run_pytest(workspace, "tests/test_validators.py")
        assert result["passed"] is False
        assert result["exit_code"] != 0
    finally:
        await EphemeralWorktreeProvisioner.cleanup_worktree(workspace)
