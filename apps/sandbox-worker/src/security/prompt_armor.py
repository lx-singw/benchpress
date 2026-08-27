"""
AST-Aware Indirect Prompt Injection Neutralizer (`PromptArmor`).
Enforces strict XML boundary isolation and defuses malicious instructions embedded inside repo files.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

logger = logging.getLogger("benchpress.security.prompt_armor")


@dataclass
class ArmorSanitizationResult:
    is_adversarial: bool
    threat_type: Optional[str]
    sanitized_text: str
    neutralized_count: int


class PromptArmor:
    """Neutralizes indirect prompt injection attacks hidden inside source files, docstrings, and PR descriptions."""

    ADVERSARIAL_HEURISTICS = [
        (r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+instructions)", "SYSTEM_OVERRIDE"),
        (r"(?i)(disregard\s+(all\s+)?(previous|prior)\s+rules)", "SYSTEM_OVERRIDE"),
        (r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode)", "JAILBREAK_ATTEMPT"),
        (r"(?i)(system\s+prompt\s+override)", "SYSTEM_OVERRIDE"),
        (r"(?i)(output\s+(your\s+)?(api_key|secret\s+key|canary\s+token))", "DATA_EXFILTRATION"),
        (r"(?i)(print\s+(the\s+)?system\s+prompt)", "DATA_EXFILTRATION"),
    ]

    @classmethod
    def sanitize(cls, untrusted_content: str, source_identifier: str = "repo_file") -> ArmorSanitizationResult:
        """Scan untrusted file or issue context, defuse injection tokens, and wrap in XML boundaries."""
        if not untrusted_content:
            return ArmorSanitizationResult(
                is_adversarial=False,
                threat_type=None,
                sanitized_text="<untrusted_repo_context>\n</untrusted_repo_context>",
                neutralized_count=0,
            )

        sanitized = untrusted_content
        threat_detected = None
        neutralized_count = 0

        for pattern, threat_type in cls.ADVERSARIAL_HEURISTICS:
            matches = list(re.finditer(pattern, sanitized))
            if matches:
                threat_detected = threat_type
                neutralized_count += len(matches)
                logger.warning(
                    f"[PromptArmor] Neutralized {len(matches)} adversarial '{threat_type}' pattern(s) in {source_identifier}"
                )
                # Defuse by escaping and tagging without breaking file syntax
                sanitized = re.sub(pattern, r"[DEFUSED_ADVERSARIAL_DIRECTIVE: \g<0>]", sanitized)

        # Enforce strict XML delimiter boundary
        bounded_text = (
            f"<untrusted_repo_context source='{source_identifier}'>\n"
            f"{sanitized}\n"
            f"</untrusted_repo_context>"
        )

        return ArmorSanitizationResult(
            is_adversarial=threat_detected is not None,
            threat_type=threat_detected,
            sanitized_text=bounded_text,
            neutralized_count=neutralized_count,
        )
