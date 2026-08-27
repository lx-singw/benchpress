"""
Benchpress Sandbox Worker: FastAPI Cloud Tasks Target Service & Real-Time WebSocket Streaming.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Set
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks, WebSocket, WebSocketDisconnect
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


class ConnectionManager:
    """Manages active WebSocket connections by trajectory_id and global broadcast."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, trajectory_id: Optional[str] = None):
        await websocket.accept()
        if trajectory_id:
            if trajectory_id not in self.active_connections:
                self.active_connections[trajectory_id] = set()
            self.active_connections[trajectory_id].add(websocket)
        else:
            self.global_connections.add(websocket)
        logger.info(f"WebSocket client connected (trajectory: {trajectory_id or 'global'})")

    def disconnect(self, websocket: WebSocket, trajectory_id: Optional[str] = None):
        if trajectory_id and trajectory_id in self.active_connections:
            self.active_connections[trajectory_id].discard(websocket)
            if not self.active_connections[trajectory_id]:
                del self.active_connections[trajectory_id]
        else:
            self.global_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected (trajectory: {trajectory_id or 'global'})")

    async def broadcast_event(self, event: Dict[str, Any]):
        """Broadcast event to both trajectory-specific and global listeners."""
        payload_text = json.dumps(event)
        traj_id = event.get("trajectory_id")

        targets = set(self.global_connections)
        if traj_id and traj_id in self.active_connections:
            targets.update(self.active_connections[traj_id])

        disconnected = []
        for ws in targets:
            try:
                await ws.send_text(payload_text)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, traj_id)


manager = ConnectionManager()


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
        "active_ws_connections": len(manager.global_connections) + sum(len(s) for s in manager.active_connections.values()),
    }


async def _run_trajectory_job(payload: TrajectoryTaskPayload):
    """Background task executing the 13-state trajectory loop with real-time WebSocket broadcasting."""
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

    async def _on_event(event: Dict[str, Any]):
        await manager.broadcast_event(event)

    engine = AsyncFsmEngine(context=ctx, on_event=_on_event)
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
        "stream_url": f"/ws/trajectories/{payload.trajectory_id}",
    }


@app.websocket("/ws/trajectories/{trajectory_id}")
async def websocket_trajectory_stream(websocket: WebSocket, trajectory_id: str):
    """Real-time turn and state transition WebSocket stream for a specific trajectory."""
    await manager.connect(websocket, trajectory_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG", "trajectory_id": trajectory_id}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, trajectory_id)


@app.websocket("/ws/events")
async def websocket_global_stream(websocket: WebSocket):
    """Global multi-tenant stream broadcasting all active agent events."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
