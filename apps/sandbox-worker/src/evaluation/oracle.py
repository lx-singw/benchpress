"""
Deterministic Pytest Oracle Runner.
Executes test suites within isolated sandboxes to objectively verify task resolution.
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
from .result_parser import parse_pytest_output

logger = logging.getLogger("benchpress.evaluation.oracle")


class DeterministicPytestOracle:
    """Runs test assertions inside temporary workspace and measures exit codes."""

    def run_evaluation(
        self,
        sandbox_dir: Path,
        timeout_seconds: int = 30,
    ) -> Dict[str, Any]:
        """Execute pytest runner in sandbox directory."""
        try:
            cmd = [sys.executable, "-m", "pytest", "-v"]
            result = subprocess.run(
                cmd,
                cwd=str(sandbox_dir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            parsed = parse_pytest_output(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
            return parsed

        except subprocess.TimeoutExpired as e:
            logger.warning(f"Pytest evaluation timed out after {timeout_seconds}s")
            return {
                "exit_code": 124,
                "assertions_passed": 0,
                "assertions_failed": 1,
                "resolved": False,
                "stdout": e.stdout or "",
                "stderr": f"Evaluation timed out after {timeout_seconds}s",
                "timed_out": True,
            }
        except Exception as e:
            logger.error(f"Error running pytest oracle: {e}")
            return {
                "exit_code": 1,
                "assertions_passed": 0,
                "assertions_failed": 1,
                "resolved": False,
                "stdout": "",
                "stderr": str(e),
                "infra_error": str(e),
            }
