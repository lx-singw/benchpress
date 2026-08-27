"""
Vertex AI Gemini Fine-Tuning JSONL Exporter (`VertexExporter`).
Exports formatted conversation datasets into Vertex AI Gemini 3.5 Flash fine-tuning `.jsonl` files.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("benchpress.distillation.vertex_exporter")


class VertexExporter:
    """Exports structured SFT and DPO records into JSONL format for GCP Vertex AI."""

    @classmethod
    def export_sft_to_jsonl(cls, dataset: List[Dict[str, Any]], output_filepath: str) -> int:
        """Write SFT dataset records to file."""
        out_path = Path(output_filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        with out_path.open("w", encoding="utf-8") as f:
            for record in dataset:
                f.write(json.dumps(record) + "\n")
                count += 1

        logger.info(f"[VertexExporter] Exported {count} SFT records to {output_filepath}")
        return count

    @classmethod
    def export_dpo_to_jsonl(cls, dataset: List[Dict[str, Any]], output_filepath: str) -> int:
        """Write DPO preference pairs to file."""
        out_path = Path(output_filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        with out_path.open("w", encoding="utf-8") as f:
            for record in dataset:
                f.write(json.dumps(record) + "\n")
                count += 1

        logger.info(f"[VertexExporter] Exported {count} DPO records to {output_filepath}")
        return count
