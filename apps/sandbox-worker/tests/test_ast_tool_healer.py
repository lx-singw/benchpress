"""
Supervisor AST Tool Interceptor & Autonomous Dynamic Patch Injection Tests.
"""

import pytest
from supervisor.ast_interceptor import AstInterceptor
from supervisor.ast_healer import AstHealer
from tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_ast_interceptor_valid_and_invalid():
    registry = ToolRegistry()
    interceptor = AstInterceptor(registry=registry)

    # 1. Valid tool call
    valid_args = {"path": "django/core/validators.py", "target_content": "old", "replacement_content": "new"}
    is_valid, err, parsed = interceptor.intercept_and_validate("editHunk", valid_args)
    assert is_valid is True
    assert err is None
    assert parsed["path"] == "django/core/validators.py"

    # 2. Missing required parameter
    bad_args = {"target_content": "old"}
    is_valid, err, _ = interceptor.intercept_and_validate("editHunk", bad_args)
    assert is_valid is False
    assert "Missing required parameter" in err

    # 3. Unknown tool
    is_valid, err, _ = interceptor.intercept_and_validate("unknown_custom_tool", {})
    assert is_valid is False
    assert "Unknown tool" in err


@pytest.mark.asyncio
async def test_ast_healer_dynamic_repair_and_injection():
    healer = AstHealer()

    # Broken tool call with legacy parameter aliases and mangled name
    mangled_tool = "edit_file"
    mangled_args = {
        "file_path": "django/core/validators.py",
        "hunk": "regex = r'^[\\w.@+-]+$'",
        "replacement": "```python\nregex = r'\\A[\\w.@+-]+\\Z'\n```",
    }

    healed_ok, rep_tool, rep_args, trace = await healer.heal_tool_call(
        mangled_tool,
        mangled_args,
        "Missing required parameter 'path'",
    )

    assert healed_ok is True
    assert rep_tool == "editHunk"
    assert rep_args["path"] == "django/core/validators.py"
    assert rep_args["target_content"] == "regex = r'^[\\w.@+-]+$'"
    # Markdown backticks stripped
    assert "```" not in rep_args["replacement_content"]
    assert "regex = r'\\A[\\w.@+-]+\\Z'" in rep_args["replacement_content"]
    assert healer.healing_events_count == 1
