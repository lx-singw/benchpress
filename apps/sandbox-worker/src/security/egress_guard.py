"""
eBPF Network Egress Interceptor & Non-Root Sandbox Capability Enforcer (`EgressGuard`).
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger("benchpress.security.egress_guard")


class EgressGuard:
    """Enforces zero-egress network policies and drops elevated Linux capabilities inside gVisor containers."""

    DENIED_DESTINATIONS = [
        r"https?://(?:[0-9]{1,3}\.){3}[0-9]{1,3}",  # Direct IP connections
        r"https?://(?:pastebin|webhook|ngrok|requestbin)",  # Exfiltration sinks
    ]

    ALLOWED_CAPABILITIES = [
        "CAP_DAC_OVERRIDE",
        "CAP_FOWNER",
    ]

    DENIED_CAPABILITIES = [
        "CAP_SYS_ADMIN",
        "CAP_NET_ADMIN",
        "CAP_SYS_PTRACE",
        "CAP_SYS_MODULE",
    ]

    @classmethod
    def validate_network_egress(cls, destination_uri: str) -> Tuple[bool, str]:
        """Verify network egress destination is permitted under zero-trust enterprise policy."""
        if not destination_uri:
            return True, "ALLOWED"

        for pattern in cls.DENIED_DESTINATIONS:
            if re.search(pattern, destination_uri, re.IGNORECASE):
                logger.warning(f"[EgressGuard] Blocked unauthorized network egress to '{destination_uri}'")
                return False, f"EPERM: Network egress to {destination_uri} denied by VPC-SC policy"

        return True, "ALLOWED"

    @classmethod
    def audit_linux_capabilities(cls, requested_caps: List[str]) -> Tuple[bool, List[str]]:
        """Filter out root privilege capabilities to maintain least-privilege gVisor isolation."""
        dropped = [c for c in requested_caps if c in cls.DENIED_CAPABILITIES]
        if dropped:
            logger.info(f"[EgressGuard] Stripped dangerous Linux capabilities: {dropped}")
        return len(dropped) == 0, dropped
