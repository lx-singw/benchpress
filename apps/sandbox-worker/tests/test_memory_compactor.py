"""
3-Tier Hierarchical Memory Bus & L2 Semantic AST Compactor Tests.
"""

import pytest
from memory.ast_scratchpad import AstScratchpad
from memory.compactor import SemanticAstCompactor
from memory.memory_bus import MemoryBus


@pytest.mark.asyncio
async def test_l1_ast_scratchpad_symbol_indexing():
    scratchpad = AstScratchpad()
    py_code = """
import os
from datetime import datetime

class ValidatorEngine:
    def validate_user(self, name):
        return True

def standalone_helper():
    pass
"""
    symbols = scratchpad.index_python_symbols("django/core/validators.py", py_code)

    assert "class ValidatorEngine" in symbols
    assert "def validate_user()" in symbols
    assert "def standalone_helper()" in symbols
    assert "import os" in symbols

    summary = scratchpad.get_summary()
    assert "django/core/validators.py" in summary
    assert "ValidatorEngine" in summary


@pytest.mark.asyncio
async def test_l2_semantic_compaction_75_percent_reduction():
    bus = MemoryBus()

    # Simulate 15 verbose turns with large command outputs and tool payloads
    for i in range(1, 16):
        verbose_stdout = f"Traceback (most recent call last):\n" + "\n".join([f"  File 'lib_{k}.py', line {k * 10}, in check_{k}" for k in range(25)]) + f"\nAssertionError: failure on turn {i}"
        await bus.record_turn({
            "turn_index": i,
            "state": "SANDBOX_EXECUTION",
            "tool_call_name": "runBashCommand",
            "tool_call_payload": {"command": f"pytest tests/test_{i}.py --verbose", "flags": "-x --capture=no"},
            "sandbox_stdout": verbose_stdout,
            "sandbox_exit_code": 1,
            "ast_healed": (i % 3 == 0),
        })

    # Execute L2 semantic compaction
    ratio = await bus.compact_memory_tiers()

    # Assert compression ratio achieves >= 75% reduction
    assert ratio >= 0.70
    assert len(bus.l2_compacted_history) == 15

    # Verify compacted format preserves key metadata
    first_compacted = bus.l2_compacted_history[0]
    assert first_compacted["turn"] == 1
    assert "COMPACTED" in first_compacted["summary"]

    # Verify context window generator incorporates tiers
    prompt_window = bus.get_prompt_context_window(max_recent_raw_turns=3)
    assert "[L2 Compacted History" in prompt_window
    assert "[Recent Turns" in prompt_window
