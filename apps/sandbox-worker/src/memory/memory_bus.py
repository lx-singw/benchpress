"""
Unified 3-Tier Hierarchical Memory Bus (L1 Scratchpad, L2 Semantic Compactor, L3 Episodic Store).
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from .ast_scratchpad import AstScratchpad
from .compactor import SemanticAstCompactor

logger = logging.getLogger("benchpress.memory.bus")


class MemoryBus:
    """Coordinates 3-tier memory across L1 working context, L2 semantic compaction, and L3 episodic cache."""

    def __init__(self):
        self.l1_scratchpad = AstScratchpad()
        self.l2_compacted_history: List[Dict[str, Any]] = []
        self.l3_episodic_store: Dict[str, Any] = {}
        self.raw_turn_history: List[Dict[str, Any]] = []
        self.latest_compression_ratio: float = 0.0

    async def record_turn(self, turn_dict: Dict[str, Any]):
        """Append turn to raw memory stream."""
        self.raw_turn_history.append(turn_dict)

    async def set_working_context(self, key: str, value: Any):
        """Set item in L1 memory."""
        self.l1_scratchpad.add_note(f"{key}: {str(value)[:100]}")

    async def compact_memory_tiers(self) -> float:
        """Trigger L2 semantic compaction over accumulated turn history."""
        compacted, ratio = SemanticAstCompactor.compact_turn_history(self.raw_turn_history)
        self.l2_compacted_history = compacted
        self.latest_compression_ratio = ratio
        return ratio

    def get_prompt_context_window(self, max_recent_raw_turns: int = 3) -> str:
        """Build compressed, high-density context prompt for the LLM."""
        sections = []

        # 1. L1 Working Symbol Cache
        sections.append(self.l1_scratchpad.get_summary())

        # 2. L2 Compacted Historical Turns (Older than recent raw turns)
        if len(self.raw_turn_history) > max_recent_raw_turns:
            older_turns = self.raw_turn_history[:-max_recent_raw_turns]
            compacted_older, _ = SemanticAstCompactor.compact_turn_history(older_turns)
            sections.append(f"[L2 Compacted History ({len(compacted_older)} turns)]: {str(compacted_older)}")

        # 3. Recent Raw Turns (Full Fidelity)
        recent_turns = self.raw_turn_history[-max_recent_raw_turns:]
        sections.append(f"[Recent Turns ({len(recent_turns)})]: {str(recent_turns)}")

        return "\n\n".join(sections)
