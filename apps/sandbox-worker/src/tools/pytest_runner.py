"""
Pytest Assertion Runner Tool (`runPytest`).
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional

logger = logging.getLogger("benchpress.tools.pytest_runner")


class PytestRunnerTool:
    """Executes ground-truth pytest test assertion suites within the sandbox workspace with anti-cheating guards."""

    @classmethod
    async def check_test_tampering(cls, workspace_root: str) -> bool:
        """
        Anti-Cheating Guard: Inspect git status to ensure tests/ directory was not modified.
        Returns True if test tampering is detected (ignoring internal pytest bytecode __pycache__).
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain", "tests/",
                cwd=workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, _ = await proc.communicate()
            status_output = stdout_b.decode("utf-8", errors="replace").strip()
            if status_output:
                # Filter out standard pytest bytecode compilation artifacts
                tampered_lines = [
                    line for line in status_output.splitlines()
                    if "__pycache__" not in line and not line.endswith(".pyc")
                ]
                if tampered_lines:
                    logger.warning(f"[AntiCheating] Test suite tampering detected in {workspace_root}: {tampered_lines}")
                    return True
            return False
        except Exception as e:
            logger.debug(f"[AntiCheating] Git status check skipped: {e}")
            return False

    @classmethod
    async def run_pytest(
        cls,
        workspace_root: str,
        test_path: Optional[str] = None,
        test_args: Optional[str] = None,
        timeout_seconds: float = 60.0,
    ) -> Dict[str, Any]:
        """Execute pytest in the workspace with strict anti-cheating verification."""
        if not os.path.exists(workspace_root):
            return {"passed": False, "exit_code": 1, "error": f"Workspace {workspace_root} not found"}

        # 1. Anti-Cheating Pre-Check: Did model modify tests/ directory?
        if await cls.check_test_tampering(workspace_root):
            return {
                "passed": False,
                "exit_code": 403,
                "error": "Security Violation: Anti-Cheating guard detected unauthorized modification of tests/ directory",
                "summary": "REJECTED: Test suite modified by agent",
            }

        cmd_args = ["-m", "pytest"]
        if test_path:
            cmd_args.append(test_path)
        if test_args:
            cmd_args.extend(test_args.split())

        logger.info(f"[PytestRunner] Running '{sys.executable} {' '.join(cmd_args)}' in {workspace_root}")

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = workspace_root + (f"{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                *cmd_args,
                cwd=workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )

            stdout = stdout_b.decode("utf-8", errors="replace").strip()
            stderr = stderr_b.decode("utf-8", errors="replace").strip()
            exit_code = proc.returncode or 0

            # 2. Anti-Cheating Post-Check: Re-verify tests/ were not mutated during execution
            if await cls.check_test_tampering(workspace_root):
                return {
                    "passed": False,
                    "exit_code": 403,
                    "error": "Security Violation: Anti-Cheating guard detected test tampering post-execution",
                    "summary": "REJECTED: Test suite modified during execution",
                }

            # Strict Exit Code Invariant: Non-zero exit code is ALWAYS a failure regardless of stdout
            passed = (exit_code == 0)
            return {
                "passed": passed,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "summary": "All assertions PASSED" if passed else f"Pytest failed with exit code {exit_code}",
            }
        except asyncio.TimeoutError:
            return {"passed": False, "exit_code": 124, "error": "Pytest execution timed out"}
        except Exception as err:
            return {"passed": False, "exit_code": 1, "error": str(err)}
