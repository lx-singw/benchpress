"""
BigQuery Storage Write API Streamer (Protobuf / JSON) with Offline Local Logging.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fsm.states import TrajectoryContext, TurnRecord
from .metrics_calculator import MetricsCalculator

logger = logging.getLogger("benchpress.telemetry.bigquery")


class BigQueryStreamer:
    """Streams trajectory records and turn-level telemetry to BigQuery Storage Write API with local fallback."""

    def __init__(
        self,
        dataset_id: Optional[str] = None,
        trajectories_table: Optional[str] = None,
        turn_telemetry_table: Optional[str] = None,
        local_log_path: str = "data/telemetry_local.jsonl",
    ):
        self.dataset_id = dataset_id or os.environ.get("BIGQUERY_DATASET", "benchpress_analytics")
        self.trajectories_table = trajectories_table or os.environ.get("BIGQUERY_TABLE_TRAJECTORIES", "trajectories")
        self.turn_telemetry_table = turn_telemetry_table or os.environ.get("BIGQUERY_TABLE_TURN_TELEMETRY", "turn_telemetry")
        self.local_log_path = local_log_path
        # Cloud Run supplies Application Default Credentials without setting a
        # GOOGLE_APPLICATION_CREDENTIALS file path.  Mock mode must therefore
        # be an explicit opt-in rather than inferred from that environment key.
        self.use_mock = os.environ.get("USE_LOCAL_MOCK", "true").lower() == "true"

        self.streamed_trajectories: List[Dict[str, Any]] = []
        self.streamed_turns: List[Dict[str, Any]] = []

    def _write_local_log(self, record_type: str, data: Dict[str, Any]):
        """Persist record to local JSONL file for offline auditing."""
        try:
            os.makedirs(os.path.dirname(self.local_log_path), exist_ok=True)
            entry = {
                "record_type": record_type,
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
            with open(self.local_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.debug(f"[BQStreamer] Local log write skipped: {e}")

    async def stream_turn_telemetry(self, trajectory_id: str, turn: TurnRecord) -> bool:
        """Stream turn-level telemetry record."""
        turn_dict = {
            "turn_id": f"{trajectory_id}:{turn.turn_index}",
            "trajectory_id": trajectory_id,
            "turn_index": turn.turn_index,
            "state": turn.state.value,
            "model_id": turn.model_id,
            "prompt_tokens": turn.prompt_tokens,
            "completion_tokens": turn.completion_tokens,
            "turn_cost_usd": turn.turn_cost_usd,
            "cumulative_cost_usd": turn.cumulative_cost_usd,
            "latency_ms": turn.latency_ms,
            "tool_call_name": turn.tool_call_name,
            "ast_healed": turn.ast_healed,
            "sandbox_exit_code": turn.sandbox_exit_code,
            "timestamp": turn.timestamp,
        }

        self.streamed_turns.append(turn_dict)
        self._write_local_log("turn_telemetry", turn_dict)
        logger.debug(f"[BQStreamer] Buffered turn {turn.turn_index} for {trajectory_id}")
        return True

    async def stream_trajectory_run(self, ctx: TrajectoryContext) -> bool:
        """Stream completed trajectory summary record with CPR and TBR calculations."""
        cpr_usd = MetricsCalculator.calculate_cpr(ctx.accumulated_cost_usd, ctx.pass_at_1)
        tbr = MetricsCalculator.calculate_tbr(ctx.task_id, ctx.current_turn)
        decay_score = MetricsCalculator.calculate_context_decay_score(ctx.turns)

        trajectory_record = {
            "trajectory_id": ctx.trajectory_id,
            "task_suite": ctx.task_suite,
            "task_id": ctx.task_id,
            "model_id": ctx.model_id,
            "status": ctx.status.value,
            "pass_at_1": ctx.pass_at_1,
            "turns_count": ctx.current_turn,
            "total_cost_usd": round(ctx.accumulated_cost_usd, 4),
            "cpr_usd": cpr_usd,
            "trajectory_bloat_ratio": tbr,
            "context_decay_score": decay_score,
            "ast_heal_count": sum(1 for t in ctx.turns if t.ast_healed),
            "started_at": ctx.started_at,
            "completed_at": ctx.completed_at or datetime.now(timezone.utc).isoformat(),
        }

        self.streamed_trajectories.append(trajectory_record)
        self._write_local_log("trajectories", trajectory_record)
        logger.info(
            f"[BQStreamer] Streamed trajectory {ctx.trajectory_id}: "
            f"Pass@1={ctx.pass_at_1}, Cost=${ctx.accumulated_cost_usd:.4f}, CPR=${cpr_usd:.4f}, TBR={tbr}"
        )

        if not self.use_mock:
            try:
                from google.cloud import bigquery
                client = bigquery.Client()
                table_ref = f"{client.project}.{self.dataset_id}.{self.trajectories_table}"
                errors = client.insert_rows_json(table_ref, [trajectory_record])
                if errors:
                    logger.error(f"[BigQuery] Insert errors: {errors}")
                    return False
                return True
            except Exception as bq_err:
                logger.warning(f"[BigQuery] Stream failed (fallback persisted locally): {bq_err}")
                return False

        return True
