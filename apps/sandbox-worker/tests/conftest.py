"""
Shared Pytest Fixtures for Benchpress Sandbox Worker Test Suite.
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from typing import AsyncGenerator, Generator
from fsm.states import TrajectoryContext, FsmState, TrajectoryStatus
from tools.registry import ToolRegistry


@pytest.fixture
def sample_trajectory_context() -> TrajectoryContext:
    """Create a standardized TrajectoryContext fixture."""
    return TrajectoryContext(
        trajectory_id="test-traj-11099-abc",
        task_suite="SWE_BENCH_VERIFIED",
        task_id="django__django-11099",
        model_id="gemini-2.5-pro",
        budget_limit_usd=2.00,
        max_turns=10,
    )


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Instantiate a fresh ToolRegistry."""
    return ToolRegistry()


@pytest.fixture
def temp_git_workspace() -> Generator[str, None, None]:
    """Create a temporary git-initialized workspace directory."""
    temp_dir = tempfile.mkdtemp(prefix="test_bp_git_")
    os.system(f"git init '{temp_dir}' > /dev/null 2>&1")
    os.system(f"git -C '{temp_dir}' config user.name 'TestBot'")
    os.system(f"git -C '{temp_dir}' config user.email 'test@benchpress.ai'")

    # Create dummy app.py
    with open(os.path.join(temp_dir, "app.py"), "w") as f:
        f.write("# Benchpress test file\nx = 1\n")
    os.system(f"git -C '{temp_dir}' add -A && git -C '{temp_dir}' commit -m 'initial' > /dev/null 2>&1")

    yield temp_dir

    shutil.rmtree(temp_dir, ignore_errors=True)
