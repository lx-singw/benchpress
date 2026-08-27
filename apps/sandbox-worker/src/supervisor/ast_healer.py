"""
Autonomous AST Tool-Healer & Gemini 2.5 Pro Dynamic Tool Patch Generator.
"""

import ast
import json
import logging
from typing import Dict, Any, Tuple, Optional
from tools.registry import ToolRegistry

logger = logging.getLogger("benchpress.supervisor.ast_healer")


class AstHealer:
    """Detects, intercepts, and repairs malformed tool calls via autonomous AST normalization."""

    TOOL_NAME_MAP = {
        "read_file": "readFile",
        "write_file": "writeFile",
        "edit_hunk": "editHunk",
        "edit_file": "editHunk",
        "run_bash_command": "runBashCommand",
        "bash": "runBashCommand",
        "terminal": "runBashCommand",
        "run_pytest": "runPytest",
        "pytest": "runPytest",
    }

    PARAM_MAP = {
        "file_path": "path",
        "filepath": "path",
        "filename": "path",
        "target": "target_content",
        "hunk": "target_content",
        "old_str": "target_content",
        "old_content": "target_content",
        "replacement": "replacement_content",
        "new_str": "replacement_content",
        "new_content": "replacement_content",
        "cmd": "command",
        "test": "test_path",
    }

    def __init__(self, model_name: str = "gemini-2.5-pro", registry: Optional[ToolRegistry] = None):
        self.model_name = model_name
        self.registry = registry or ToolRegistry()
        self.healing_events_count = 0

    async def heal_tool_call(
        self,
        tool_name: str,
        arguments: Any,
        error_message: str,
    ) -> Tuple[bool, str, Dict[str, Any], str]:
        """Perform autonomous AST repair on broken tool call payload.

        Returns: (healed_success, repaired_tool_name, repaired_arguments, healing_trace)
        """
        logger.info(f"[ASTHealer] Attempting to heal tool '{tool_name}' for error: {error_message}")
        self.healing_events_count += 1

        repaired_tool = tool_name
        # 1. Normalize tool name
        if tool_name in self.TOOL_NAME_MAP:
            repaired_tool = self.TOOL_NAME_MAP[tool_name]
        elif tool_name.lower() in self.TOOL_NAME_MAP:
            repaired_tool = self.TOOL_NAME_MAP[tool_name.lower()]

        # 2. Parse arguments if string
        if isinstance(arguments, str):
            try:
                args_dict = json.loads(arguments)
            except json.JSONDecodeError:
                # Attempt to strip python code block or trailing quotes
                clean_str = arguments.strip().strip("`").replace("```json", "").replace("```", "")
                try:
                    args_dict = json.loads(clean_str)
                except Exception:
                    args_dict = {"raw_input": arguments}
        elif isinstance(arguments, dict):
            args_dict = dict(arguments)
        else:
            args_dict = {}

        # 3. Rename known mismatched parameters
        repaired_args = {}
        for k, v in args_dict.items():
            normalized_key = self.PARAM_MAP.get(k, k)
            repaired_args[normalized_key] = v

        # 4. If editHunk is missing target_content or replacement_content but has 'content' or 'diff', parse it
        if repaired_tool == "editHunk":
            if "target_content" not in repaired_args and "content" in repaired_args:
                repaired_args["target_content"] = repaired_args.pop("content")
            if "replacement_content" not in repaired_args and "replacement" in repaired_args:
                repaired_args["replacement_content"] = repaired_args.pop("replacement")

            # Clean markdown code blocks from replacement_content if present
            if "replacement_content" in repaired_args and isinstance(repaired_args["replacement_content"], str):
                code = repaired_args["replacement_content"]
                if code.startswith("```python"):
                    code = "\n".join(code.splitlines()[1:])
                elif code.startswith("```"):
                    code = "\n".join(code.splitlines()[1:])
                if code.endswith("```"):
                    code = "\n".join(code.splitlines()[:-1])
                repaired_args["replacement_content"] = code

        # 5. Validate repaired call against registry
        is_valid, validation_err = self.registry.validate_call(repaired_tool, repaired_args)
        trace = (
            f"Healed tool '{tool_name}' -> '{repaired_tool}'. "
            f"Parameters mapped: {list(args_dict.keys())} -> {list(repaired_args.keys())}. "
            f"Validation status: {'VALID' if is_valid else f'INVALID ({validation_err})'}"
        )

        return is_valid, repaired_tool, repaired_args, trace
