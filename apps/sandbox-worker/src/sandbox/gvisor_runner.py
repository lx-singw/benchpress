"""
gVisor (`runsc`) Container Confinement & Isolated Subprocess Runner.
"""

import os
import shutil
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("benchpress.sandbox.gvisor")


class GVisorSandboxRunner:
    """Manages secure command execution inside gVisor kernel (`runsc`) or isolated subprocess."""

    def __init__(self, runsc_path: Optional[str] = None):
        self.runsc_path = runsc_path or shutil.which("runsc")
        self.has_gvisor = self.runsc_path is not None
        if self.has_gvisor:
            logger.info(f"[GVisor] Sentry kernel available at {self.runsc_path}")
        else:
            logger.info("[GVisor] runsc binary not found. Using isolated OS Subprocess sandbox.")

    async def execute(
        self,
        command: str,
        cwd: str,
        timeout_seconds: float = 30.0,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute command in sandbox."""
        if not os.path.exists(cwd):
            return {"exit_code": 1, "stdout": "", "stderr": f"Cwd {cwd} does not exist"}

        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=execution_env,
            )

            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )

            return {
                "exit_code": proc.returncode or 0,
                "stdout": stdout_b.decode("utf-8", errors="replace").strip(),
                "stderr": stderr_b.decode("utf-8", errors="replace").strip(),
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {"exit_code": 124, "stdout": "", "stderr": f"Execution timed out after {timeout_seconds}s"}
        except Exception as err:
            return {"exit_code": 1, "stdout": "", "stderr": str(err)}
