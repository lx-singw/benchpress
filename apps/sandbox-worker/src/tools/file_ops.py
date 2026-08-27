"""
AST-Aware File Operations Tool (`readFile`, `writeFile`, `editHunk`).
"""

import os
import ast
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("benchpress.tools.file_ops")


class FileOpsTool:
    """Provides safe, sandboxed file reading, writing, and AST-aware diff replacement."""

    @staticmethod
    def _resolve_safe_path(workspace_root: str, relative_path: str) -> str:
        """Ensure file path does not escape workspace directory boundaries."""
        abs_root = os.path.abspath(workspace_root)
        target = os.path.abspath(os.path.join(abs_root, relative_path.lstrip("/\\")))
        if not target.startswith(abs_root):
            raise ValueError(f"Path traversal detected: {relative_path} escapes workspace {workspace_root}")
        return target

    @classmethod
    def read_file(
        cls,
        workspace_root: str,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Read lines from file in workspace."""
        try:
            target_path = cls._resolve_safe_path(workspace_root, path)
            if not os.path.exists(target_path):
                return {"success": False, "error": f"FileNotFoundError: {path} does not exist"}

            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s = max(1, start_line or 1) - 1
            e = min(total_lines, end_line or total_lines)

            selected_lines = lines[s:e]
            content = "".join(selected_lines)

            return {
                "success": True,
                "path": path,
                "total_lines": total_lines,
                "start_line": s + 1,
                "end_line": e,
                "content": content,
            }
        except Exception as err:
            return {"success": False, "error": str(err)}

    @classmethod
    def write_file(cls, workspace_root: str, path: str, content: str) -> Dict[str, Any]:
        """Create or overwrite a file."""
        try:
            target_path = cls._resolve_safe_path(workspace_root, path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True, "path": path, "bytes_written": len(content.encode("utf-8"))}
        except Exception as err:
            return {"success": False, "error": str(err)}

    @classmethod
    def edit_hunk(
        cls,
        workspace_root: str,
        path: str,
        target_content: str,
        replacement_content: str,
    ) -> Dict[str, Any]:
        """Replace exact code hunk in file."""
        try:
            target_path = cls._resolve_safe_path(workspace_root, path)
            if not os.path.exists(target_path):
                return {"success": False, "error": f"FileNotFoundError: {path} does not exist"}

            with open(target_path, "r", encoding="utf-8") as f:
                original = f.read()

            if target_content not in original:
                # Provide line hint
                return {
                    "success": False,
                    "error": f"Target content not found in {path}. Ensure whitespace and indentation match exactly.",
                }

            # Check if replacement causes syntax error in Python files
            if path.endswith(".py"):
                candidate = original.replace(target_content, replacement_content, 1)
                try:
                    ast.parse(candidate)
                except SyntaxError as syn_err:
                    return {
                        "success": False,
                        "error": f"SyntaxError in replacement: {syn_err.msg} at line {syn_err.lineno}",
                    }

            updated = original.replace(target_content, replacement_content, 1)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(updated)

            return {
                "success": True,
                "path": path,
                "modified": True,
                "message": f"Successfully applied hunk edit to {path}",
            }
        except Exception as err:
            return {"success": False, "error": str(err)}
