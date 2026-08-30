"""Repository-wide pytest import layout and shared worker fixtures."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parent
WORKER_SRC = ROOT_DIR / "apps" / "sandbox-worker" / "src"
worker_src_string = str(WORKER_SRC)
if worker_src_string in sys.path:
    sys.path.remove(worker_src_string)
sys.path.insert(0, worker_src_string)

from fsm.states import TrajectoryContext
from tools.registry import ToolRegistry


@pytest.fixture
def sample_trajectory_context() -> TrajectoryContext:
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
    return ToolRegistry()


@pytest.fixture
def temp_git_workspace():
    with tempfile.TemporaryDirectory(prefix="test_bp_git_") as temp_dir:
        workspace = Path(temp_dir)
        subprocess.run(["git", "init", str(workspace)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(workspace), "config", "user.name", "TestBot"], check=True)
        subprocess.run(["git", "-C", str(workspace), "config", "user.email", "test@benchpress.ai"], check=True)
        (workspace / "app.py").write_text("# Benchpress test file\nx = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(workspace), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(workspace), "commit", "-m", "initial"],
            check=True,
            capture_output=True,
        )
        yield temp_dir
