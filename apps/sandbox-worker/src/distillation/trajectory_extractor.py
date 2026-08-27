"""
BigQuery Pass@1 Trajectory Extractor (`TrajectoryExtractor`).
Extracts verified passing agent trajectories with Trajectory Bloat Ratio < 1.15 from BigQuery or memory.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger("benchpress.distillation.extractor")


class TrajectoryExtractor:
    """Filters BigQuery records for high-value distillation training samples."""

    @classmethod
    def filter_golden_trajectories(
        cls,
        raw_trajectories: List[Dict[str, Any]],
        max_bloat_ratio: float = 1.15
    ) -> List[Dict[str, Any]]:
        """Filter for trajectories where Pass@1 == True, resolved == True, and bloat <= max_bloat_ratio."""
        golden: List[Dict[str, Any]] = []

        for traj in raw_trajectories:
            is_pass = traj.get("pass_at_1", False) or traj.get("resolved", False)
            bloat = traj.get("trajectory_bloat_ratio", 1.0)

            if is_pass and bloat <= max_bloat_ratio:
                golden.append(traj)

        logger.info(f"[TrajectoryExtractor] Extracted {len(golden)}/{len(raw_trajectories)} golden trajectories")
        return golden
