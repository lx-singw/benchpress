"""
Benchpress Sandbox Worker: FastAPI Cloud Tasks Target, Evaluation Orchestrator & Live Stream.
"""

import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from fsm.states import TrajectoryContext, TrajectoryStatus
from fsm.engine import AsyncFSMRunner
from security.task_auth import verify_task_request
from orchestrator.service import OrchestratorService
from idempotency.service import IdempotencyService
from contracts.models import RunManifest, RunResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchpress.worker")

app = FastAPI(
    title="Benchpress Sandbox Worker & Orchestrator",
    version="1.0.0",
    description="Cloud Run Gen2 Evaluation Orchestrator, Task Dispatcher & FSM Execution Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator_service = OrchestratorService()
idempotency_service = IdempotencyService()


class OrchestrateRequest(BaseModel):
    event_id: str
    correlation_id: str
    segment_id: str = "swe_coding_python_interactive"


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


@app.post("/orchestrate")
async def orchestrate_evaluation(
    payload: OrchestrateRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Sovereign Evaluation Planning.
    Invokes Gemini 3.5+ planner, validates plan policy, persists RunManifests, and dispatches tasks.
    """
    logger.info(f"[Worker] Received /orchestrate for event '{payload.event_id}' (corr: {payload.correlation_id})")
    result = await orchestrator_service.orchestrate(
        event_id=payload.event_id,
        correlation_id=payload.correlation_id,
        segment_id=payload.segment_id,
    )
    if result.get("status") == "PLAN_REJECTED":
        return result
    return result


@app.post("/execute-run")
async def execute_run(
    manifest: RunManifest,
    authenticated: bool = Depends(verify_task_request),
    x_worker_id: Optional[str] = Header(None),
):
    """
    Cloud Tasks Target for Immutable Single-Run Execution with CAS Idempotency.
    """
    worker_id = x_worker_id or f"worker_instance_{os.getpid()}"
    logger.info(f"[Worker] Received /execute-run for run_key '{manifest.logical_run_key}' (worker: {worker_id})")

    async def _dummy_execution():
        # Execution placeholder wired to full run_service in Sprint 3 (IMP-04)
        return {
            "logical_run_key": manifest.logical_run_key,
            "status": "SUCCEEDED",
            "resolved": True,
        }

    outcome = await idempotency_service.execute_idempotent_run(
        run_key=manifest.logical_run_key,
        worker_id=worker_id,
        execution_coro=_dummy_execution,
    )

    if outcome.get("status") == "LEASE_HELD":
        raise HTTPException(status_code=429, detail="Active lease held by another worker. Retry later.")
    if outcome.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Run manifest not found.")

    return outcome


# Legacy / Prototype endpoints preserved for backward compatibility
@app.post("/execute-task")
async def execute_trajectory_task(
    payload: TrajectoryTaskPayload,
    background_tasks: BackgroundTasks,
    x_cloudtasks_queuename: Optional[str] = Header(None),
    x_benchpress_hmac: Optional[str] = Header(None),
):
    """Legacy Cloud Tasks Target for prototype asynchronous runs."""
    logger.info(
        f"[Worker] Received legacy task {payload.trajectory_id} for model {payload.model_id}"
    )

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


async def _run_trajectory_job(payload: TrajectoryTaskPayload):
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
    await broadcast_trajectory_event(payload.trajectory_id, {
        "type": "TRAJECTORY_FINISHED",
        "status": result_ctx.status.value,
        "pass_at_1": result_ctx.pass_at_1,
        "turns_count": result_ctx.current_turn,
        "total_cost_usd": result_ctx.accumulated_cost_usd,
    })


async def broadcast_trajectory_event(trajectory_id: str, event_data: Dict[str, Any]):
    if trajectory_id in active_connections:
        for ws in active_connections[trajectory_id]:
            try:
                await ws.send_json(event_data)
            except Exception:
                pass


@app.websocket("/ws/trajectories/{trajectory_id}")
async def websocket_trajectory_stream(websocket: WebSocket, trajectory_id: str):
    await websocket.accept()
    if trajectory_id not in active_connections:
        active_connections[trajectory_id] = []
    active_connections[trajectory_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[trajectory_id].remove(websocket)
        if not active_connections[trajectory_id]:
            del active_connections[trajectory_id]


def ctx_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level="info")
