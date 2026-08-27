"""
Benchpress Sandbox Worker: FastAPI Cloud Tasks Target & WebSocket Live Event Emitter.
"""

import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from fsm.states import TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchpress.worker")

app = FastAPI(
    title="Benchpress Sandbox Worker",
    version="1.0.0",
    description="Cloud Run Gen2 Asynchronous Agent Trajectory Sandbox Worker & 13-State FSM Runner",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrajectoryTaskPayload(BaseModel):
    trajectory_id: str
    task_suite: str = Field(default="SWE_BENCH_VERIFIED")
    task_id: str = Field(default="django__django-11099")
    model_id: str = Field(default="gemini-2.5-pro")
    budget_limit_usd: float = Field(default=2.00, ge=0.01)
    max_turns: int = Field(default=20, ge=1, le=50)
    metadata: Optional[Dict[str, Any]] = None


# Active WebSocket connections dictionary: trajectory_id -> List[WebSocket]
active_connections: Dict[str, List[WebSocket]] = {}


async def broadcast_trajectory_event(trajectory_id: str, event_data: Dict[str, Any]):
    """Broadcast real-time state change or turn completion to connected WebSocket clients."""
    if trajectory_id in active_connections:
        for ws in active_connections[trajectory_id]:
            try:
                await ws.send_json(event_data)
            except Exception:
                pass


@app.get("/healthz")
async def health_check():
    """Liveness and readiness probe for Cloud Run Gen2."""
    return {
        "status": "healthy",
        "service": "benchpress-sandbox-worker",
        "version": "1.0.0",
        "runtime": "python-3.12",
        "active_trajectories": len(active_connections),
    }


async def _run_trajectory_job(payload: TrajectoryTaskPayload):
    """Background task executing the full 13-state FSM trajectory runner."""
    logger.info(f"[Worker] Initiating AsyncFSMRunner for trajectory {payload.trajectory_id}")
    ctx = TrajectoryContext(
        trajectory_id=payload.trajectory_id,
        task_suite=payload.task_suite,
        task_id=payload.task_id,
        model_id=payload.model_id,
        budget_limit_usd=payload.budget_limit_usd,
        max_turns=payload.max_turns,
        metadata=payload.metadata or {},
    )

    runner = AsyncFSMRunner(context=ctx)
    result_ctx = await runner.run()
    logger.info(
        f"[Worker] Trajectory {payload.trajectory_id} finished: "
        f"status={result_ctx.status.value}, pass_at_1={result_ctx.pass_at_1}, "
        f"turns={result_ctx.current_turn}, cost=${result_ctx.accumulated_cost_usd:.4f}"
    )

    await broadcast_trajectory_event(payload.trajectory_id, {
        "type": "TRAJECTORY_FINISHED",
        "status": result_ctx.status.value,
        "pass_at_1": result_ctx.pass_at_1,
        "turns_count": result_ctx.current_turn,
        "total_cost_usd": result_ctx.accumulated_cost_usd,
    })


@app.post("/execute-task")
async def execute_trajectory_task(
    payload: TrajectoryTaskPayload,
    background_tasks: BackgroundTasks,
    x_cloudtasks_queuename: Optional[str] = Header(None),
    x_benchpress_hmac: Optional[str] = Header(None),
):
    """Cloud Tasks HTTP Push Target for asynchronous benchmark runs."""
    logger.info(
        f"[Worker] Received benchmark task {payload.trajectory_id} for model {payload.model_id} "
        f"(task: {payload.task_id}, queue: {x_cloudtasks_queuename or 'direct'})"
    )

    # Optional HMAC check if secret is configured and not in mock dev mode
    if not settings.use_local_mock and x_benchpress_hmac:
        expected_sig = hmac.new(
            settings.benchpress_hmac_secret.encode(),
            payload.trajectory_id.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_benchpress_hmac):
            raise HTTPException(status_code=403, detail="Invalid HMAC signature")

    background_tasks.add_task(_run_trajectory_job, payload)
    return {
        "status": "PROCESSING",
        "trajectory_id": payload.trajectory_id,
        "model_id": payload.model_id,
        "task_id": payload.task_id,
        "enqueued_at": ctx_now(),
    }


@app.websocket("/ws/trajectories/{trajectory_id}")
async def websocket_trajectory_stream(websocket: WebSocket, trajectory_id: str):
    """WebSocket stream for real-time turn waterfall and FSM state events."""
    await websocket.accept()
    if trajectory_id not in active_connections:
        active_connections[trajectory_id] = []
    active_connections[trajectory_id].append(websocket)
    logger.info(f"[WebSocket] Client connected for trajectory {trajectory_id}")

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[trajectory_id].remove(websocket)
        if not active_connections[trajectory_id]:
            del active_connections[trajectory_id]
        logger.info(f"[WebSocket] Client disconnected for trajectory {trajectory_id}")


def ctx_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level="info")
