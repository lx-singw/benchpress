"""
Private Enterprise Git Ingestion & AST Mapper (`RepoIngestor`).
Clones or maps private repository worktrees, parses AST symbols, and extracts test suites.
"""

import os
import ast
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("benchpress.evals.repo_ingestor")


@dataclass
class IngestedRepoSymbolMap:
    repo_name: str
    total_files: int
    functions_count: int
    classes_count: int
    symbol_index: Dict[str, List[str]] = field(default_factory=dict)
    test_files: List[str] = field(default_factory=list)


class RepoIngestor:
    """Ingests enterprise repositories, indexing classes, functions, and pytest files."""

    @classmethod
    def index_repository_directory(cls, repo_dir: str) -> IngestedRepoSymbolMap:
        """Scan a repository path and build an in-memory AST symbol table."""
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return IngestedRepoSymbolMap(
                repo_name=repo_path.name,
                total_files=0,
                functions_count=0,
                classes_count=0,
            )

        total_files = 0
        functions_count = 0
        classes_count = 0
        symbol_index: Dict[str, List[str]] = {}
        test_files: List[str] = []

        for py_file in repo_path.rglob("*.py"):
            total_files += 1
            rel_path = str(py_file.relative_to(repo_path))

            if "test" in rel_path.lower():
                test_files.append(rel_path)

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)

                funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

                functions_count += len(funcs)
                classes_count += len(classes)
                symbol_index[rel_path] = funcs + classes

            except Exception as e:
                logger.debug(f"[RepoIngestor] Failed to parse AST for {rel_path}: {e}")

        return IngestedRepoSymbolMap(
            repo_name=repo_path.name,
            total_files=total_files,
            functions_count=functions_count,
            classes_count=classes_count,
            symbol_index=symbol_index,
            test_files=test_files,
        )
