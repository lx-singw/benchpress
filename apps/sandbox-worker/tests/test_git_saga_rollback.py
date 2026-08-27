"""
Compensating Git-Tree Saga Snapshotting & Atomic Rollback Tests.
"""

import pytest
import os
from sandbox.git_saga import GitSagaTracker
from tools.file_ops import FileOpsTool


@pytest.mark.asyncio
async def test_git_tree_snapshot_and_atomic_rollback(temp_git_workspace):
    ws = temp_git_workspace

    # 1. Capture clean snapshot
    initial_hash = await GitSagaTracker.capture_snapshot(ws)
    assert initial_hash not in ("", "empty-tree-hash", "err-tree-hash")

    # 2. Mutate file with breaking syntax
    broken_content = "def broken():\n    syntax error !!\n"
    FileOpsTool.write_file(ws, "app.py", broken_content)

    read_broken = FileOpsTool.read_file(ws, "app.py")
    assert "syntax error !!" in read_broken.get("content", "")

    # 3. Execute atomic compensating rollback
    rolled_back = await GitSagaTracker.rollback_to_snapshot(ws, initial_hash)
    assert rolled_back is True

    # 4. Verify file restored to clean state
    read_restored = FileOpsTool.read_file(ws, "app.py")
    assert "x = 1" in read_restored.get("content", "")
    assert "syntax error" not in read_restored.get("content", "")
