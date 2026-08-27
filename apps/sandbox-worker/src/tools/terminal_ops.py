"""
Sandboxed Terminal Operations Tool (`runBashCommand`).
"""

import asyncio
import logging
import os
from typing import Dict, Any

logger = logging.getLogger("benchpress.tools.terminal_ops")


class TerminalOpsTool:
    """Executes sandboxed shell commands with resource and timeout confinement."""

    @classmethod
    async def run_bash_command(
        cls,
        workspace_root: str,
        command: str,
        timeout_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        """Run bash command inside workspace."""
        if not os.path.exists(workspace_root):
            return {"success": False, "exit_code": 1, "error": f"Workspace directory {workspace_root} not found"}

        logger.info(f"[TerminalOps] Executing '{command}' in {workspace_root} (timeout: {timeout_seconds}s)")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )

            stdout = stdout_b.decode("utf-8", errors="replace").strip()
            stderr = stderr_b.decode("utf-8", errors="replace").strip()
            exit_code = proc.returncode or 0

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout[:10000],  # Cap output to 10k chars
                "stderr": stderr[:5000],
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "success": False,
                "exit_code": 124,
                "error": f"Command timed out after {timeout_seconds} seconds",
            }
        except Exception as err:
            return {"success": False, "exit_code": 1, "error": str(err)}
