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
from execution.run_service import RunExecutionService
from aggregation.aggregator import ConfigurationAggregator
from aggregation.sufficiency import SufficiencyEvaluator
from policy.canary import CanaryExecutor
from policy.promotion import PolicyPromotionService
from policy.rollback import PolicyRollbackService
from policy.repository import get_policy_repository
from ledger.firestore import get_ledger
from contracts.models import RunManifest, RunResult, Aggregate, CanaryResult, DecisionReceipt
from contracts.states import ExperimentState, InternalOutcome, PublicDecision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchpress.worker")

app = FastAPI(
    title="Benchpress Sandbox Worker & Policy Governor",
    version="1.0.0",
    description="Cloud Run Gen2 Evaluation Orchestrator, Sandboxed Execution & Policy Promotion Engine",
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
run_execution_service = RunExecutionService()
aggregator = ConfigurationAggregator()
sufficiency_evaluator = SufficiencyEvaluator()
canary_executor = CanaryExecutor()
promotion_service = PolicyPromotionService()
rollback_service = PolicyRollbackService()
policy_repo = get_policy_repository()
ledger = get_ledger()


class OrchestrateRequest(BaseModel):
    event_id: str
    correlation_id: str
    segment_id: str = "swe_coding_python_interactive"


class AggregateRequest(BaseModel):
    experiment_id: str
    correlation_id: str
    baseline_configuration_id: str
    candidate_configuration_id: str
    task_segment_id: str = "swe_coding_python_interactive"


class CanaryRequest(BaseModel):
    experiment_id: str
    correlation_id: str
    task_segment_id: str = "swe_coding_python_interactive"
    baseline_policy_version: str
    candidate_policy_version: str
    candidate_configuration_id: str
    canary_task_id: str = "TASK-001"


class TrajectoryTaskPayload(BaseModel):
    trajectory_id: str
    task_suite: str = Field(default="SWE_BENCH_VERIFIED")
    task_id: str = Field(default="django__django-11099")
    model_id: str = Field(default="gemini-2.5-pro")
    budget_limit_usd: float = Field(default=2.00, ge=0.01)
    max_turns: int = Field(default=20, ge=1, le=50)
    metadata: Optional[Dict[str, Any]] = None


active_connections: Dict[str, List[WebSocket]] = {}


@app.get("/healthz")
async def health_check():
    """Liveness probe."""
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
    """
    logger.info(f"[Worker] Received /orchestrate for event '{payload.event_id}' (corr: {payload.correlation_id})")
    result = await orchestrator_service.orchestrate(
        event_id=payload.event_id,
        correlation_id=payload.correlation_id,
        segment_id=payload.segment_id,
    )
    return result


@app.post("/execute-run")
async def execute_run(
    manifest: RunManifest,
    authenticated: bool = Depends(verify_task_request),
    x_worker_id: Optional[str] = Header(None),
):
    """
    Cloud Tasks Target for Sandboxed Run Execution with CAS Idempotency.
    """
    worker_id = x_worker_id or f"worker_instance_{os.getpid()}"
    logger.info(f"[Worker] Received /execute-run for run_key '{manifest.logical_run_key}' (worker: {worker_id})")

    async def _execute_sandboxed():
        return await run_execution_service.execute_run(
            manifest=manifest,
            worker_id=worker_id,
        )

    outcome = await idempotency_service.execute_idempotent_run(
        run_key=manifest.logical_run_key,
        worker_id=worker_id,
        execution_coro=_execute_sandboxed,
    )

    if outcome.get("status") == "LEASE_HELD":
        raise HTTPException(status_code=429, detail="Active lease held by another worker. Retry later.")
    if outcome.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Run manifest not found.")

    return outcome


@app.post("/aggregate")
async def aggregate_experiment_results(
    payload: AggregateRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Aggregation, Stopping Evaluation and Sufficiency Decision.
    """
    logger.info(f"[Worker] Received /aggregate for experiment '{payload.experiment_id}'")

    # Fetch all run results for experiment from ledger
    all_results = [
        RunResult.model_validate(res)
        for res in ledger.results.values()
        if res.get("experiment_id") == payload.experiment_id
    ]

    base_results = [r for r in all_results if r.configuration_id == payload.baseline_configuration_id]
    cand_results = [r for r in all_results if r.configuration_id == payload.candidate_configuration_id]

    if not base_results or not cand_results:
        return {
            "status": "AWAITING_RUNS",
            "experiment_id": payload.experiment_id,
            "baseline_runs_count": len(base_results),
            "candidate_runs_count": len(cand_results),
        }

    base_agg = aggregator.aggregate_runs(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        configuration_id=payload.baseline_configuration_id,
        results=base_results,
    )

    cand_agg = aggregator.aggregate_runs(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        configuration_id=payload.candidate_configuration_id,
        results=cand_results,
    )

    outcome = sufficiency_evaluator.evaluate_outcome(base_agg, cand_agg)

    ledger.update_experiment_state(
        experiment_id=payload.experiment_id,
        target_state=ExperimentState.AGGREGATING,
        reason=f"Aggregation computed. Outcome: {outcome.value}",
    )

    return {
        "status": "AGGREGATED",
        "experiment_id": payload.experiment_id,
        "internal_outcome": outcome.value,
        "baseline_aggregate": base_agg.model_dump(mode="json"),
        "candidate_aggregate": cand_agg.model_dump(mode="json"),
    }


@app.post("/canary")
async def execute_canary_evaluation(
    payload: CanaryRequest,
    authenticated: bool = Depends(verify_task_request),
):
    """
    Cloud Tasks Target for Contained Canary Verification and Atomic Policy Promotion.
    """
    logger.info(f"[Worker] Received /canary for candidate '{payload.candidate_policy_version}'")

    canary_result = await canary_executor.execute_canary(
        experiment_id=payload.experiment_id,
        correlation_id=payload.correlation_id,
        baseline_policy_version=payload.baseline_policy_version,
        candidate_policy_version=payload.candidate_policy_version,
        candidate_config_id=payload.candidate_configuration_id,
        canary_task_id=payload.canary_task_id,
    )

    # Fetch aggregates from ledger
    base_agg_dict = next(
        (a for a in ledger.results.values() if a.get("configuration_id") != payload.candidate_configuration_id),
        None
    )

    # If canary passes -> Promote
    if canary_result.promotion_approved:
        ledger.update_experiment_state(
            experiment_id=payload.experiment_id,
            target_state=ExperimentState.DECIDED_PROMOTED,
            reason="Canary passed all guardrails. Policy promoted.",
        )
    else:
        ledger.update_experiment_state(
            experiment_id=payload.experiment_id,
            target_state=ExperimentState.DECIDED_STAY,
            reason=f"Canary failed: {canary_result.rollback_reason}",
        )

    return {
        "status": "CANARY_COMPLETED",
        "experiment_id": payload.experiment_id,
        "canary_result": canary_result.model_dump(mode="json"),
    }


# Legacy endpoints
@app.post("/execute-task")
async def execute_trajectory_task(
    payload: TrajectoryTaskPayload,
    background_tasks: BackgroundTasks,
    x_cloudtasks_queuename: Optional[str] = Header(None),
    x_benchpress_hmac: Optional[str] = Header(None),
):
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
