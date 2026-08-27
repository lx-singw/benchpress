"""
Enterprise Trajectory Distillation Test Suite.
Verifies BigQuery Pass@1 extraction and Vertex AI Gemini SFT/DPO JSONL export.
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))

from src.distillation.trajectory_extractor import TrajectoryExtractor
from src.distillation.dataset_synthesizer import DatasetSynthesizer
from src.distillation.vertex_exporter import VertexExporter


def test_trajectory_extractor_filtering():
    """Verify TrajectoryExtractor selects only Pass@1 runs with low bloat ratio."""
    raw_runs = [
        {"trajectory_id": "run-1", "pass_at_1": True, "resolved": True, "trajectory_bloat_ratio": 1.05},
        {"trajectory_id": "run-2", "pass_at_1": False, "resolved": False, "trajectory_bloat_ratio": 1.50},
        {"trajectory_id": "run-3", "pass_at_1": True, "resolved": True, "trajectory_bloat_ratio": 1.40},  # Bloat > 1.15
    ]

    golden = TrajectoryExtractor.filter_golden_trajectories(raw_runs, max_bloat_ratio=1.15)
    assert len(golden) == 1
    assert golden[0]["trajectory_id"] == "run-1"


def test_dataset_synthesizer_and_vertex_export():
    """Verify conversion of golden trajectory to Vertex AI SFT JSONL."""
    sample_trajectory = {
        "trajectory_id": "traj-gold-01",
        "task_id": "django__django-11099",
        "problem_statement": "Fix validator regex trailing characters.",
        "turns": [
            {
                "turn_index": 1,
                "tool_call_name": "editHunk",
                "tool_call_payload": {"file": "validators.py", "diff": "..."},
                "sandbox_stdout": "Hunk applied successfully.",
            }
        ],
    }

    sft_record = DatasetSynthesizer.synthesize_sft_conversation(sample_trajectory)
    assert "messages" in sft_record
    assert len(sft_record["messages"]) >= 4

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "vertex_sft.jsonl"
        count = VertexExporter.export_sft_to_jsonl([sft_record], str(out_file))

        assert count == 1
        assert out_file.exists()

        lines = out_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert "messages" in parsed
