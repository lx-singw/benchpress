"""
BigQuery Storage Write API Streamer with Batching & In-Memory Fallback.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from fsm.states import TrajectoryContext, TurnResult

logger = logging.getLogger("benchpress.telemetry.bigquery")


class BigQueryStreamer:
    """Streams trajectory and turn-level telemetry to BigQuery."""

    def __init__(self, dataset_id: Optional[str] = None, table_id: Optional[str] = None):
        self.dataset_id = dataset_id or os.environ.get("BIGQUERY_DATASET", "benchpress_telemetry")
        self.table_id = table_id or os.environ.get("BIGQUERY_TABLE_TRAJECTORIES", "trajectory_runs")
        self.use_mock = os.environ.get("USE_LOCAL_MOCK", "true").lower() == "true" or not os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.buffered_records: List[Dict[str, Any]] = []

    async def stream_trajectory_run(self, ctx: TrajectoryContext) -> bool:
        """Stream completed trajectory summary record."""
        record = {
            "trajectory_id": ctx.trajectory_id,
            "task_suite": ctx.task_suite,
            "task_id": ctx.task_id,
            "model_id": ctx.model_id,
            "total_turns": ctx.current_turn,
            "total_cost_usd": ctx.accumulated_cost_usd,
            "resolved": ctx.resolved,
            "early_halted": ctx.early_halted,
            "halt_reason": ctx.halt_reason,
            "git_snapshots_count": len(ctx.git_snapshots),
        }

        if self.use_mock:
            self.buffered_records.append(record)
            logger.info(f"[MockBigQuery] Streamed trajectory record {ctx.trajectory_id}: {record}")
            return True

        try:
            from google.cloud import bigquery
            client = bigquery.Client()
            table_ref = f"{client.project}.{self.dataset_id}.{self.table_id}"
            errors = client.insert_rows_json(table_ref, [record])
            if errors:
                logger.error(f"BigQuery streaming errors: {errors}")
                return False
            return True
        except Exception as e:
            logger.warning(f"BigQuery stream failed (fallback buffered): {e}")
            self.buffered_records.append(record)
            return False
