"""
Benchpress Sandbox Worker: FastAPI Cloud Tasks Target Service.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel, Field

from fsm.states import TrajectoryContext
from fsm.engine import AsyncFsmEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchpress.worker")

app = FastAPI(
    title="Benchpress Sandbox Worker",
    version="1.0.0",
    description="Cloud Run Gen2 Asynchronous Agent Trajectory Sandbox Worker",
)


class TrajectoryTaskPayload(BaseModel):
    trajectory_id: str
    task_suite: str
    task_id: str
    model_id: str
    budget_limit_usd: float = Field(default=2.00, ge=0.01)
    max_turns: int = Field(default=20, ge=1, le=50)
    metadata: Optional[Dict[str, Any]] = None


@app.get("/healthz")
async def health_check():
    """Liveness and readiness probe for Cloud Run Gen2."""
    return {
        "status": "healthy",
        "service": "benchpress-sandbox-worker",
        "version": "1.0.0",
        "runtime": "python-3.12",
    }


async def _run_trajectory_job(payload: TrajectoryTaskPayload):
    """Background task executing the 13-state trajectory loop."""
    logger.info(f"Starting FSM engine for trajectory {payload.trajectory_id}")
    ctx = TrajectoryContext(
        trajectory_id=payload.trajectory_id,
        task_suite=payload.task_suite,
        task_id=payload.task_id,
        model_id=payload.model_id,
        budget_limit_usd=payload.budget_limit_usd,
        max_turns=payload.max_turns,
        metadata=payload.metadata or {},
    )
    engine = AsyncFsmEngine(context=ctx)
    result_ctx = await engine.run_trajectory()
    logger.info(
        f"Completed trajectory {payload.trajectory_id}: "
        f"resolved={result_ctx.resolved}, turns={result_ctx.current_turn}, cost=${result_ctx.accumulated_cost_usd:.4f}"
    )


@app.post("/execute-task")
async def execute_trajectory_task(
    payload: TrajectoryTaskPayload,
    background_tasks: BackgroundTasks,
    x_cloudtasks_queuename: Optional[str] = Header(None),
):
    """Cloud Tasks HTTP Push Target for asynchronous benchmark runs."""
    logger.info(
        f"Received benchmark task {payload.trajectory_id} for model {payload.model_id} "
        f"(queue: {x_cloudtasks_queuename or 'direct'})"
    )
    background_tasks.add_task(_run_trajectory_job, payload)
    return {
        "status": "PROCESSING",
        "trajectory_id": payload.trajectory_id,
        "model_id": payload.model_id,
        "task_id": payload.task_id,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
