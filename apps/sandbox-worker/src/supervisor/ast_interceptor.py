"""
AST Interceptor: Schema Diff & Signature Parser for Tool Calls.
"""

import ast
import json
import logging
from typing import Dict, Any, Tuple, Optional, List
from tools.registry import ToolRegistry

logger = logging.getLogger("benchpress.supervisor.ast_interceptor")


class AstInterceptor:
    """Validates syntax and parameter conformance of emitted tool calls before execution."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()

    def intercept_and_validate(self, tool_name: str, raw_arguments: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate syntax, JSON parsing, and schema conformance of raw tool call."""
        # 1. Parse JSON if arguments are passed as string
        parsed_args = raw_arguments
        if isinstance(raw_arguments, str):
            try:
                parsed_args = json.loads(raw_arguments)
            except json.JSONDecodeError as json_err:
                return False, f"JSONDecodeError in tool arguments: {json_err.msg}", None

        if not isinstance(parsed_args, dict):
            return False, f"Invalid arguments format: expected dict, got {type(parsed_args).__name__}", None

        # 2. Check if tool exists
        tool_def = self.registry.get_tool_definition(tool_name)
        if not tool_def:
            # Check if name is slightly mangled (e.g. "read_file" vs "readFile")
            return False, f"Unknown tool '{tool_name}'", parsed_args

        # 3. Parameter Schema Conformance
        for req in tool_def.required:
            if req not in parsed_args:
                # Check for legacy alias substitutions (e.g. 'file_path' -> 'path')
                return False, f"Missing required parameter '{req}' for tool '{tool_name}'", parsed_args

        # 4. If code is supplied in editHunk or writeFile, parse AST
        if tool_name in ("writeFile", "editHunk") and "replacement_content" in parsed_args:
            path = parsed_args.get("path", "")
            code_content = parsed_args.get("replacement_content", "")
            if path.endswith(".py") and code_content:
                try:
                    ast.parse(code_content)
                except SyntaxError as syn_err:
                    return False, f"SyntaxError in replacement code: {syn_err.msg} at line {syn_err.lineno}", parsed_args

        return True, None, parsed_args
