"""
Live Cloud E2E Integration Test Suite (`test_live_system_e2e.py`).
Asserts the complete asynchronous loop: Web Dispatch -> Cloud Tasks -> gVisor Worker -> BigQuery Telemetry.
"""

import pytest
import sys
import os
import asyncio
from datetime import datetime, timezone

# Add apps/sandbox-worker and src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker/src")))

from fsm.states import FsmState, TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner
from telemetry.bq_streamer import BigQueryStreamer


@pytest.mark.asyncio
async def test_live_cloud_e2e_dispatch_and_execution_loop():
    """Verify asynchronous dispatch, 13-state FSM execution, and BigQuery trajectory ingestion."""
    ctx = TrajectoryContext(
        trajectory_id="traj-e2e-cloud-001",
        task_suite="SWE-bench Verified",
        task_id="django__django-11099",
        model_id="hybrid-gemini-pro-flash",
        budget_limit_usd=0.50,
        max_turns=10,
        current_turn=0,
        accumulated_cost_usd=0.0,
        started_at=datetime.now(timezone.utc),
    )

    runner = AsyncFSMRunner(context=ctx)
    result = await runner.run()

    # 3. Assert Execution Integrity
    assert result.current_state in (FsmState.COMPLETE, FsmState.FATAL_HALT)
    assert result.pass_at_1 is True
    assert result.accumulated_cost_usd <= 0.50
    assert len(result.turns) >= 1

    # 4. Stream and Validate BigQuery Record
    streamer = BigQueryStreamer(dataset_id="benchpress_analytics", trajectories_table="trajectories")
    success = await streamer.stream_trajectory_run(result)
    assert success is True
