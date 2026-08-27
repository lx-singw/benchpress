"""
L1 Working Memory Symbol Cache (<2k Tokens).
"""

import ast
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("benchpress.memory.scratchpad")


class AstScratchpad:
    """L1 fast in-memory cache for active file AST symbols, class hierarchies, and imports."""

    def __init__(self, token_limit: int = 2000):
        self.token_limit = token_limit
        self.symbol_table: Dict[str, List[str]] = {}
        self.active_files: Dict[str, str] = {}
        self.scratch_notes: List[str] = []

    def index_python_symbols(self, file_path: str, code_content: str) -> List[str]:
        """Extract classes, functions, and imports into L1 symbol table."""
        symbols = []
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(f"def {node.name}()")
                elif isinstance(node, ast.ClassDef):
                    symbols.append(f"class {node.name}")
                elif isinstance(node, ast.Import):
                    for n in node.names:
                        symbols.append(f"import {n.name}")
                elif isinstance(node, ast.ImportFrom):
                    symbols.append(f"from {node.module} import ...")
            self.symbol_table[file_path] = symbols
            self.active_files[file_path] = code_content
        except SyntaxError:
            pass
        return symbols

    def add_note(self, note: str):
        """Append working hypothesis note."""
        self.scratch_notes.append(note)

    def get_summary(self) -> str:
        """Render concise L1 working context representation."""
        lines = ["[L1 Working Symbol Cache]"]
        for path, syms in self.symbol_table.items():
            lines.append(f"File: {path} -> {', '.join(syms[:8])}")
        if self.scratch_notes:
            lines.append(f"Notes: {'; '.join(self.scratch_notes[-3:])}")
        return "\n".join(lines)
