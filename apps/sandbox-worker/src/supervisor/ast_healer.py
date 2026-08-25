"""
Autonomous AST Tool-Healer for Tool Schema Signatures and Syntax Repair.
"""

import ast
import json
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("benchpress.supervisor.ast_healer")


class AstHealer:
    """Detects, intercepts, and heals malformed LLM tool call ASTs and JSON schemas."""

    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.model_name = model_name
        self.healed_count = 0

    def validate_tool_call(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate if the tool payload has correct syntax and required parameters."""
        if not isinstance(payload, dict):
            return False, "Payload must be a dictionary"

        if "tool" not in payload:
            return False, "Missing 'tool' identifier in payload"

        # If payload contains Python code replacement, check AST parseability
        if "replacement" in payload and isinstance(payload["replacement"], str):
            try:
                ast.parse(payload["replacement"])
            except SyntaxError as e:
                return False, f"SyntaxError in replacement code: {e.msg} at line {e.lineno}"

        return True, None

    async def repair_payload(
        self,
        broken_payload: Dict[str, Any],
        error_message: str,
    ) -> Tuple[Dict[str, Any], bool]:
        """Perform autonomous AST repair on broken tool call payload."""
        logger.info(f"Initiating AST Tool Healing for error: {error_message}")
        repaired = dict(broken_payload)

        # Autonomous schema normalization
        if "tool" not in repaired and "name" in repaired:
            repaired["tool"] = repaired.pop("name")

        if "arguments" in repaired and isinstance(repaired["arguments"], str):
            try:
                repaired["arguments"] = json.loads(repaired["arguments"])
            except json.JSONDecodeError:
                pass

        if "path" not in repaired and "file_path" in repaired:
            repaired["path"] = repaired.pop("file_path")

        # Fix minor syntax issues in replacement string if any
        if "replacement" in repaired and isinstance(repaired["replacement"], str):
            code_str = repaired["replacement"]
            # Deduplicate broken triple backticks or markdown fences
            if code_str.startswith("```python") or code_str.startswith("```"):
                code_str = "\n".join(code_str.splitlines()[1:])
            if code_str.endswith("```"):
                code_str = "\n".join(code_str.splitlines()[:-1])
            repaired["replacement"] = code_str.strip()

        self.healed_count += 1
        return repaired, True
