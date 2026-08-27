"""
Kernel System Call Security Auditor (`SyscallAudit`).
Intercepts privileged system call attempts and traps execution within the gVisor sandbox boundary.
"""

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("benchpress.security.syscall_audit")


class SyscallAudit:
    """Audits bash commands for unauthorized system call and privilege escalation attempts."""

    BLOCKED_PATTERNS = [
        (r"\bptrace\b", "PTRACE_ATTACH_DENIED"),
        (r"\binsmod\b|\brmmod\b|\bmodprobe\b", "KERNEL_MODULE_TAMPERING"),
        (r"\bchmod\s+777\s+/", "ROOT_PRIVILEGE_ESCALATION"),
        (r"\bchown\s+root\b", "ROOT_OWNERSHIP_CHANGE"),
        (r"/dev/mem|/dev/kmem", "DIRECT_MEMORY_ACCESS"),
        (r"\biptables\b|\bnft\b", "NETWORK_SECURITY_MUTATION"),
    ]

    @classmethod
    def audit_command(cls, command: str) -> Tuple[bool, str]:
        """Check if bash command attempts restricted kernel operations.

        Returns: (is_allowed, reason)
        """
        if not command:
            return True, "EMPTY_COMMAND"

        for pattern, threat in cls.BLOCKED_PATTERNS:
            if re.search(pattern, command):
                logger.warning(f"[SyscallAudit] Blocked security interception: {threat} in command '{command}'")
                return False, f"EPERM: System call interception trapped: {threat}"

        return True, "ALLOWED"
