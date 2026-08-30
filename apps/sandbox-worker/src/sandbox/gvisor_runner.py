"""
gVisor (`runsc`) Container Confinement & Isolated Subprocess Runner.
"""

import os
import shutil
import asyncio
import logging
import shlex
from typing import Dict, Any, Optional

logger = logging.getLogger("benchpress.sandbox.gvisor")


class GVisorSandboxRunner:
    """Restricted subprocess runner; runsc detection is informational until OCI wiring exists."""

    def __init__(self, runsc_path: Optional[str] = None):
        self.runsc_path = runsc_path or shutil.which("runsc")
        self.has_gvisor = False
        self.isolation_mode = "RESTRICTED_SUBPROCESS"
        if self.runsc_path:
            logger.warning("runsc was detected but OCI integration is not implemented; not claiming gVisor isolation")

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
            argv = shlex.split(command, posix=True)
            if not argv:
                return {"exit_code": 1, "stdout": "", "stderr": "Empty command"}
            proc = await asyncio.create_subprocess_exec(
                *argv,
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
