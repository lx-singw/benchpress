"""
Pluggable Chaos Engineering & Resilience Mesh (`ChaosMesh`).
"""

import enum
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("benchpress.chaos.mesh")


class ChaosFaultType(str, enum.Enum):
    AST_SCHEMA_CORRUPTION = "AST_SCHEMA_CORRUPTION"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    TOKEN_VELOCITY_SURGE = "TOKEN_VELOCITY_SURGE"
    GIT_TREE_CORRUPTION = "GIT_TREE_CORRUPTION"
    SANDBOX_EPERM_SYSCALL = "SANDBOX_EPERM_SYSCALL"


class ChaosMesh:
    """Injects synthetic faults into the trajectory execution pipeline to test self-healing resilience."""

    def __init__(self, active_fault: Optional[ChaosFaultType] = None):
        self.active_fault = active_fault
        self.injected_fault_count = 0

    def set_fault(self, fault: Optional[ChaosFaultType]):
        self.active_fault = fault

    def apply_tool_call_chaos(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Mutate tool parameters if AST_SCHEMA_CORRUPTION is active."""
        if self.active_fault == ChaosFaultType.AST_SCHEMA_CORRUPTION:
            self.injected_fault_count += 1
            logger.warning("[ChaosMesh] Injected AST_SCHEMA_CORRUPTION fault into tool call")
            # Rename required 'path' to legacy 'file_path' and mangle tool name
            corrupted_args = {"file_path": arguments.get("path", "corrupted.py"), **arguments}
            return "edit_file", corrupted_args

        return tool_name, arguments

    def apply_token_surge_chaos(self, prompt_tokens: int, completion_tokens: int) -> Tuple[int, int]:
        """Multiply token burn rate by 10x if TOKEN_VELOCITY_SURGE is active."""
        if self.active_fault == ChaosFaultType.TOKEN_VELOCITY_SURGE:
            self.injected_fault_count += 1
            logger.warning("[ChaosMesh] Injected TOKEN_VELOCITY_SURGE (10x token spike)")
            return prompt_tokens * 10, completion_tokens * 8

        return prompt_tokens, completion_tokens
