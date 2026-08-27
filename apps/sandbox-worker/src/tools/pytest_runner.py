"""
Pytest Assertion Runner Tool (`runPytest`).
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("benchpress.tools.pytest_runner")


class PytestRunnerTool:
    """Executes ground-truth pytest test assertion suites within the sandbox workspace."""

    @classmethod
    async def run_pytest(
        cls,
        workspace_root: str,
        test_path: Optional[str] = None,
        test_args: Optional[str] = None,
        timeout_seconds: float = 60.0,
    ) -> Dict[str, Any]:
        """Execute pytest in the workspace."""
        if not os.path.exists(workspace_root):
            return {"passed": False, "exit_code": 1, "error": f"Workspace {workspace_root} not found"}

        cmd_parts = ["pytest"]
        if test_path:
            cmd_parts.append(test_path)
        if test_args:
            cmd_parts.extend(test_args.split())

        command = " ".join(cmd_parts)
        logger.info(f"[PytestRunner] Running '{command}' in {workspace_root}")

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = workspace_root + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")

            proc = await asyncio.create_subprocess_shell(
                command,
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

            passed = exit_code == 0
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
